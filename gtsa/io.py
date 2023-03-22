from pathlib import Path
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT

import geoutils as gu
import numpy as np
import rioxarray
import xarray as xr
from rasterio.enums import Resampling

from dask.distributed import Client, LocalCluster
import logging


def run_command(command, verbose=False, shell=False):
    if verbose == True:
        print(*command)
    
    p = Popen(command,
              stdout=PIPE,
              stderr=STDOUT,
              shell=shell)
    
    while p.poll() is None:
        try:
            line = (p.stdout.readline()).decode('ASCII').rstrip('\n')
            if verbose == True:
                print(line)
        except:
            pass

            
def parse_timestamps(file_list):
    return [datetime.strptime(str(i)[-14:-4], "%Y-%m-%d") for i in file_list]

def parse_hsfm_timestamps(file_list):
    date_times = []
    for i in file_list:
        parts = i.name.split('_')
        for p in parts:
            if '-' in p:
                date_times.append(p)
                
    return [datetime.strptime(i, "%Y-%m-%d") for i in date_times]

def parse_earthdem_timestamps(file_list):
    date_times = []
    for i in file_list:
        parts = i.name.split('_')
        date_times.append(parts[1])
                
    return [datetime.strptime(i, "%Y%m%d") for i in date_times]
    
def dask_start_cluster(nproc, threads=1, ip_addres=None, port=':8786'):
    """
    Starts a dask cluster. Can provide a custom IP or URL to view the progress dashboard. 
    This may be necessary if working on a remote machine.
    """
    cluster = LocalCluster(n_workers=nproc,
                           threads_per_worker=threads,
                           silence_logs=logging.ERROR,
                           dashboard_address=port)

    client = Client(cluster)
    
    if ip_addres:
        port = str(cluster.dashboard_link.split(':')[-1])
        url = ":".join([ip_addres,port])
        print('\n'+'Dask dashboard at:',url)
    else:
        print('\n'+'Dask dashboard at:',cluster.dashboard_link)
    
    print('Workers:', nproc)
    print('Threads per worker:', threads, '\n')
    return client


def dask_get_mapped_tasks(dask_array):
    """
    Finds tasks associated with chunked dask array.
    """
    # TODO There has to be a better way to do this...
    txt = dask_array._repr_html_()
    idx = txt.find('Tasks')
    strings = txt[idx-20:idx].split(' ')
    tasks_count = max([int(i) for i in strings if i.isdigit()])
    return tasks_count

def stack_geotif_arrays(geotif_files_list):
    """
    Simple function to stack raster arrays. Assumes these are already aligned.
    Inputs
    ----------
    geotif_files_list : list of GeoTIFF files
    Returns
    -------
    ma_stack : numpy.ma.core.MaskedArray
    """
    arrays = []
    for i in geotif_files_list:
        src = gu.georaster.Raster(i)
        masked_array = src.data
        arrays.append(masked_array)
    ma_stack = np.ma.vstack(arrays)
    return ma_stack



def xr_read_geotif(geotif_file_path, chunks='auto', masked=True):
    """
    Reads in single or multi-band GeoTIFF as dask array.
    Inputs
    ----------
    GeoTIFF_file_path : GeoTIFF file path
    Returns
    -------
    ds : xarray.Dataset
        Includes rioxarray extension to xarray.Dataset
    """

    da = rioxarray.open_rasterio(geotif_file_path, chunks=chunks, masked=True)

    # Extract bands and assign as variables in xr.Dataset()
    ds = xr.Dataset()
    for i, v in enumerate(da.band):
        da_tmp = da.sel(band=v)
        da_tmp.name = "band" + str(i + 1)

        ds[da_tmp.name] = da_tmp

    # Delete empty band coordinates.
    # Need to preserve spatial_ref coordinate, even though it appears empty.
    # See spatial_ref attributes under ds.coords.variables used by rioxarray extension.
    del ds.coords["band"]

    # Preserve top-level attributes and extract single value from value iterables e.g. (1,) --> 1
    ds.attrs = da.attrs
    for key, value in ds.attrs.items():
        try:
            if len(value) == 1:
                ds.attrs[key] = value[0]
        except TypeError:
            pass

    return ds


