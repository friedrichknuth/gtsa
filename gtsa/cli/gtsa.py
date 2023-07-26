import click
from pathlib import Path
import shutil
import psutil
import pandas as pd
import numpy as np
import xarray as xr
import rasterio
import dask

import gtsa

VALID_COMPUTATIONS = [
    "count",
    "mean",
    "std",
    "min",
    "max",
    "median",
    "sum",
    "nmad",
    "polyfit",
]


def check_computations(compute):
    if compute in VALID_COMPUTATIONS:
        return compute
    else:
        print(f"Invalid compute command {compute}. Skipping.")
        return


@click.command(
    help="Stack single-band GeoTIFFs as Zarr file for memory-efficient data retrieval and processing."
)
@click.option(
    "-if",
    "--input_file",
    prompt=True,
    default="data/stack.zarr",
    help="Path to Zarr file. Default is 'data/stack.zarr'.",
)
@click.option(
    "-vn",
    "--variable_name",
    default="band1",
    help="Variable name. Default is 'band1'.",
)
@click.option(
    "-c",
    "--compute",
    multiple=True,
    default=["count"],
    type=click.Choice(VALID_COMPUTATIONS),
    help=f"Which computation to perform. Valid options are {VALID_COMPUTATIONS}. Default is 'count'.",
)
@click.option(
    "-deg",
    "--degree",
    multiple=True,
    type=int,
    help="Degree for polynomial fit. Provide after specifying '--compute polyfit'.",
)
@click.option(
    "-f",
    "--frequency",
    multiple=True,
    default=["1Y"],
    help="Frequency for model fitting. E.g. datetimes are converted to decimal year floats is '1Y'. Default is '1Y'.",
)
@click.option(
    "-od",
    "--outdir",
    default="data/outputs",
    help="Output directory path. Default is 'data/outputs'.",
)
@click.option(
    "-mw",
    "--workers",
    default=None,
    type=int,
    help="Number of cores. Default is logical cores -1.",
)
@click.option(
    "-de",
    "--dask_enabled",
    is_flag=True,
    default=False,
    help="Set to use dask.",
)
@click.option(
    "-ip",
    "--ip_address",
    default=None,
    help="IP address for dask dashboard. Default is local host.",
)
@click.option(
    "-p",
    "--port",
    default="8787",
    help="Port for dask dashboard. Default is 8787.",
)
@click.option(
    "-ow",
    "--overwrite",
    is_flag=True,
    default=False,
    help="Set to overwrite.",
)
@click.option(
    "-si",
    "--silent",
    is_flag=True,
    default=False,
    help="Set to silence stdout.",
)
@click.option(
    "-tr",
    "--test_run",
    is_flag=True,
    default=False,
    help="Set for testing. Extracts 500x500 window from center of stack.",
)
def main(
    input_file,
    variable_name,
    compute,
    degree,
    frequency,
    outdir,
    workers,
    dask_enabled,
    ip_address,
    port,
    overwrite,
    silent,
    test_run,
):
    verbose = not silent

    if degree:
        degree = list(degree)
        polyfits = [i for i in compute if i == "polyfit"]
        if len(degree) != len(polyfits):
            raise ValueError("Must provide --degree after each '--compute polyfit'.")

    if not workers:
        workers = psutil.cpu_count(logical=True) - 1

    if dask_enabled:
        client = gtsa.io.dask_start_cluster(
            workers,
            ip_address=ip_address,
            port=port,
            verbose=verbose,
        )

    ds = xr.open_dataset(input_file, chunks="auto", engine="zarr")

    # optimize chunks and reload lazily
    tc, yc, xc = gtsa.io.determine_optimal_chuck_size(ds, verbose=verbose)
    ds = xr.open_dataset(
        input_file, chunks={"time": tc, "y": yc, "x": xc}, engine="zarr"
    )

    # check frequency and convert time to numeric
    for i in frequency:
        if i == "1Y":
            times = [pd.to_datetime(x) for x in ds[variable_name].time.values]
            decyear_times = np.array(
                [gtsa.utils.date_time_to_decyear(x) for x in times]
            )
            ds["time"] = decyear_times
        else:
            raise ValueError(
                f"Only {i} supported as frequency option. Skipping timestamp conversion."
            )

    # # assign crs back
    # TODO add option to pass bounds or shapefile and clip
    # crs = rasterio.crs.CRS.from_epsg(32610)
    # ds = ds.rio.write_crs(crs)
    if test_run:
        ds = gtsa.geospatial.extract_dataset_center_window(ds, size=500)

    output_directory = Path(outdir)
    output_directory.mkdir(parents=True, exist_ok=True)

    # TODO enable custom scratch space with dask.config.set({'temporary_directory': 'path/to/dir'})
    with dask.config.set(
        {"distributed.scheduler.worker-ttl": None}
    ):  # disable heartbeat check
        CORE_MODULES = ["count", "mean", "std", "min", "max", "median", "sum"]
        computations = []
        degree_tmp = degree.copy()  # will need these again later
        for c in compute:
            if c in CORE_MODULES:
                m = getattr(ds[variable_name], c)
                result = m(axis=0)
                result.name = c
                computations.append(result)
            if c == "nmad":
                result = gtsa.temporal.dask_nmad(ds[variable_name])
                result.name = c
                computations.append(result)
            if c == "polyfit":
                min_count = 3  # TODO maybe parameterize
                # min_time_lag = 1Y # TODO add parameter for minimum time between first and last datapoint in time series
                # specified -frequency option might be a good default option for min_time_lag
                if verbose:
                    print(f"Computing count")
                    
                ds["count"] = (
                    ds[variable_name]
                    .count(axis=0)
                    .chunk("auto", balance=True)
                    .compute()
                )
                print(f"Excluding time series with count < {min_count}.")
                result = ds.where(ds["count"] > min_count)[variable_name].polyfit(
                    dim="time", deg=degree_tmp.pop(0)
                )
                computations.append(result)

        for i, result in enumerate(computations):
            if isinstance(result, type(xr.Dataset())):
                if "polyfit_coefficients" in list(result.data_vars):
                    c = "polyfit_deg" + str(degree.pop(0))
            elif isinstance(result, type(xr.DataArray())):
                c = result.name

            output_file = Path(output_directory, c + ".zarr")

            result = result.chunk("auto", balance=True)
            if overwrite:
                shutil.rmtree(output_file, ignore_errors=True)
            if overwrite or not output_file.exists():
                if verbose:
                    print("Computing", c)
                result.to_zarr(output_file)
                if verbose:
                    print("Saved", output_file)
            elif verbose:
                print(f"File already exists. {output_file}")
                print("Overwrite set to False. Skipping.")
    # TODO add some default plotting options
    return


if __name__ == "__main__":
    main()
