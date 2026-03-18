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
    start_date="2000-01-01",
    end_date="2023-01-01",
    dt="M",
    offset=0,
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


def GPR_model(X_train, y_train, kernel, alpha=2, normalize_y = True):
    X_train = X_train.squeeze()[:, np.newaxis]
    y_train = y_train.squeeze()

    gaussian_process_model = GaussianProcessRegressor(
        kernel=kernel,
        normalize_y=normalize_y,
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
    time_array,
    data_array,
    alpha_array,
    kernel=None,
    kernel_factory=None,
    times=None,
    prediction_time_series=None,
    count_thresh=3,
    time_delta_min=None,
    apply_filter=False,
    normalize_y=True,
    center_time=False,
):
    # assign array of uncertainty values for each data point
    # if isinstance(alpha, numbers.Number):
    #     alphas = np.full(len(data_array), alpha)
    # elif len(alpha) == len(data_array):
    #     alphas = alpha

    mask = np.isfinite(data_array)
    full_mask = mask.copy()

    data_array = data_array[mask]
    time_array = time_array[mask]
    alpha_array = alpha_array[mask]
    
    if np.all(~np.isfinite(data_array)):
        a = prediction_time_series.copy()
        a[:] = np.nan
        return a, a, full_mask
        
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
        if len(data_array) < count_thresh:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a, full_mask

    if time_delta_min:
        time_delta = max(time_array) - min(time_array)
        if time_delta < time_delta_min:
            a = prediction_time_series.copy()
            a[:] = np.nan
            return a, a, full_mask

    if np.all(~np.isfinite(data_array)):
        a = prediction_time_series.copy()
        a[:] = np.nan
        return a, a, full_mask

    # Build kernel from factory if provided (data-dependent kernels)
    if kernel_factory is not None:
        kernel = kernel_factory(time_array, data_array, alpha_array)

    # Centre time axis around mean (needed for linear-kernel stability)
    if center_time:
        mu_x = np.nanmean(time_array)
        time_array = time_array - mu_x
        prediction_time_series = prediction_time_series - mu_x

    # When normalize_y=False, manually subtract data mean before fitting
    # and add it back after prediction (matching pyddem behaviour).
    # When normalize_y=True, sklearn handles this internally.
    mu_y = 0.0
    if not normalize_y:
        mu_y = np.nanmean(data_array)
        data_array = data_array - mu_y

    model = GPR_model(time_array, data_array, kernel, alpha=alpha_array, normalize_y=normalize_y)

    mean_prediction, std_prediction = GPR_predict(model, prediction_time_series)

    if not normalize_y:
        mean_prediction = mean_prediction + mu_y

    return mean_prediction, std_prediction, full_mask


def dask_apply_GPR(ds, variable_name="band1", alphas_name="uncertainty", kwargs=None):
    results = xr.apply_ufunc(
        dask_GPR,
        ds["time"],
        ds[variable_name],
        ds[alphas_name],
        kwargs=kwargs,
        input_core_dims=[["time"], ["time"], ["time"]],
        output_core_dims=[["new_time"], ["new_time"], ["input_time"]],
        dask_gufunc_kwargs=dict(
            output_sizes={
                "new_time": len(kwargs["prediction_time_series"]),
                "input_time": len(ds["time"].values),
            }
        ),
        output_dtypes=[float, float, bool],
        vectorize=True,
        dask="parallelized",
    )

    mean_prediction, std_prediction, mask = results

    mask = mask.assign_coords({"input_time": ds["time"].values})
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
        {
            "mean_prediction": mean_prediction,
            "std_prediction": std_prediction,
            "mask": mask,
        }
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


def GPR_pyddem_kernel(time_vals=None, data_vals=None, err_vals=None):
    """
    Adaptation of the pyddem final_fit kernel.
    https://github.com/iamdonovan/pyddem/blob/main/pyddem/fit_tools.py#L1147

    When called with no arguments, returns the kernel with static
    default hyperparameters (backward-compatible).

    When called with per-pixel data, computes data-dependent
    hyperparameters following the pyddem final_fit logic:
      - nonlin_var  = mean(err) + (RMSE / standardized_RMSE)^2
      - period_nonlinear = min(100, 100 / standardized_RMSE^2)

    Parameters
    ----------
    time_vals : array-like or None
        Decimal-year time values (after outlier filtering).
    data_vals : array-like or None
        Elevation values (after outlier filtering).
    err_vals : array-like or None
        Squared uncertainties (variance), i.e. uncertainty**2.

    Returns
    -------
    kernel : sklearn kernel
    """
    base_var = 50.0

    if (time_vals is not None
            and data_vals is not None
            and err_vals is not None
            and len(time_vals) >= 2):
        # Weighted least-squares linear fit (pyddem wls_matrix equivalent)
        w = 1.0 / np.asarray(err_vals, dtype=float)
        t = np.asarray(time_vals, dtype=float)
        d = np.asarray(data_vals, dtype=float)
        w_sum = w.sum()
        w_x = (w * t).sum() / w_sum
        w_y = (w * d).sum() / w_sum
        beta1 = ((w * (t - w_x) * (d - w_y)).sum()
                 / (w * (t - w_x) ** 2).sum())
        beta0 = w_y - beta1 * w_x
        residuals = d - (beta0 + beta1 * t)
        res = np.sqrt(np.mean(residuals ** 2))
        res_stdized = np.sqrt(np.mean(residuals ** 2 / np.asarray(err_vals, dtype=float)))

        if res_stdized != 0:
            nonlin_var = np.mean(err_vals) + (res / res_stdized) ** 2
            period_nonlinear = min(100.0, 100.0 / res_stdized ** 2)
        else:
            nonlin_var = np.mean(err_vals)
            period_nonlinear = 100.0
    else:
        # Static defaults (original behaviour)
        period_nonlinear = 100.0
        nonlin_var = 500

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
