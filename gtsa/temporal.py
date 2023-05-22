import multiprocessing as mp

import matplotlib
import numpy as np
import pandas as pd
import psutil
from sklearn import linear_model
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import (
    RBF,
    ConstantKernel,
    ExpSineSquared,
    PairwiseKernel,
    RationalQuadratic,
    WhiteKernel,
    Matern,
)
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import statsmodels.api as sm
from tqdm import tqdm

import xarray as xr
import dask

from gtsa import utils

from sklearn.utils import all_estimators
import inspect

def check_sklearn_parallell_support():
    # source: https://gist.github.com/rikturr/ca4449a87fcd512d3d846341949d1b34
    has_n_jobs = []
    for est in all_estimators():
        s = inspect.signature(est[1])
        if 'n_jobs' in s.parameters:
            has_n_jobs.append(est)
    print(has_n_jobs)

def remove_nan_from_training_data(X_train, y_train_masked_array):
    array = y_train_masked_array.data
    mask = ~np.ma.getmaskarray(y_train_masked_array)
    X_train = X_train[mask]
    y_train = y_train_masked_array[mask]
    return X_train, y_train


def mask_low_count_pixels(ma_stack, n_thresh=3):
    count = np.ma.masked_equal(ma_stack.count(axis=0), 0).astype(np.uint16).data
    valid_mask_2D = count >= n_thresh
    valid_data = ma_stack[:, valid_mask_2D]
    return valid_data, valid_mask_2D


def create_prediction_timeseries(start_date="2000-01-01", end_date="2023-01-01", dt="M"):
    # M  = monthly frequency
    # 3M = every 3 months
    # 6M = every 6 months
    d = pd.date_range(start_date, end_date, freq=dt)
    X = d.to_series().apply([utils.date_time_to_decyear]).values.squeeze()
    return X

""" Polynomial fitting functions """

def poly_n_deg(x, *p):
    poly = 0.
    for i, n in enumerate(p):
        poly += n * x**i
    return poly
    
def poly_fit(X_train, y_train, deg=6):
    if len(X_train) < deg:
        deg = len(X_train)
#         print(deg)
    p0 = np.ones(deg,)
    coeff, var_matrix = curve_fit(poly_n_deg,
                                  X_train,
                                  y_train, 
                                  p0=p0)
    return coeff

def poly_run(args, deg=6):
    X_train, y_train_masked_array, deg = args
    X_train, y_train = remove_nan_from_training_data(X_train, y_train_masked_array)
    coeff = poly_fit(X_train, y_train, deg=deg)
    return coeff

def poly_predict(args):
    X, coeff = args
    prediction = [poly_n_deg(x, *tuple(coeff)) for x in X]
    return prediction

def poly_predict_parallel(X, coeff, cpu_count=None):
    if not cpu_count:
        cpu_count = mp.cpu_count() - 1
    pool = mp.Pool(processes=cpu_count)
    results = pool.map(poly_predict, tqdm([(x, coeff) for x in X]))
    return np.ma.array(results)

def poly_run_parallel(X_train, ma_stack, cpu_count=None, deg=6):
    if not cpu_count:
        cpu_count = mp.cpu_count() - 1
    pool = mp.Pool(processes=cpu_count)
    results = pool.map(poly_run, tqdm([(X_train, ma_stack[:, i], deg) for i in range(ma_stack.shape[1])]))
    return np.array(results)

def poly_reshape_parallel_results(results, ma_stack, valid_mask_2D):
    results_stack = []
    print(results.shape)
    m = np.ma.masked_all_like(ma_stack[0])
    m[valid_mask_2D] = results[:]
    return m
#     for i in range(results.shape[1]):
#         m = np.ma.masked_all_like(ma_stack[0])
#         m[valid_mask_2D] = results[:, i]
#         results_stack.append(m)
#     results_stack = np.ma.stack(results_stack)
#     return results_stack

""" Linear fitting functions """

