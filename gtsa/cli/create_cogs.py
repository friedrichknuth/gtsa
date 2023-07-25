import click
from pathlib import Path
import gtsa


@click.command(
    help="Create Cloud Optimized GeoTIFFs (COGs) in EPSG:4326 for visualization with Folium and TiTiler."
)
@click.option(
    "-dd",
    "--datadir",
    prompt=True,
    default="data",
    help="Path to directory containing GeoTIFFs.",
)
@click.option(
    "-od",
    "--outdir",
    prompt=True,
    default="data/cogs",
    help="Output directory path.",
)
@click.option(
    "-mw",
    "--workers",
    default=None,
    help="Set to integer matching cores to be used.",
)
@click.option(
    "-si",
    "--silent",
    is_flag=True,
    default=True,
    help="Set to silence stdout. Default is False.",
)
@click.option(
    "-ow",
    "--overwrite",
    is_flag=True,
    default=False,
    help="Set to overwrite. Default is False.",
)
def main(
    datadir,
    outdir,
    workers,
    silent,
    overwrite,
):
    files = [x for x in sorted(Path(datadir).glob("*.tif"))]

    out = gtsa.utils.create_cogs(
        files,
        output_directory=outdir,
        crs="EPSG:4326",  # currently required for visualization with folium and titiler
        overwrite=overwrite,
        workers=workers,
        verbose=silent,
    )
    print("DONE")


if __name__ == "__main__":
    main()
