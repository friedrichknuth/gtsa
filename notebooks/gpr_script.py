import gtsa

from gtsa import temporal, plotting, utils

import os
import glob
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings('ignore')


data_dir    = gtsa.pathlib.Path('/mnt/storage/knuth/sites/scg/hsfm_data/final_products')

dems_fn       = sorted(data_dir.glob('dem*.tif'))

data_dir    = gtsa.pathlib.Path('/mnt/storage/knuth/sites/scg/hsfm_data')
glacier_fn     = data_dir.joinpath('rgi_glacier_oultine.geojson')
reference_dem  = data_dir.joinpath('reference_dem.tif')

reference_dem = gtsa.gdal.resample_dem(reference_dem, res=5)

date_times = [d for d in gtsa.io.parse_timestamps(dems_fn)]
dates = [d.date() for d in date_times]


ds = gtsa.io.xr_stack_geotifs(dems_fn,
                              date_times,
                              reference_dem,
                              resampling="bilinear",
                              save_to_nc = False)

ma_stack = gtsa.io.np.ma.masked_invalid(ds['band1'].values)

X = gtsa.temporal.create_prediction_timeseries(start_date = dates[0].strftime("%Y-%m-%d"),
                                               end_date = dates[-1].strftime("%Y-%m-%d"),
                                               dt ='M')

X_train = np.ma.array([utils.date_time_to_decyear(i) for i in date_times]).data
test_stack = ma_stack

valid_data, valid_mask_2D = temporal.mask_low_count_pixels(test_stack, n_thresh = 3)

glacier_kernel = temporal.GPR_glacier_kernel()
print("Running GPR")
results = temporal.GPR_run_parallel(X_train, valid_data, X, glacier_kernel)

prediction_stack = temporal.GPR_reshape_parallel_results(results, test_stack, valid_mask_2D)

np.savez_compressed('prediction_stack.npz', 
                    data=prediction_stack.data, 
                    mask=prediction_stack.mask)

print('Done')