def linreg_fit(X_train, y_train, method="TheilSen"):

    if method == "Linear":
        m = linear_model.LinearRegression()
        m.fit(X_train.squeeze()[:, np.newaxis], y_train.squeeze())
        slope = m.coef_
        intercept = m.intercept_

    if method == "TheilSen":
        m = linear_model.TheilSenRegressor()
        m.fit(X_train.squeeze()[:, np.newaxis], y_train.squeeze())
        slope = m.coef_
        intercept = m.intercept_

    if method == "RANSAC":
        m = linear_model.RANSACRegressor()
        m.fit(X_train.squeeze()[:, np.newaxis], y_train.squeeze())
        slope = m.estimator_.coef_
        intercept = m.estimator_.intercept_

    return slope[0], intercept
    
def linreg_run(args):
    X_train, y_train_masked_array, method = args

    X_train, y_train = remove_nan_from_training_data(X_train, y_train_masked_array)
    slope, intercept = linreg_fit(X_train, y_train, method=method)

    return slope, intercept


def linreg_predict(args):
    slope, x, intercept = args
    prediction = slope * x + intercept
    return prediction


def linreg_predict_parallel(slope, X, intercept, cpu_count=None):
    if not cpu_count:
        cpu_count = mp.cpu_count() - 1
    pool = mp.Pool(processes=cpu_count)
    results = pool.map(linreg_predict, tqdm([(slope, x, intercept) for x in X]))
    return np.ma.array(results)


def linreg_run_parallel(X_train, ma_stack, cpu_count=None, method="TheilSen"):
    if not cpu_count:
        cpu_count = mp.cpu_count() - 1
    pool = mp.Pool(processes=cpu_count)
    results = pool.map(linreg_run, tqdm([(X_train, ma_stack[:, i], method) for i in range(ma_stack.shape[1])]))
    return np.array(results)

def linreg_reshape_parallel_results(results, ma_stack, valid_mask_2D):
    results_stack = []
    for i in range(results.shape[1]):
        m = np.ma.masked_all_like(ma_stack[0])
        m[valid_mask_2D] = results[:, i]
        results_stack.append(m)
    results_stack = np.ma.stack(results_stack)
    return results_stack

""" Gaussian Process Regression """

def GPR_CO2_kernel():
    """
    adapted from
    https://scikit-learn.org/stable/auto_examples/gaussian_process/plot_gpr_co2.html#sphx-glr-auto-examples-gaussian-process-plot-gpr-co2-py
    """
    
    long_term_trend_kernel = 50.0**2 * RBF(length_scale=50.0)

    seasonal_kernel = (
        2.0**2
        * RBF(length_scale=100.0)
        * ExpSineSquared(length_scale=1.0, periodicity=1.0, periodicity_bounds="fixed")
    )

    irregularities_kernel = 0.5**2 * RationalQuadratic(length_scale=1.0, alpha=1.0)

    noise_kernel = 0.1**2 * RBF(length_scale=0.1) + WhiteKernel(
        noise_level=0.1**2, noise_level_bounds=(1e-5, 1e5)
    )

    co2_kernel = (long_term_trend_kernel + seasonal_kernel + irregularities_kernel + noise_kernel)
    co2_kernel

def GPR_huggonet_kernel():
    """
    https://github.com/iamdonovan/pyddem/blob/master/pyddem/fit_tools.py#L1054
    """
    base_var = 50.
    period_nonlinear = 100.
    nonlin_var = 0
    
    k1 = PairwiseKernel(1, metric='linear')
    k2 = ConstantKernel(30) * ExpSineSquared(length_scale=1, periodicity=1)
    k3 = (
        ConstantKernel(base_var * 0.6) * RBF(0.75) + \
        ConstantKernel(base_var * 0.3) * RBF(1.5) + \
        ConstantKernel(base_var * 0.1) * RBF(3)
    )
    k4 = (PairwiseKernel(1, metric="linear") * \
         ConstantKernel(nonlin_var) * \
         RationalQuadratic(period_nonlinear, 1)
         )

    
    kernel = k1+k2+k3+k4
    return(kernel)

