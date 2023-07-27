import click
from pathlib import Path
import psutil
import gtsa


@click.command(
    help="Create Cloud Optimized GeoTIFFs (COGs) in EPSG:4326 for visualization with Folium and TiTiler."
)
@click.option(
    "-dd",
    "--datadir",
    prompt=True,
    default="data/orthos/south-cascade",
    help="Path to directory containing single-band 8-bit GeoTIFFs. Default is 'data/orthos/south-cascade'.",
)
@click.option(
    "-od",
    "--outdir",
    prompt=True,
    default="data/orthos/south-cascade/cogs",
    help="Output directory path. Default is 'data/orthos/south-cascade/cogs'.",
)
@click.option(
    "-mw",
    "--workers",
    default=None,
    type=int,
    help="Number of cores. Default is logical cores -1.",
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
def main(
    datadir,
    outdir,
    workers,
    silent,
    overwrite,
):
    verbose = not silent

    if not workers:
        workers = psutil.cpu_count(logical=True) - 1
    files = [x for x in sorted(Path(datadir).glob("*.tif"))]

    out = gtsa.utils.create_cogs(
        files,
        output_directory=outdir,
        crs="EPSG:4326",  # currently required for visualization with folium and titiler
        overwrite=overwrite,
        workers=workers,
        verbose=verbose,
    )
    print("DONE")


if __name__ == "__main__":
    main()
