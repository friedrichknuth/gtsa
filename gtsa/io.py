from pathlib import Path
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
import fsspec
import re
import shutil

# import geoutils as gu
import numpy as np
import rioxarray
import xarray as xr
from rasterio.enums import Resampling
import zarr

from dask.distributed import Client, LocalCluster
import logging

import warnings
warnings.filterwarnings("ignore")

def parse_urls_from_S3_bucket(s3_bucket_name,
                              aws_server_url = 's3.amazonaws.com', 
                              folder = '',
                              extension = 'tif',
                             ):
    
    fs = fsspec.filesystem('s3')
    bucket = 's3://'+Path(s3_bucket_name, folder).as_posix()
    base_url = Path(s3_bucket_name+'.'+aws_server_url,folder).as_posix()
    file_names  = [x.split('/')[-1] for x in fs.ls(bucket) if extension in x]
    urls   = ['http://'+ Path(base_url,x).as_posix() for x in file_names]

    return urls

def _get_test_sites(s3_bucket_name):
    fs = fsspec.filesystem('s3')
    bucket ='s3://'+s3_bucket_name
    sites = [x.split('/')[-1] for x in fs.ls(bucket)]
    return sites
    

def run_command(command, verbose=True):
    '''
    Run something from the command line.
    
    Example 1
    call = ['command', 'input', output']
    run_command(call)
    
    Example 2
    call = 'command "input" output'
    run_command(call)
    
    Use a space seperated string if your command contains nested strings.
    '''
    
    if isinstance(command, type(str())):
        print(command)
        shell = True
    else:
        print(*command)
        shell = False
    
    p = Popen(command,
              stdout=PIPE,
              stderr=STDOUT,
              shell=shell)
    
    while p.poll() is None:
        if verbose == True:
            try:
                line = (p.stdout.readline()).decode('ASCII').rstrip('\n')
            except:
                line = p.stdout.read()
                pass
            print(line)

            
def parse_timestamps(file_list,
                     date_string_pattern = '....-..-..',
                    ):
    tmp = re.compile(date_string_pattern)
    results = []
    for x in file_list:
        try:
            results.append(tmp.search(x).group(0))
        except:
            print('pattern not find in',x)
    return results

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

# def stack_geotif_arrays(geotif_files_list):
#     """
#     Simple function to stack raster arrays. Assumes these are already aligned.
#     Inputs
#     ----------
#     geotif_files_list : list of GeoTIFF files
#     Returns
#     -------
#     ma_stack : numpy.ma.core.MaskedArray
#     """
#     arrays = []
#     for i in geotif_files_list:
#         src = gu.georaster.Raster(i)
#         masked_array = src.data
#         arrays.append(masked_array)
#     ma_stack = np.ma.vstack(arrays)
#     return ma_stack



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