def GPR_glacier_kernel():
    
#     # fit data tight
#     kernel = RBF(5) * ConstantKernel(100) + RBF(20) + RBF(100) * PairwiseKernel(1, metric='linear')
#     # fit data coarse
#     kernel = RBF(5) + RBF(20) + RBF(100) * PairwiseKernel(1, metric='linear') 
    
    k1 = 30.0 * Matern(length_scale=10.0, nu=1.5)
    k2 = ConstantKernel(30) * ExpSineSquared(length_scale=1, periodicity=30)
    k3 = ConstantKernel(30) * ExpSineSquared(length_scale=1, periodicity=1)
    
    kernel = k1 + k2 + k3

    return kernel

def GPR_model(X_train, y_train, kernel, alpha=2):
    X_train = X_train.squeeze()[:, np.newaxis]
    y_train = y_train.squeeze()

#     gaussian_process_model = GaussianProcessRegressor(
#         kernel=kernel, normalize_y=True, alpha=alpha, n_restarts_optimizer=9,
#     )
    gaussian_process_model = GaussianProcessRegressor(
        kernel=kernel, normalize_y=True, alpha=alpha, n_restarts_optimizer=0, optimizer=None,
    )

    gaussian_process_model = gaussian_process_model.fit(X_train, y_train)
    return gaussian_process_model


def GPR_predict(gaussian_process_model, X):
    X = X.squeeze()[:, np.newaxis]
    mean_prediction, std_prediction = gaussian_process_model.predict(X, return_std=True)

    return mean_prediction, std_prediction


def GPR_run(args):
    X_train, y_train_masked_array, X, glacier_kernel = args
    X_train, y_train = remove_nan_from_training_data(X_train, y_train_masked_array)
    gaussian_process_model = GPR_model(X_train, y_train, glacier_kernel, alpha=2)
    prediction, std_prediction = GPR_predict(gaussian_process_model, X)

    return prediction


def GPR_run_parallel(X_train, ma_stack, X, kernel, cpu_count=None):
    if not cpu_count:
        cpu_count = mp.cpu_count() - 1
    pool = mp.Pool(processes=cpu_count)
    results = pool.map(GPR_run, tqdm([(X_train, ma_stack[:, i], X, kernel) for i in range(ma_stack.shape[1])]))
    return np.array(results)


def GPR_reshape_parallel_results(results, ma_stack, valid_mask_2D):
    results_stack = []
    for i in range(results.shape[1]):
        m = np.ma.masked_all_like(ma_stack[0])
        m[valid_mask_2D] = results[:, i]
        results_stack.append(m)
    results_stack = np.ma.stack(results_stack)
    return results_stack


""" Dask functions """

def dask_GPR(DataArray, 
             times = None,
             kernel = None,
             prediction_time_series = None,
             alpha = 2,
             count_thresh = 3, 
             time_delta_min = None):
    
    # TODO change to isfinite
    mask = ~np.isnan(DataArray)
    
    if count_thresh:
        if np.sum(mask) < count_thresh:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a
    
    if time_delta_min:
        time_delta = max(times[mask]) - min(times[mask])
        if time_delta < time_delta_min:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a
        
    
    model = GPR_model(times[mask], DataArray[mask], kernel, alpha=alpha)
    
    mean_prediction, std_prediction = GPR_predict(model, prediction_time_series)
    
    return mean_prediction, std_prediction
    