def xr_stack_geotifs(geotif_files_list, 
                     datetimes_list, 
                     reference_geotif_file, 
                     resampling="bilinear",
                     save_to_nc=False,
                     nc_out_dir = None,
                     overwrite = True,
                    ):

    """
    Stack single or multi-band GeoTiFFs to reference_geotiff.
    Returns out-of-memory dask array, unless resampling occurs.
    
    Optionally, set save_to_nc true when resmapling is required to
    return an out-of-memory dask array.
    Inputs
    ----------
    geotif_files_list     : list of GeoTIFF file paths
    datetimes_list        : list of datetime objects for each GeoTIFF
    reference_geotif_file : GeoTIFF file path
    Returns
    -------
    ds : xr.Dataset()
    """

    if save_to_nc and nc_out_dir:
        nc_out_dir = Path(nc_out_dir)
        nc_out_dir.mkdir(parents=True, exist_ok=True)
    ## Check each geotiff has a datetime associated with it.
    if len(datetimes_list) == len(geotif_files_list):
        pass
    else:
        print("length of datetimes does not match length of GeoTIFF list")
        print("datetimes:", len(datetimes_list))
        print("geotifs:", len(geotif_files_list))
        return None
    
    ## Choose resampling method. Defaults to bilinear.
    if isinstance(resampling, type(Resampling.bilinear)):
        resampling = resampling
    elif resampling == "bilinear":
        resampling = Resampling.bilinear
    elif resampling == "nearest":
        resampling = Resampling.nearest
    elif resampling == "cubic":
        resampling = Resampling.cubic
    else:
        resampling = Resampling.bilinear

    ## Get target object with desired crs, res, bounds, transform
    ## TODO: Parameterize crs, res, bounds, transform
    ref = xr_read_geotif(reference_geotif_file)

    ## Stack geotifs and dimension in time
    datasets = []
    nc_files = []
    out_dirs = []

    c = 0
    for index, file_name in enumerate(geotif_files_list):
        if not nc_out_dir:
            out_fn = str(Path(file_name).with_suffix("")) + ".nc"
        else:
            out_fn = str(Path(nc_out_dir,Path(file_name).with_suffix("").name + ".nc"))
        
        if Path(out_fn).exists() and not overwrite:
            nc_files.append(out_fn)
            out_dir = str(Path(out_fn).parents[0])
            out_dirs.append(out_dir)
            src = xr.open_dataset(out_fn)
            datasets.append(src)
            
        else:
            Path(out_fn).unlink(missing_ok=True)
            src = xr_read_geotif(file_name)
            if not check_xr_rio_ds_match(src, ref):
                src = src.rio.reproject_match(ref, resampling=resampling)
                c += 1
            src = src.assign_coords({"time": datetimes_list[index]})
            src = src.expand_dims("time")
            if save_to_nc:
                src.to_netcdf(out_fn)
                nc_files.append(out_fn)
                out_dir = str(Path(out_fn).parents[0])
                out_dirs.append(out_dir)
            datasets.append(src)
    
    # check if anything was resampled
    if c != 0:
        print('Resampled', 
              c, 
              'of', 
              len(geotif_files_list), 
              'dems to match reference DEM spatial_ref, crs, transform, bounds, and resolution.')

    # Optionally ensure data are returned as dask array.
    if save_to_nc:
        print('Saved .nc files in',','.join([str(i) for i in list(set(out_dirs))]))
        ds = xr.open_mfdataset(nc_files)
        ds = ds.sortby('time')
        ds.rio.write_crs(ref.rio.crs, inplace=True)
        return ds
        
    print('here')
    ds = xr.concat(datasets, dim="time", combine_attrs="no_conflicts")
    ds = ds.sortby('time')
    return ds


def check_xr_rio_ds_match(ds1, ds2):
    """
    Checks if spatial attributes, crs, bounds, and transform match.
    Inputs
    ----------
    ds1 : xarray.Dataset with rioxarray extension
    ds2 : xarray.Dataset with rioxarray extension
    Returns
    -------
    bool
    """

    if (
        (ds1["spatial_ref"].attrs == ds2["spatial_ref"].attrs)
        & (ds1.rio.crs == ds2.rio.crs)
        & (ds1.rio.transform() == ds2.rio.transform())
        & (ds1.rio.bounds() == ds2.rio.bounds())
        & (ds1.rio.resolution() == ds2.rio.resolution())
    ):
        return True
    else:
        return False