def create_zarr_stack(xarray_dataset,
                      output_directory = './',
                      zarr_stack_file_name= 'stack.zarr',
                      overwrite = False,
                      print_info = True,
                      cleanup = False,
                      ):
    
    # TODO - writing to zarr with ds.rio.crs assigned fails - not sure how to preserve the crs in the saved file
    
    ds = xarray_dataset
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    
    zarr_stack_fn  = Path(output_directory, zarr_stack_file_name)
    zarr_stack_tmp = Path(output_directory, 'stack_tmp.zarr')
    
    if overwrite:
        shutil.rmtree(zarr_stack_fn, ignore_errors=True)
        shutil.rmtree(zarr_stack_tmp, ignore_errors=True)
    elif zarr_stack_fn.exists():
        ds = xr.open_dataset(zarr_stack_fn,chunks='auto',engine='zarr')
        if print_info:
            print('\nZarr file exists')
            print('\nZarr file info')
            source_group = zarr.open(zarr_stack_fn)
            source_array = source_group['band1']
            print(source_group.tree())
            print(source_array.info)
            del source_group
            del source_array
        
        tc,yc,xc  = determine_optimal_chuck_size(ds,
                                                  print_info = print_info)
        ds = xr.open_dataset(zarr_stack_fn,
                             chunks={'time': tc, 'y': yc, 'x':xc},engine='zarr')
        return ds
    
    else:
        # remove attributes that zarr doesn't like
        try:
            ds = ds.drop(['spatial_ref'])
            for i in ds.data_vars:
                try:
                    del ds[i].attrs['grid_mapping']
                except:
                    pass
        except:
            pass

        if print_info:
            print('Creating temporary zarr stack')
        ds.to_zarr(zarr_stack_tmp)

        if print_info:
            source_group = zarr.open(zarr_stack_tmp)
            source_array = source_group['band1']
            print(source_group.tree())
            print(source_array.info)
            del source_group
            del source_array

        if print_info:
            print('Rechunking temporary zarr stack and saving as')
            print(str(zarr_stack_fn))

        arr = ds['band1'].data.rechunk({0:-1, 1:'auto', 2:'auto'}, 
                                                    block_size_limit=1e8, 
                                                    balance=True)
        t,y,x = arr.chunks[0][0], arr.chunks[1][0], arr.chunks[2][0]
        ds = xr.open_dataset(zarr_stack_tmp,
                             chunks={'time': t, 'y': y, 'x':x},engine='zarr')
        ds['band1'].encoding = {'chunks': (t, y, x)}  
        ds.to_zarr(zarr_stack_fn)

        if print_info:
            print('\nRechunked zarr file info')
            source_group = zarr.open(zarr_stack_fn)
            source_array = source_group['band1']
            print(source_group.tree())
            print(source_array.info)
            del source_group
            del source_array
        if cleanup:
            if print_info:
                print('Removing temporary zarr stack')
            shutil.rmtree(zarr_stack_tmp, ignore_errors=True)

        tc,yc,xc  = determine_optimal_chuck_size(ds,
                                                  print_info = print_info)
        ds = xr.open_dataset(zarr_stack_fn,
                             chunks={'time': tc, 'y': yc, 'x':xc},engine='zarr')

        return ds

def determine_optimal_chuck_size(ds,
                                 print_info = True):
    if print_info:
        print('\nDetermining optimal chunk size for processing')
    ## set chunk size to 1 MB if single time series array < 1 MB in size
    ## else increase to max of 1 GB chunk sizes.
    
    time_series_array_size = ds['band1'].sel(x=ds['band1'].x.values[0], 
                                             y=ds['band1'].y.values[0]).nbytes
    if time_series_array_size < 1e6:
        chunk_size_limit = 2e6
    elif time_series_array_size < 1e7:
        chunk_size_limit = 2e7
    elif time_series_array_size < 1e8:
        chunk_size_limit = 2e8
    else:
        chunk_size_limit = 1e9
    ds_size = ds['band1'].nbytes / 1e9
    t = len(ds.time)
    x = len(ds.x)
    y = len(ds.y)
    arr = ds['band1'].data.rechunk({0:-1, 1:'auto', 2:'auto'}, 
                                                block_size_limit=chunk_size_limit, 
                                                balance=True)
    tc,yc,xc = arr.chunks[0][0], arr.chunks[1][0], arr.chunks[2][0]
    chunksize = ds['band1'][:tc,:yc,:xc].nbytes / 1e6
    if print_info:
        print('Chunk shape:','('+','.join([str(x) for x in [tc,yc,xc]])+')')
        print('Chunk size:',ds['band1'][:tc,:yc,:xc].nbytes, '('+str(chunksize)+'G)')
    
    return tc,yc,xc
        
def xr_stack_geotifs(geotif_files_list, 
                     datetimes_list, 
                     reference_geotif_file, 
                     resampling="bilinear",
                     save_to_nc=False,
                     nc_out_dir = None,
                     overwrite = True,
                     cleanup = False,
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
#             if not check_xr_rio_ds_match(src, ref):
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