def dask_apply_GPR(DataArray, dim, kwargs=None):
    results = xr.apply_ufunc(
        dask_GPR,
        DataArray,
        kwargs=kwargs,
        input_core_dims=[[dim]],
        output_core_dims=[['new_time'], ['new_time']],
        output_sizes={'new_time': len(kwargs['prediction_time_series'])},
        output_dtypes=[float, float],
        vectorize=True,
        dask="parallelized")
    
    mean_prediction, std_prediction = results
    mean_prediction = mean_prediction.rename({'new_time': 'time'})
    mean_prediction = mean_prediction.assign_coords({"time": kwargs['prediction_time_series']})
    mean_prediction = mean_prediction.transpose('time', 'y', 'x')

    std_prediction = std_prediction.rename({'new_time': 'time'})
    std_prediction = std_prediction.assign_coords({"time": kwargs['prediction_time_series']})
    std_prediction = std_prediction.transpose('time', 'y', 'x')
    
    mean_prediction.data = mean_prediction.data.rechunk({0:'auto', 1:'auto', 2:'auto'},
                                                          block_size_limit=1e8, 
                                                          balance=True)
    std_prediction.data = std_prediction.data.rechunk({0:'auto', 1:'auto', 2:'auto'},
                                                          block_size_limit=1e8, 
                                                          balance=True)
    
    ds = xr.Dataset({'mean_prediction':mean_prediction,
                     'std_prediction':std_prediction})
    
    return ds


def dask_linreg(DataArray, times = None, count_thresh = None, time_delta_min = None):
    """
    Apply linear regression to DataArray.
    Returns np.nan if valid pixel count less than count_thresh
    and/or difference between first and last time stamp less than time_delta_min.
    
    Default value for time_delta_min assumes times are provided in days.
    """
    mask = ~np.isnan(DataArray)
    
    if count_thresh:
        if np.sum(mask) < count_thresh:
            return np.nan, np.nan
    
    if time_delta_min:
        time_delta = max(times[mask]) - min(times[mask])
        if time_delta < time_delta_min:
            return np.nan, np.nan

#     m = linear_model.LinearRegression()
    m = linear_model.TheilSenRegressor()
    m.fit(times[mask].reshape(-1,1), DataArray[mask])
    
    return m.coef_[0], m.intercept_

def dask_apply_linreg(DataArray, dim, kwargs=None):
    # TODO check if da.map_blocks is faster / more memory efficient
    # using da.apply_ufunc for now.
    # da.map_blocks can handle chunked time dim blocks. 
    results = xr.apply_ufunc(
        dask_linreg,
        DataArray,
        kwargs=kwargs,
        input_core_dims=[[dim]],
        output_core_dims=[[],[]],
        vectorize=True,
        dask="parallelized",)
    return results

def nmad(DataArray):
    if np.all(np.isnan(DataArray)):
        return np.nan
    else:
        return 1.4826 * np.nanmedian(np.abs(DataArray - np.nanmedian(DataArray)))
    
def count(DataArray):
    return np.nansum(~np.isnan(DataArray))

def apply_nmad(DataArray):
    return np.apply_along_axis(nmad,0,DataArray)

def apply_count(DataArray):
    return np.apply_along_axis(count,0,DataArray)

def dask_apply_func(DataArray, func):
    result = xr.apply_ufunc(
        func,
        DataArray,
        dask="allowed",)
    return result

def xr_dask_count(ds):
    """
    Computes count along time axis in x, y, time in dask.array.core.Array.
    
    Returns xr.DataArray with x, y dims.
    """
    arr_count = dask_apply_func(ds['band1'].data, apply_count).compute()
    arr_count = np.ma.masked_where(arr_count==0,arr_count)
    
    count_da = ds['band1'].isel(time=0).drop('time')
    count_da.values = arr_count
    count_da.name = 'count'
    
    return count_da
    
def xr_dask_nmad(ds):
    """
    Computes NMAD along time axis in x, y, time in dask.array.core.Array.
    
    Returns xr.DataArray with x, y dims.
    """
    arr_nmad = dask_apply_func(ds['band1'].data, apply_nmad).compute()
    nmad_da = ds['band1'].isel(time=0).drop('time')
    nmad_da.values = arr_nmad
    nmad_da.name   = 'nmad'
    
    return nmad_da