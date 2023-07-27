import geopandas as gpd
import numpy as np
import scipy
import math
import rasterio
from shapely.geometry import Point, Polygon
import concurrent
import rioxarray


def df_xy_coords_to_gdf(
    df,
    lon="lon",
    lat="lat",
    crs="epsg:4326",
):
    """
    Function to convert pandas dataframe containing lat, lon coordinates to geopandas dataframe.
    """
    geometry = [Point(xy) for xy in zip(df[lon], df[lat])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)

    return gdf


def bounds2polygon(xmin, ymin, xmax, ymax, crs):
    """
    Function to return square polygon as GeoDataFrame
    """

    vertices = [(xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]
    polygon = Polygon(vertices)
    polygon_gdf = gpd.GeoDataFrame(
        gpd.GeoSeries(polygon), columns=["geometry"], crs=crs
    )
    return polygon_gdf


def extract_gpd_geometry(point_gdf):
    """
    Function to extract x, y, z coordinates and add as columns to input geopandas data frame.
    """
    x = []
    y = []
    z = []
    for i in range(len(point_gdf)):
        x.append(point_gdf["geometry"].iloc[i].coords[:][0][0])
        y.append(point_gdf["geometry"].iloc[i].coords[:][0][1])
        if len(point_gdf["geometry"].iloc[i].coords[:][0]) == 3:
            z.append(point_gdf["geometry"].iloc[i].coords[:][0][2])

    point_gdf["x"] = x
    point_gdf["y"] = y
    if len(point_gdf["geometry"].iloc[0].coords[:][0]) == 3:
        point_gdf["z"] = z
    return point_gdf


def dem_stack_bounds2polygon(tifs):
    """
    Function to return polygon for max bounds in stack of DEMs.

    Input:
    tifs : list : DEM file paths

    Returns:
    polygon as GeoDataFrame
    """

    if _check_common_epsg(tifs):
        epsg_code = _get_epsg_code(tifs[0])
        xmin, xmax, ymin, ymax = _get_max_bounds(tifs)
        polygon_gdf = bounds2polygon(xmin, xmax, ymin, ymax, epsg_code=epsg_code)
        return polygon_gdf


def extract_dataset_center_window(ds, xdim="x", ydim="y", size=256, verbose=True):
    xmode = np.abs(scipy.stats.mode(ds["y"].diff("y"))[0])
    ymode = np.abs(scipy.stats.mode(ds["y"].diff("y"))[0])
    size = size * np.mean(np.array([xmode, ymode]))
    cx, cy = _get_dataset_centroid(ds)
    if verbose:
        print(f"Dataset center: {cx}, {cy}")
        print(f"Test column size: {size} by {size} in spatial coordinate units.")
    offset = size / 2
    xmin = cx - offset
    xmax = cx + offset
    ymin = cy - offset
    ymax = cy + offset
    try:
        ds = ds.rio.clip_box(minx=xmin, miny=ymin, maxx=xmax, maxy=ymax)

    except Exception as e:
        if isinstance(type(e), type(rioxarray.exceptions.MissingCRS)):
            if verbose:
                print(
                    "No CRS defined.\nUsing xarray slicing to select data along spatial coordinate axes."
                )
            ds = ds.sel({xdim: slice(xmin, xmax), ydim: slice(ymax, ymin)})

    return ds


def _get_dataset_centroid(ds):
    xmin, ymin, xmax, ymax = ds.rio.bounds()
    cx = (xmax - xmin) / 2 + xmin
    cy = (ymax - ymin) / 2 + ymin
    return cx, cy


def _get_raster_centroid(filename):
    src = rasterio.open(filename)
    xmin, ymin, xmax, ymax = src.bounds
    cx = (xmax - xmin) / 2 + xmin
    cy = (ymax - ymin) / 2 + ymin
    return cx, cy


def _get_rasters_centroid(tifs):
    xmin, xmax, ymin, ymax = _get_max_bounds(tifs)
    cx = (xmax - xmin) / 2 + xmin
    cy = (ymax - ymin) / 2 + ymin
    return cx, cy


def _get_bounds(tif):
    src = rasterio.open(tif)
    xmin, ymin, xmax, ymax = src.bounds
    return xmin, xmax, ymin, ymax


def _get_max_bounds(tifs):
    """
    Function to return max bounds for stack ov overlapping geotiffs.

    Input:
    tifs : list : file paths

    Returns:
    xmin, xmax, ymin, ymax : coordinates
    """

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    # check all tifs are in same CRS
    epsg_codes = []
    futures = {pool.submit(_get_epsg_code, x): x for x in tifs}
    epsg_codes = [f.result() for f in concurrent.futures.as_completed(futures)]
    if len(list(set(epsg_codes))) != 1:
        print("Not all input files have the same CRS")
        for i in list(zip(epsg_codes, tifs)):
            print(i)

    # find max bounds
    else:
        xmin_vals = []
        ymin_vals = []
        xmax_vals = []
        ymax_vals = []

        ## submitting in parallel isn't faster for some reason...
        #         futures = {pool.submit(_get_bounds, x): x for x in tifs}
        #         results = [f.result() for f in concurrent.futures.as_completed(futures)]
        #         for r in results:
        #             xmin, xmax, ymin, ymax = r
        #             xmin_vals.append(xmin)
        #             ymin_vals.append(ymin)
        #             xmax_vals.append(xmax)
        #             ymax_vals.append(ymax)

        for fn in tifs:
            src = rasterio.open(fn, masked=True)
            xmin, ymin, xmax, ymax = src.bounds
            xmin_vals.append(xmin)
            ymin_vals.append(ymin)
            xmax_vals.append(xmax)
            ymax_vals.append(ymax)

        xmin = np.min(xmin_vals)
        ymin = np.min(ymin_vals)
        xmax = np.max(xmax_vals)
        ymax = np.max(ymax_vals)

        return xmin, xmax, ymin, ymax


def _get_epsg_code(tif):
    """
    Return EPSG code for tif

    Input
    tif : file path

    Returns
    str : EPSG code
    """

    src = rasterio.open(tif)
    epsg_code = str(src.crs.to_epsg())

    return epsg_code


def _check_common_epsg(tifs):
    """
    Checks all input tif files have the same epsg code
    """
    epsg_codes = []
    for i in tifs:
        epsg_codes.append(_get_epsg_code(i))
    epsg_codes_set = list(set(epsg_codes))
    if len(epsg_codes_set):
        return True
    else:
        print("List of input tif files contains multiple epsg codes.")
        for i in list(zip([j.name for j in tifs], epsg_codes)):
            print("epsg:" + i[1], i[0])
        return False


def _lon_lat_to_utm_epsg_code(lon, lat):
    """
    Function to retrieve local UTM EPSG code from WGS84 geographic coordinates.
    """
    utm_band = str((math.floor((lon + 180) / 6) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = "0" + utm_band
    if lat >= 0:
        epsg_code = "326" + utm_band
    else:
        epsg_code = "327" + utm_band
    return epsg_code
