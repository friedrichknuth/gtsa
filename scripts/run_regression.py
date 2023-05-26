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
output_directory = './products/timeseries/'
print_info = True
rgi02_file = '/mnt/storage/knuth/sites/strato_glaciers/data/rgi/02_rgi60_WesternCanadaUS.geojson'

# sites = gtsa.io._get_test_sites(bucket)
sites = ['rainier',]


rgi02_gdf = gpd.read_file(rgi02_file)
kernel = gtsa.temporal.GPR_glacier_kernel()
workers = psutil.cpu_count(logical=True)-1
crs = rasterio.crs.CRS.from_epsg(4326)

if __name__ == "__main__":

    with dask.config.set({'temporary_directory': '/mnt/storage/knuth/dask-scratch-space/'}):
    
        t1 = time()
        Path(output_directory).mkdir(parents=True, exist_ok=True)

        client = gtsa.io.dask_start_cluster(workers,
                                            ip_addres='http://sunhado.ce.washington.edu',
                                            port=':8786')
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
            
            xmin, ymin, xmax, ymax = ds_zarr['band1'].rio.bounds()
            bounds_gdf = gtsa.geospatial.bounds2polygon(xmin, xmax, ymin, ymax)
            glaciers_gdf = gpd.sjoin(rgi02_gdf, bounds_gdf, predicate='intersects') # intersecting glaciers
            glaciers_gdf = glaciers_gdf[glaciers_gdf['Name'].str.len() > 2] # named
            glaciers_gdf = glaciers_gdf[glaciers_gdf['Area']>1] # greater than 1 km^2
            
            glaciers = glaciers_gdf['RGIId'].values
            
            xmin, ymin, xmax, ymax = glaciers_gdf.total_bounds
            subset = ds_zarr.sel(x=slice(xmin, xmax), y=slice(ymax,ymin))
            times = [pd.to_datetime(i) for i in subset['band1'].time.values]
            time_stamps = np.array([gtsa.utils.date_time_to_decyear(i) for i in times])
            prediction_time_series = gtsa.temporal.create_prediction_timeseries(start_date = '1950-01-01',
                                                                                end_date = '2020-01-01',
                                                                                dt ='Y')
            ds_result = gtsa.temporal.dask_apply_GPR(subset['band1'],
                                                   'time', 
                                                   kwargs={'times':time_stamps,
                                                           'kernel': kernel,
                                                           'prediction_time_series' : prediction_time_series})
            ds_result.to_zarr('rainier.zarr')

#             xmin, ymin, xmax, ymax = ds_zarr['band1'].rio.bounds()
#             bounds_gdf = gtsa.geospatial.bounds2polygon(xmin, xmax, ymin, ymax)
#             glaciers_gdf = gpd.sjoin(rgi02_gdf, bounds_gdf, predicate='intersects') # intersecting glaciers
#             glaciers_gdf = glaciers_gdf[glaciers_gdf['Name'].str.len() > 2] # named
#             glaciers_gdf = glaciers_gdf[glaciers_gdf['Area']>1] # greater than 1 km^2
            
#             glaciers = glaciers_gdf['RGIId'].values

#             for glacier in glaciers:
#                 out = Path(output_directory, glacier).as_posix().replace('.','-')+'.zarr'

#                 glacier_gdf = glaciers_gdf[glaciers_gdf['RGIId'].str.contains(glacier)]
#                 try:
#                     xmin, ymin, xmax, ymax = glacier_gdf.bounds.values[0]
#                     subset = ds_zarr.sel(x=slice(xmin, xmax), y=slice(ymax,ymin))

#                     times = [pd.to_datetime(i) for i in subset['band1'].time.values]
#                     time_stamps = np.array([gtsa.utils.date_time_to_decyear(i) for i in times])
#                     prediction_time_series = gtsa.temporal.create_prediction_timeseries(start_date = '1950-01-01',
#                                                                                         end_date = '2020-01-01',
#                                                                                         dt ='Y')
#                     ds_result = gtsa.temporal.dask_apply_GPR(subset['band1'],
#                                                            'time', 
#                                                            kwargs={'times':time_stamps,
#                                                                    'kernel': kernel,
#                                                                    'prediction_time_series' : prediction_time_series})

#                     ds_result.to_zarr(out)

#                     print(out)
#                 except:
#                     print('NODATA',glacier)
#                     pass




        t2 = time()
        print(f"Took {(t2-t1)/60:.2f} min to process with {workers} workers")
        print('DONE')