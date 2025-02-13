import numpy as np
import numbers
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
import xarray as xr
from gtsa import utils




def error_wrapper(da, reference_raster, glacier_mask):
    # da is the data array for a single time step (2D array)
    # reference_raster is a xdem.DEM object
    # glacier_mask is a xdem.DEM object

    # If the data array is all NaNs, return NaN
    if np.all(~np.isfinite(da)):
        return np.nan
    # Otherwise, calculate the uncertainty with xDEM
    else:
        dem = xdem.DEM.from_array(da, transform=reference_raster.transform, crs=reference_raster.crs)
        uncertainty, variogram = dem.estimate_uncertainty(reference_raster, stable_terrain=glacier_mask)
        return uncertainty.data.data


def calculate_error(da, xdem, glacier_mask, chunk_size=(100, 100)):
    # da is the xarray.DataArray object
    # xdem is the xdem.DEM object
    # glacier_mask is the xdem.DEM object

    # Ensure the dataset is not chunked in time
    da = ds.chunk({"time": -1, "x": chunk_size[0], "y": chunk_size[1]})
    # Initialize the error array
    error = np.zeros(da.shape[0])

    # Loop through each time step
    for i in tqdm(range(da.shape[0])):
        # The error computation might not work if no stable ground pixels are present
        try:
            test = error_wrapper(da.isel(time=i).values, xdem.DEM(reference_raster), glacier_mask) # Calculate the uncertainty
            error[i] = np.nanmean(test) # Store the mean uncertainty for the slice (time step)
        except:
            error[i] = np.nan # If the computation fails, store NaN
            print(f"Failed for {i}") # Print the time step that failed

    error[np.isnan(error)] = np.nanmean(error) # Replace NaNs with the mean uncertainty

    return error


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


def GPR_model(X_train, y_train, kernel, alpha=2, iterations=False, n_iter=0):
    X_train = X_train.squeeze()[:, np.newaxis]
    y_train = y_train.squeeze()

    if iterations:
        gaussian_process_model = GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            alpha=alpha**2, # As recommended by the scikit-learn documentation https://scikit-learn.org/stable/auto_examples/gaussian_process/plot_gpr_noisy_targets.html
            n_restarts_optimizer=n_iter,
            optimizer='fmin_l_bfgs_b',
        )
    else:
         gaussian_process_model = GaussianProcessRegressor(
            kernel=kernel,
            normalize_y=True,
            alpha=alpha**2, # As recommended by the scikit-learn documentation https://scikit-learn.org/stable/auto_examples/gaussian_process/plot_gpr_noisy_targets.html
            n_restarts_optimizer=n_iter,
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
    iterations=False,
    n_iter=0,
    count_thresh=3,
    time_delta_min=None,
):
    # assign array of uncertainty values for each data point
    if isinstance(alpha, numbers.Number):
        alpha = np.full(len(DataArray), alpha)
    elif len(alpha) == len(DataArray):
        alpha = alpha

    mask = np.isfinite(DataArray)

    data_array = DataArray[mask]
    time_array = times[mask]
    alpha_array = alpha[mask]

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

    model = GPR_model(time_array, data_array, kernel, alpha=alpha_array, iterations=iterations, n_iter=n_iter)

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
