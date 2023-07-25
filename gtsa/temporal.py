import numpy as np
import numbers
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
import xarray as xr
from gtsa import utils


def create_prediction_timeseries(
    start_date="2000-01-01", end_date="2023-01-01", dt="M"
):
    d = pd.date_range(start_date, end_date, freq=dt)
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
):
    # assign array of uncertainty values for each data point
    if isinstance(alpha, numbers.Number):
        alphas = np.full(len(DataArray), alpha)
    elif len(alpha) == len(DataArray):
        alphas = alpha

    mask = np.isfinite(DataArray)

    data_array = DataArray[mask]
    time_array = times[mask]
    alpha_array = alphas[mask]

    if count_thresh:
        if np.sum(mask) < count_thresh:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a

    if time_delta_min:
        time_delta = max(time_array) - min(time_array)
        if time_delta < time_delta_min:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a

    model = GPR_model(time_array, data_array, kernel, alpha=alpha_array)

    mean_prediction, std_prediction = GPR_predict(model, prediction_time_series)

    return mean_prediction, std_prediction


def dask_apply_GPR(DataArray, dim, kwargs=None):
    results = xr.apply_ufunc(
        dask_GPR,
        DataArray,
        kwargs=kwargs,
        input_core_dims=[[dim]],
        output_core_dims=[["new_time"], ["new_time"]],
        output_sizes={"new_time": len(kwargs["prediction_time_series"])},
        output_dtypes=[float, float],
        vectorize=True,
        dask="parallelized",
    )

    mean_prediction, std_prediction = results
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
        {"mean_prediction": mean_prediction, "std_prediction": std_prediction}
    )

    return ds


def dask_apply_func(DataArray, func):
    result = xr.apply_ufunc(
        func,
        DataArray,
        dask="allowed",
    )
    return result
