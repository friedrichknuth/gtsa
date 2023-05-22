import gtsa
import rasterio
import xarray as xr
import dask
import geopandas as gpd
import pandas as pd
import numpy as np
import psutil
from pathlib import Path
from time import time


bucket = 'petrichor'
aws_server_url = 's3.us-west-2.amazonaws.com'
product = 'stack'
base_directory = './stacks'
crs = rasterio.crs.CRS.from_epsg(4326)
print_info = True
workers = psutil.cpu_count(logical=True)-1
rgi02_file = '/mnt/storage/knuth/sites/strato_glaciers/data/rgi/02_rgi60_WesternCanadaUS.geojson'

# sites = gtsa.io._get_test_sites(bucket)

sites = ['rainier',]
# glaciers = ['Carbon Glacier WA', 'Winthrop Glacier WA', 'Emmons Glacier WA', 
#  'Cowlitz Glacier WA', 'Paradise Glacier WA', 'Nisqually Glacier WA',
#  'Kautz Glacier WA', 'Tahoma Glacier WA', 'Puyallup Glacier WA', 
#  'North Mowich Glacier WA', 
# ]

kernel = gtsa.temporal.GPR_glacier_kernel()


if __name__ == "__main__":

    with dask.config.set({'temporary_directory': '/mnt/storage/knuth/dask-scratch-space/'}):
        pass
    
    t1 = time()
    
    client = gtsa.io.dask_start_cluster(workers)
    rgi02_gdf = gpd.read_file(rgi02_file)
    
    for s in sites:
        folder = gtsa.io.Path(s, product).as_posix()

        zarr_url = gtsa.io.parse_urls_from_S3_bucket(bucket,
                                                     aws_server_url = aws_server_url,
                                                     folder = folder,
                                                     extension= 'stack.zarr')[0]


        ds_zarr = xr.open_dataset(zarr_url,chunks='auto',engine='zarr')
        tc,yc,xc  = gtsa.io.determine_optimal_chuck_size(ds_zarr,
                                                          print_info = print_info)
        ds_zarr = xr.open_dataset(zarr_url,
                             chunks={'time': tc, 'y': yc, 'x':xc},engine='zarr')
        ds_zarr = ds_zarr.rio.write_crs(crs)
        
        xmin, xmax = -121.79, -121.78
        ymin, ymax = 46.89, 46.90

        subset = ds_zarr.sel(x=slice(xmin, xmax), y=slice(ymax,ymin))
        
#         subset = ds_zarr
        
        time_stamps = [gtsa.utils.date_time_to_decyear(i) for i in [pd.to_datetime(j) for j in subset['band1'].time.values]]
        time_stamps = np.array(time_stamps)
        prediction_time_series = gtsa.temporal.create_prediction_timeseries(start_date = '1950-01-01',
                                                                            end_date = '2020-01-01',
                                                                            dt ='M')
        ds_result = gtsa.temporal.dask_apply_GPR(subset['band1'],
                                               'time', 
                                               kwargs={'times':time_stamps,
                                                       'kernel': kernel,
                                                       'prediction_time_series' : prediction_time_series})
        
        ds_result.to_zarr('test.zarr')
        
        
        
        
    t2 = time()
    print(f"Took {(t2-t1)/60:.2f} min to process with {workers} workers")
    print('DONE')