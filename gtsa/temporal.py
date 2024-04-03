import numpy as np
import numbers
import pandas as pd
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
import xarray as xr
from gtsa import utils
import gtsa


def create_prediction_timeseries(
    start_date="2000-01-01", end_date="2023-01-01", dt="M", offset=0,
):
    d = pd.date_range(start_date, end_date, freq=dt) + pd.DateOffset(days=offset)
    X = d.to_series().apply([utils.date_time_to_decyear]).values.squeeze()
    return X


def nmad(array):
    if np.all(~np.isfinite(array)):
        return np.nan
    else:
        return 1.4826 * np.nanmedian(np.abs(array - np.nanmedian(array)))


def dask_nmad(DataArray, dim="time"):
    result = xr.apply_ufunc(
        nmad,
        DataArray,
        input_core_dims=[[dim]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
    )
    return result


def GPR_model(X_train, y_train, kernel, alpha=2):
    X_train = X_train.squeeze()[:, np.newaxis]
    y_train = y_train.squeeze()

    gaussian_process_model = GaussianProcessRegressor(
        kernel=kernel,
        normalize_y=True,
        alpha=alpha,
        n_restarts_optimizer=0,
        optimizer=None,
    )

    # print(gaussian_process_model.kernel)
    gaussian_process_model = gaussian_process_model.fit(X_train, y_train)
    return gaussian_process_model


def GPR_predict(gaussian_process_model, X):
    X = X.squeeze()[:, np.newaxis]
    mean_prediction, std_prediction = gaussian_process_model.predict(X, return_std=True)

    return mean_prediction, std_prediction


def dask_GPR(
    DataArray,
    times=None,
    kernel=None,
    prediction_time_series=None,
    alpha=2,
    count_thresh=3,
    time_delta_min=None,
    apply_filter=False,
):
    # assign array of uncertainty values for each data point
    if isinstance(alpha, numbers.Number):
        alphas = np.full(len(DataArray), alpha)
    elif len(alpha) == len(DataArray):
        alphas = alpha

    mask = np.isfinite(DataArray)
    full_mask = mask.copy()

    data_array = DataArray[mask]
    time_array = times[mask]
    alpha_array = alphas[mask]

    if apply_filter and np.sum(mask) > count_thresh:
        # print(np.sum(mask))
        # mask = gtsa.filters.mask_outliers_rate_of_change(time_array,
        #                                     data_array,
        #                                     threshold = 200)

        filt_mask = gtsa.filters.mask_outliers_gaussian_process(
            time_array, data_array, alpha_array
        )
        data_array = data_array[filt_mask]
        time_array = time_array[filt_mask]
        alpha_array = alpha_array[filt_mask]
        full_mask[mask] = filt_mask

    if count_thresh:
        if np.sum(mask) < count_thresh:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a , full_mask

    if time_delta_min:
        time_delta = max(time_array) - min(time_array)
        if time_delta < time_delta_min:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a , full_mask

    model = GPR_model(time_array, data_array, kernel, alpha=alpha_array)

    mean_prediction, std_prediction = GPR_predict(model, prediction_time_series)

    return mean_prediction, std_prediction, full_mask


def dask_apply_GPR(DataArray, dim, kwargs=None):
    results = xr.apply_ufunc(
        dask_GPR,
        DataArray,
        kwargs=kwargs,
        input_core_dims=[[dim]],
        output_core_dims=[["new_time"], ["new_time"], ["input_time"]],
        dask_gufunc_kwargs=dict(output_sizes={"new_time": len(kwargs["prediction_time_series"]),
                                              "input_time": len(kwargs["times"])}),
        output_dtypes=[float, float, bool],
        vectorize=True,
        dask="parallelized",
    )

    mean_prediction, std_prediction, mask = results

    mask = mask.assign_coords(
        {"input_time": kwargs["times"]}
    )
    mask = mask.transpose("input_time", "y", "x")

    mean_prediction = mean_prediction.rename({"new_time": "time"})
    mean_prediction = mean_prediction.assign_coords(
        {"time": kwargs["prediction_time_series"]}
    )
    mean_prediction = mean_prediction.transpose("time", "y", "x")

    std_prediction = std_prediction.rename({"new_time": "time"})
    std_prediction = std_prediction.assign_coords(
        {"time": kwargs["prediction_time_series"]}
    )
    std_prediction = std_prediction.transpose("time", "y", "x")

    mean_prediction.data = mean_prediction.data.rechunk(
        {0: "auto", 1: "auto", 2: "auto"}, block_size_limit=1e8, balance=True
    )
    std_prediction.data = std_prediction.data.rechunk(
        {0: "auto", 1: "auto", 2: "auto"}, block_size_limit=1e8, balance=True
    )

    ds = xr.Dataset(
        {"mean_prediction": mean_prediction, 
        "std_prediction": std_prediction,
        "mask":mask}
    )

    return ds


def dask_apply_func(DataArray, func):
    result = xr.apply_ufunc(
        func,
        DataArray,
        dask="allowed",
    )
    return result


def GPR_kernel_smoother():
    kernel = ConstantKernel(30) * Matern(length_scale=10.0, nu=1.5)
    return kernel


def GPR_kernel_projection_decadal():
    kernel = ConstantKernel(30) * ExpSineSquared(length_scale=1, periodicity=30)
    return kernel


def GPR_kernel_projection_seasonal():
    kernel = ConstantKernel(30) * ExpSineSquared(length_scale=6, periodicity=1)
    return kernel


def GPR_glacier_kernel():
    k1 = ConstantKernel(30) * Matern(length_scale=30.0, nu=1.5)
    k2 = ConstantKernel(30) * Matern(length_scale=10.0, nu=1.5)
    k3 = ConstantKernel(30) * ExpSineSquared(length_scale=6, periodicity=1)

    # k1 = ConstantKernel(30) * Matern(length_scale=30.0, nu=1.5)
    # k2 = ConstantKernel(30) * ExpSineSquared(length_scale=1, periodicity=30)
    # k3 = ConstantKernel(30) * ExpSineSquared(length_scale=1, periodicity=1)

    # k1 = GPR_kernel_smoother()
    # k2 = GPR_kernel_projection_seasonal()
    # k3 = GPR_kernel_projection_decadal()

    kernel = k1 + k2 + k3
    return kernel

    #     # fit data tight
    #     kernel = RBF(5) * ConstantKernel(100) + RBF(20) + RBF(100) * PairwiseKernel(1, metric='linear')
    #     # fit data coarse
    #     kernel = RBF(5) + RBF(20) + RBF(100) * PairwiseKernel(1, metric='linear')


def GPR_pyddem_kernel():
    """
    https://github.com/iamdonovan/pyddem/blob/main/pyddem/fit_tools.py#L1147
    """
    base_var = 50.0
    period_nonlinear = 100.0  # 20 to 100
    nonlin_var = 500  # or MSE from linear fit

    k1 = PairwiseKernel(1, metric="linear")
    k2 = ConstantKernel(30) * ExpSineSquared(length_scale=1, periodicity=1)
    k3 = (
        ConstantKernel(base_var * 0.6) * RBF(0.75)
        + ConstantKernel(base_var * 0.3) * RBF(1.5)
        + ConstantKernel(base_var * 0.1) * RBF(3)
    )
    k4 = (
        PairwiseKernel(1, metric="linear")
        * ConstantKernel(nonlin_var)
        * RationalQuadratic(period_nonlinear, 10)
    )

    kernel = k1 + k2 + k3 + k4
    return kernel
