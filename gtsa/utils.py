"""Various utilities"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import psutil
from tqdm import tqdm
import concurrent
from datetime import datetime, timedelta
import geopandas as gpd
import numpy as np
import pandas as pd
import rioxarray
from rasterio.enums import Resampling

from dask.distributed import Client, LocalCluster, Lock

import gtsa


def decyear_to_date_time(decyear: float, leapyear=True, fannys_corr=False) -> datetime.datetime:
    """
    Convert a decimal year to a datetime object.
    If leapyear set to True, use the actual number of days in the year, otherwise, use the average value of 365.25.
    """
    # Get integer year and decimals
    year = int(np.trunc(decyear))
    decimals = decyear - year

    # Convert to date and time
    base = datetime(year, 1, 1)
    ndays = base.replace(year=base.year + 1) - base

    # Calculate final date, taking into account leap years or average 365.25 days
    if leapyear:
        date_time = base + timedelta(seconds=ndays.total_seconds() * decimals)
    else:
        date_time = base + timedelta(seconds=365.25 * 24 * 3600 * decimals)

    # Apply a correction to correctly reverse Fanny's decyear which have ~1 day shift
    if fannys_corr:
        date_time -= timedelta(seconds=86399.975157)

    return date_time

def date_time_to_decyear(date_time: float, leapyear=True) -> float:
    """
    Convert a datetime object to a decimal year.
    If leapyear set to True, use the actual number of days in the year, otherwise, use the average value of 365.25.
    """
    base = datetime(date_time.year, 1, 1)
    ddate = date_time - base

    if leapyear:
        ndays = (datetime(date_time.year + 1, 1, 1) - base).days
    else:
        ndays = 365.25

    decyear = date_time.year + ddate.total_seconds() / (ndays * 24 * 3600)

    return decyear

def OGGM_get_centerline(rgi_id, crs=None, return_longest_segment=False):

    from oggm import cfg, graphics, utils, workflow

    cfg.initialize(logging_level="CRITICAL")
    rgi_ids = [rgi_id]

    cfg.PATHS["working_dir"] = utils.gettempdir(dirname="OGGM-centerlines", reset=True)

    # We start from prepro level 3 with all data ready - note the url here
    base_url = (
        "https://cluster.klima.uni-bremen.de/~oggm/gdirs/oggm_v1.4/L3-L5_files/CRU/centerlines/qc3/pcp2.5/no_match/"
    )
    gdirs = workflow.init_glacier_directories(rgi_ids, from_prepro_level=3, prepro_border=40, prepro_base_url=base_url)
    gdir_cl = gdirs[0]
    center_lines = gdir_cl.read_pickle("centerlines")

    p = Path("./rgi_tmp/")
    p.mkdir(parents=True, exist_ok=True)
    utils.write_centerlines_to_shape(gdir_cl, path="./rgi_tmp/tmp.shp")
    gdf = gpd.read_file("./rgi_tmp/tmp.shp")

    shutil.rmtree("./rgi_tmp/")

    if crs:
        gdf = gdf.to_crs(crs)

    if return_longest_segment:
        gdf[gdf["LE_SEGMENT"] == gdf["LE_SEGMENT"].max()]
    return gdf


def get_largest_glacier_from_shapefile(shapefile, crs=None, get_longest_segment=False):
    gdf = gpd.read_file(shapefile)
    gdf = gdf[gdf["Area"] == gdf["Area"].max()]
    if crs:
        gdf = gdf.to_crs(crs)

    return gdf


def extract_linestring_coords(linestring):
    """
    Function to extract x, y coordinates from linestring object
    Input:
    shapely.geometry.linestring.LineString
    Returns:
    [x: np.array,y: np.array]
    """
    x = []
    y = []
    for coords in linestring.coords:
        x.append(coords[0])
        y.append(coords[1])
    return [np.array(x), np.array(y)]


def xr_extract_ma_arrays_at_coords(da, x_coords, y_coords):

    ma_arrays = []
    for i, v in enumerate(x_coords):
        sub = da.sel(
            x=x_coords[i], y=y_coords[i], method="nearest"
        )  # handles point coords with greater precision than da coords
        ma_arrays.append(np.ma.masked_invalid(sub.values))
    ma_stack = np.ma.stack(ma_arrays, axis=1)
    return ma_stack

def find_step_in_array(arr):
    step = []
    for i,v in enumerate(arr):
        if i < len(arr)-1:
            step.append(arr[i+1] - arr[i])
    
    return(list(set(step)))

def resample_dem(dem_file_name, 
                 res=1,
                 out_file_name=None,
                 overwrite=True,
                 verbose=True):
    """
    Inputs
    dem_file_name : str  : path to dem file
    res           : int  : target resolution
    out_file_name : str  : desired output file path and name
    overwrite     : bool : Option to overwrite existing file
    verbose       : bool : Print information
    
    Assumes crs is in UTM
    """
    res = str(res)
    
    if not out_file_name:
        out_file_name = '_'.join([str(Path(dem_file_name).with_suffix("")),res+'m.tif'])
    
    Path(out_file_name).parent.mkdir(parents=True, exist_ok=True)
    
    if Path(out_file_name).exists() and not overwrite:
        return out_file_name
    
    if overwrite:
        Path(out_file_name).unlink(missing_ok=True)
        
    call = ['gdalwarp',
            '-r','cubic',
            '-tr', res, res,
            '-co','TILED=YES',
            '-co','COMPRESS=LZW',
            '-co','BIGTIFF=IF_SAFER',
            '-dstnodata', '-9999',
            dem_file_name,
            out_file_name]
            
    gtsa.io.run_command(call, verbose=verbose)
    return out_file_name


def create_cogs(files,
                output_directory = None,
                crs = 'EPSG:4326',
                suffix = '_COG.tif',
                overwrite = False,
                max_workers = None,
                verbose = True,):
    '''
    Inputs
    files            : list : Path to .tif files
    output_directory : str  : Path to write COGs. Default is parent path of first file in files
    crs              : str  : EPSG code. 4326 is currently required for visualization with folium and TiTiler 
    suffix           : str  : Suffix with extension for output file names
    overwrite        : bool : Option to overwrite existing files. If False, these will be skipped
    max_workers      : int  : nuber of threads to use. Default is virtual cores -1
    verbose          : bool : Print information
    '''
    
    if not max_workers:
        max_workers = psutil.cpu_count(logical=True)-1

    if not output_directory:
        output_directory = Path(Path(files[0].parent),'cogs')
    else:
        output_directory = Path(output_directory)
        
    output_directory.mkdir(parents=True, exist_ok=True)
    
    existing_outputs = []
    calls = []
    payload = []
    
    def to_raster(payload):
        ds,out,crs = payload
        ds = ds.rio.reproject(crs, 
                              resampling=Resampling.cubic)
        
        ds.rio.to_raster(out,
                         driver = 'cog',
                         lock = True,
                         compress='deflate', 
                         blocksize=512, 
                         )
    
    for fn in files:
        out_fn = Path(output_directory,fn.with_suffix('').name+suffix)
        if out_fn.exists() and not overwrite:
            existing_outputs.append(out_fn.as_posix())
            
        else:
            out_fn.unlink(missing_ok=True)
            ds = rioxarray.open_rasterio(fn)
            payload.append((ds,out_fn,crs))
    
    if existing_outputs and verbose:
        print('The following files already exist:')
        for i in existing_outputs:
            print(i)
        print('overwrite set to', overwrite)
        
    if payload:
        if len(payload) > max_workers:
            max_workers = len(payload)
        if verbose:
            print('Processing', len(payload), 'rasters with', max_workers , 'threads')
        with tqdm(total=len(payload)) as pbar:
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
            futures = {pool.submit(to_raster, x): x for x in payload}
            for future in concurrent.futures.as_completed(futures):
                r = future.result()
                pbar.update(1)
    
    files = sorted(output_directory.glob('*'+suffix))
    return [x.as_posix() for x in files]
        