import click
from pathlib import Path
import shutil
import psutil
import pandas as pd

import gtsa


@click.command(
    help="Stack single-band GeoTIFFs for memory-efficient data retrieval and processing. Both spatial (*.nc) and temporal (.zarr) stacks are created. All input raster grids are reprojected to the reference raster grid. If no --reference_tif is specified, the last in time is selected.  "
)
@click.option(
    "-dd",
    "--datadir",
    prompt=True,
    default="data",
    help="Path to directory containing GeoTIFFs. GeoTIFFs must be single-band. Default is 'data'.",
)
@click.option(
    "-ref",
    "--reference_tif",
    default=None,
    help="Reference GeoTIFF used as template grid to perform stacking. If None, temporally last GeoTIFF in datadir is used.",
)
@click.option(
    "-od",
    "--outdir",
    prompt=True,
    default="data/dems/south-cascade",
    help="Output directory path. Default is 'data/dems/south-cascade'.",
)
@click.option(
    "-dsf",
    "--date_string_format",
    prompt=True,
    default="%Y%m%d",
    help="Format of string pattern in GeoTIFF and reference GeoTIFF file names used to parse time stamps. Default is '%Y%m%d'.",
)
@click.option(
    "-dsp",
    "--date_string_pattern",
    prompt=True,
    default="_........_",
    help="Wildcard date string pattern in GeoTIFF and reference GeoTIFF file names. Periods are wildcards. Length of prefix and suffix before wildcard sequence must be equal. Default is '_........_'.",
)
@click.option(
    "-dspo",
    "--date_string_pattern_offset",
    prompt=True,
    default=1,
    help="Character length of prefix and suffix before wildcard sequence in date_string_pattern. Length of prefix and suffix must be equal. Default is 1.",
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
    "-cl",
    "--cleanup",
    is_flag=True,
    default=False,
    help="Set to remove temporary files.",
)
@click.option(
    "-si",
    "--silent",
    is_flag=True,
    default=False,
    help="Set to silence stdout.",
)
def main(
    datadir,
    outdir,
    reference_tif,
    date_string_format,
    date_string_pattern,
    date_string_pattern_offset,
    workers,
    dask_enabled,
    ip_address,
    port,
    overwrite,
    cleanup,
    silent,
):
    verbose = not silent

    if not workers:
        workers = psutil.cpu_count(logical=True) - 1

    if dask_enabled:
        client = gtsa.io.dask_start_cluster(
            workers,
            ip_address=ip_address,
            port=port,
            verbose=verbose,
        )

    files = [x.as_posix() for x in sorted(Path(datadir).glob("*.tif"))]

    date_strings = [
        x[date_string_pattern_offset:-date_string_pattern_offset]
        for x in gtsa.io.parse_timestamps(
            files, date_string_pattern=date_string_pattern
        )
    ]

    # ensure chronological sorting
    date_strings, files = list(zip(*sorted(zip(date_strings, files))))
    date_times = [pd.to_datetime(x, format=date_string_format) for x in date_strings]

    if not reference_tif:
        reference_tif = files[-1]
        if verbose:
            print(
                'Using most recent GeoTIFF as reference grid: "{}"'.format(
                    reference_tif
                )
            )

    ds = gtsa.io.xr_stack_geotifs(
        files,
        date_times,
        reference_tif,
        resampling="cubic",
        save_to_nc=True,
        nc_out_dir=Path(outdir, "spatial").as_posix(),
        overwrite=overwrite,
        verbose=verbose,
    )

    if ds:
        ds_zarr = gtsa.io.create_zarr_stack(
            ds,
            output_directory=Path(outdir, "temporal").as_posix(),
            variable_name="band1",
            zarr_stack_file_name="stack.zarr",
            overwrite=overwrite,
            verbose=verbose,
            cleanup=cleanup,
        )

        if cleanup:
            if verbose:
                print("Removing spatially stacked NetCDF files")
            shutil.rmtree(Path(outdir, "spatial").as_posix(), ignore_errors=True)

    if verbose:
        print("DONE")

    return


if __name__ == "__main__":
    main()
