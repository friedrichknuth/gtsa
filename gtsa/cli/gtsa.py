import click
from pathlib import Path
import shutil
import psutil
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
import dask
import warnings
import bokeh
import distributed

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
VALID_FREQUENCIES = ["1Y"]


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
    default="data/dems/south-cascade/temporal/stack.zarr",
    help="Path to Zarr file. Default is 'data/stack.zarr'.",
)
@click.option(
    "-vn",
    "--variable_name",
    default="band1",
    help="Variable name. Default is 'band1'.",
)
@click.option(
    "-od",
    "--outdir",
    default="outputs",
    help="Output directory path. Default is 'outputs'.",
)
@click.option(
    "-s",
    "--shape",
    default=None,
    help="Path to vector file containing geometry. Must specify --clip_shape and/or --clip_bounds. Default is None.",
)
@click.option(
    "-c2s",
    "--clip2shape",
    is_flag=True,
    default=False,
    help="Set to clip to input --shape geometry. Values outside geometry are set to NaN.",
)
@click.option(
    "-r2b",
    "--reduce2bounds",
    is_flag=True,
    default=False,
    help="Set to reduce to input --shape bounds. Values and coordinates outside bounds are removed. Recommended for large datasets.",
)
@click.option(
    "-ic",
    "--inverse_clip",
    is_flag=True,
    default=False,
    help="Set invert --clip_shape operation.",
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
    type=click.Choice(VALID_FREQUENCIES),
    help=f"Frequency for timestamp conversion and model fitting. E.g. if '1Y', datetimes are converted to decimal year floats. Valid options are {VALID_FREQUENCIES}. Default is '1Y'.",
)
@click.option(
    "-de",
    "--dask_enabled",
    is_flag=True,
    default=False,
    help="Set to use dask.",
)
@click.option(
    "-mw",
    "--workers",
    default=None,
    type=int,
    help="Number of cores. Default is logical cores -1.",
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
    "-sw",
    "--show_warnings",
    is_flag=True,
    default=False,
    help="Set to disable warning filters.",
)
@click.option(
    "-tr",
    "--test_run",
    is_flag=True,
    default=False,
    help="Set for testing. Extracts 265x256 column from center of stack.",
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
    show_warnings,
    test_run,
    shape,
    clip2shape,
    reduce2bounds,
    inverse_clip,
):
    verbose = not silent

    if not show_warnings:
        warnings.simplefilter("ignore", bokeh.util.warnings.BokehUserWarning)
        warnings.simplefilter("ignore", UserWarning)
        warnings.simplefilter("ignore", distributed.comm.core.CommClosedError)

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

    ds = xr.open_dataset(
        input_file, chunks={"time": -1, "y": "auto", "x": "auto"}, engine="zarr"
    )

    # this reduces memory usage, but it's slower than the above
    # tc, yc, xc = gtsa.io.determine_optimal_chuck_size(ds, verbose=verbose)
    # ds = xr.open_dataset(
    #     input_file, chunks={"time": tc, "y": yc, "x": xc}, engine="zarr"
    # )

    if not ds.rio.crs:
        try:
            ds.rio.write_crs(ds.attrs["crs"])
        except KeyError:
            if verbose:
                print(
                    "No crs found in Zarr dataset attributes. Recreate the Zarr stack by assigning with `ds.attrs['crs'] = CRS.to_wkt()`. Skipping."
                )
    else:
        ds = ds.rio.write_crs(ds.rio.crs)  # write crs to all bands

    if shape and ds.rio.crs:
        gdf = gpd.read_file(shape)
        gdf = gdf.to_crs(ds.rio.crs)
        xmin, ymin, xmax, ymax = gdf.total_bounds
        if not clip2shape and not reduce2bounds:
            if verbose:
                print("No clipping operation specified. Skipping.")
        else:
            if reduce2bounds:
                initial_bounds = ds.rio.bounds()
                ds = ds.rio.clip_box(xmin, ymin, xmax, ymax)
                reduced_bounds = ds.rio.bounds()
                if verbose:
                    print(f"Initial bounds: {initial_bounds}")
                    print(f"Reduced bounds: {reduced_bounds}")
            if clip2shape:
                ds = ds.rio.clip(
                    gdf["geometry"], invert=inverse_clip
                )  # clip to actual shape
                if verbose:
                    print(
                        f"Clipped to input --shape geometry. --inverse_clip set to {inverse_clip}."
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
                f"Only {VALID_FREQUENCIES} supported as frequency options for timestamp conversion and model fitting."
            )
    if test_run:
        ds = gtsa.geospatial.extract_dataset_center_window(
            ds, xdim="x", ydim="y", size=265
        )

    output_directory = Path(outdir)
    output_directory.mkdir(parents=True, exist_ok=True)

    # TODO enable custom scratch space with dask.config.set({'temporary_directory': 'path/to/dir'})

    # with dask.config.set(
    #     {"distributed.scheduler.worker-ttl": None}
    # ) and dask.config.set(
    #     {"distributed.comm.timeouts.tcp": "50s"}
    # ):  # trying disable irrelevant heartbeat check https://github.com/dask/distributed/issues/1674
    CORE_MODULES = ["count", "mean", "std", "min", "max", "median", "sum"]
    computations = []
    if degree:
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

            ds["count"] = ds[variable_name].count(axis=0).chunk("auto", balance=True)
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
    return


if __name__ == "__main__":
    main()
