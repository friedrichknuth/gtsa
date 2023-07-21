import gtsa

from pathlib import Path
import psutil
import xarray as xr
import rasterio
import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn import linear_model
import matplotlib.pyplot as plt
import hvplot.xarray

'''
WIP

See notebook
'''

data_dirs = ['../../data/dems/south-cascade',
             '../../data/dems/mount-baker']

if __name__ == "__main__":

    workers = psutil.cpu_count(logical=True)-1

    client = gtsa.io.dask_start_cluster(workers,
                                        ip_addres=None,
                                        port=':8786')
    
    c = 0
    for data_dir in data_dirs:
    
        zarr_fn = Path(data_dir, 'stack/stack.zarr').as_posix()
        ds = xr.open_dataset(zarr_fn,chunks='auto',engine='zarr')
        
        # optimize chunks and reload lazily
        tc,yc,xc = gtsa.io.determine_optimal_chuck_size(ds,print_info = True) 
        ds = xr.open_dataset(zarr_fn,chunks={'time': tc, 'y': yc, 'x':xc},engine='zarr')
    
        # assign crs back
        crs = rasterio.crs.CRS.from_epsg(32610)
        ds = ds.rio.write_crs(crs)
    
        # ds = gtsa.geospatial.extract_dataset_center_window(ds, size = 500)
    
        count = ds['band1'].count(axis=0).compute()
        
        fig, ax = plt.subplots()
        count.plot(ax=ax)
        fig.savefig('figname_'+str(c)+'.png', bbox_inches='tight')
        c+=1
    
    print('DONE')