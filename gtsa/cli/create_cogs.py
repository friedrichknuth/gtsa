import click
from pathlib import Path
import gtsa


@click.command(
    help="Create cloud optimized GeoTIFFs (COGs) for visualization with Folium and TiTiler."
)
@click.option(
    "--datadir",
    prompt=True,
    default="data",
    help="Path to directory containing GeoTIFFs.",
)
@click.option(
    "--outdir",
    prompt=True,
    default=None,
    help="Your desired output directory path.",
)
@click.option(
    "--max_workers", default=None, help="Set to integer matching cores to be used."
)
@click.option(
    "--silent",
    is_flag=True,
    default=True,
    help="Set to silence information printed to stdout.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Set to overwrite existing outputs.",
)
def main(
    datadir,
    outdir,
    max_workers,
    silent,
    overwrite,
):
    files = [x for x in sorted(Path(data_dir).glob("*.tif"))]

    if not outdir:
        outdir = Path(data_dir, "cogs")

    out = gtsa.utils.create_cogs(
        files,
        output_directory=outdir,
        crs="EPSG:4326",  # required for visualization with folium and titiler
        overwrite=overwrite,
        max_workers=max_workers,
        verbose=silent,
    )
    print("DONE")


if __name__ == "__main__":
    main()


# data_dirs = ["../../data/orthos/south-cascade", "../../data/orthos/mount-baker"]

# ortho_cogs = []

# for data_dir in data_dirs:
#     files = [x for x in sorted(Path(data_dir).glob("*.tif"))]
#     output_directory = Path(data_dir, "cogs")

#     out = gtsa.utils.create_cogs(
#         files,
#         output_directory=output_directory,
#         crs="EPSG:4326",  # required for visualization with folium and titiler
#         overwrite=False,
#         max_workers=None,
#         verbose=True,
#     )

#     ortho_cogs.append(out)

# print("DONE")
