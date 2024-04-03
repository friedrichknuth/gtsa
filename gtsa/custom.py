import numpy as np
import xarray as xr
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
import gtsa

# def func(ds, variable_name="band1"):


#     kernel = gtsa.temporal.GPR_glacier_kernel()
#     # kernel = gtsa.temporal.GPR_kernel_smoother()

#     # Create time series for predictions
#     prediction_time_series = gtsa.temporal.create_prediction_timeseries(start_date = '1946-09-01',
#                                                end_date = '2023-09-01',
#                                                dt ='M')

#     nmads_csv = '/Users/knuth/Documents/data/dems/mount-baker/DEMs_combined/nmads.csv'
#     # nmads_csv = '/Users/knuth/Documents/data/dems/south-cascade/DEMs_combined/nmads_2013-2015_ref.csv'
#     nmad_df = pd.read_csv(nmads_csv)
#     alphas = nmad_df['nmad'].values
#     print(alphas)

#     result = gtsa.temporal.dask_apply_GPR(
#         ds[variable_name],
#         "time",
#         kwargs={
#             "times": ds[variable_name].time.values,
#             "kernel": kernel,
#             "prediction_time_series": prediction_time_series,
#             "alpha":alphas,
#             "apply_filter": True,
#         },
#     )
#     return result


# scg
def func(ds, variable_name="band1"):
    kernel = gtsa.temporal.GPR_glacier_kernel()
    # kernel = gtsa.temporal.GPR_kernel_smoother()

    # Create time series for predictions
    prediction_time_series = gtsa.temporal.create_prediction_timeseries(
        start_date="1956-09-01", end_date="2024-09-01", dt="M"
    )
    # prediction_time_series = gtsa.temporal.create_prediction_timeseries(start_date = '1956-09-01',
    #                                                end_date = '2023-09-01',
    #                                                dt ='A-SEP')

    # ## Add time validation time stamps to make predictions there as well
    # validation_ds = ds.sel(time=slice('1956-01-01','2000-01-01')).copy()
    # prediction_time_series = list(prediction_time_series)
    # [prediction_time_series.append(x) for x in [gtsa.utils.date_time_to_decyear(pd.to_datetime(y)) for y in validation_ds['time'].values]]
    # prediction_time_series = np.array(sorted(prediction_time_series))

    ## Select by coverage
    pct_coverage_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_combined/pct_coverage_2013-2015_ref.csv"
    # pct_coverage_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_combined/pct_coverage_2015_ref.csv"
    # pct_coverage_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_USGS/pct_coverage_2013-2015_ref.csv"
    pct_coverage_df = pd.read_csv(pct_coverage_csv)
    pct_coverage_df["date"] = pd.to_datetime(pct_coverage_df["dem"])
    selection_dates_all = pct_coverage_df["date"].values

    # # select by percent coverage + first and last full coverage
    # pct_coverage_df_full = pct_coverage_df[pct_coverage_df["pct_coverage"] > 0.95]
    # selection_dates_full = pct_coverage_df_full["date"].values
    # pct_coverage_df_partial = pct_coverage_df[pct_coverage_df["pct_coverage"] <= 0.95]
    # selection_dates_partial = pct_coverage_df_partial["date"].values

    # pct_coverage_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_USGS/pct_coverage_2013-2015_ref.csv"
    # pct_coverage_df = pd.read_csv(pct_coverage_csv)
    # pct_coverage_df["date"] = pd.to_datetime(pct_coverage_df["dem"])
    # pct_coverage_df_usgs = pct_coverage_df.copy()

    # pct_coverage_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_HSfM/pct_coverage_2013-2015_ref.csv"
    # pct_coverage_df = pd.read_csv(pct_coverage_csv)
    # pct_coverage_df["date"] = pd.to_datetime(pct_coverage_df["dem"])
    # pct_coverage_df_hsfm = pct_coverage_df.copy()

    # selection_dates_all = sorted(set(list(pct_coverage_df_usgs['date'].values) + list(pct_coverage_df_hsfm['date'].values)))

    selection_dates = list(selection_dates_all)
    # selection_dates = list(selection_dates_full)
    # selection_dates = list(selection_dates_partial)
    # selection_dates = list([selection_dates_full[0],]) + list(selection_dates_partial) + list([selection_dates_full[-1],])

    nmads_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_combined/nmads_2013-2015_ref.csv"
    # nmads_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_combined/nmads_2015_ref.csv"
    # nmads_csv = "/Users/knuth/Documents/data/dems/south-cascade/DEMs_USGS/nmads_2013-2015_ref.csv"
    nmad_df = pd.read_csv(nmads_csv)
    nmad_df["date"] = pd.to_datetime(nmad_df["dem"])
    nmad_df = nmad_df.set_index("date")
    nmad_df = nmad_df[nmad_df.index.isin(selection_dates)]
    alphas = nmad_df["nmad"].values
    # print(len(alphas))

    selection_dates = [pd.to_datetime(x) for x in selection_dates]
    selection_dates = [gtsa.utils.date_time_to_decyear(x) for x in selection_dates]
    ds = ds.sel(time=selection_dates, method="nearest")

    a = sorted(list(selection_dates) + list(prediction_time_series))
    prediction_time_series = np.array(a)

    result = gtsa.temporal.dask_apply_GPR(
        ds[variable_name],
        "time",
        kwargs={
            "times": ds[variable_name].time.values,
            "kernel": kernel,
            "prediction_time_series": prediction_time_series,
            "alpha": alphas,
            "apply_filter": True,
        },
    )
    return result


# def func(ds, variable_name='band1'):
#     from sklearn import linear_model
#     '''
#     The `gtsa` command line utilitiy will look for a function called `func` in gtsa.custom and pass the xarray DataArray to it.
#     You can use this function to do whatever you want with the DataArray. As an example, this function computes the nmad along the time axis.
#     '''

#     def ts_linreg(x,y, threshold = 2):
#         mask = np.isfinite(y)
#         if len(y[mask]) < threshold:
#             return np.nan
#         m = linear_model.TheilSenRegressor()
#         return m.fit(x[mask][:, np.newaxis], y[mask]).coef_ # return slope

#     decyear_times = ds['time'].values

#     result = xr.apply_ufunc(ts_linreg,
#                             decyear_times ,
#                             ds[variable_name],
#                             input_core_dims=[['time'], ['time']],
#                             vectorize=True,
#                             dask='parallelized',
#                             output_dtypes=[float],
#                         )

#     return result


# def func(ds, variable_name='band1'):
#     '''
#     The `gtsa` command line utilitiy will look for a function called `func` in gtsa.custom and pass the xarray DataArray to it.
#     You can use this function to do whatever you want with the DataArray. As an example, this function computes the nmad along the time axis.
#     '''

#     def nmad(array):
#         if np.all(~np.isfinite(array)):
#             return np.nan
#         else:
#             return 1.4826 * np.nanmedian(np.abs(array - np.nanmedian(array)))

#     result = xr.apply_ufunc(nmad,
#                             ds[variable_name],
#                             input_core_dims=[['time']],
#                             vectorize=True,
#                             dask='parallelized',
#                             output_dtypes=[float],
#                         )

#     # result = xr.apply_ufunc(
#     #     nmad,
#     #     ds[variable_name],
#     #     dask="allowed",
#     # )

#     return result
