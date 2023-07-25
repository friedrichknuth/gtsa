import click
import json
from pathlib import Path
import gtsa


@click.command(
    help="Create Folium map from remotely stored Cloud Optimized GeoTIFFs (COGs)."
)
@click.option(
    "-p",
    "--pipeline",
    prompt=True,
    default="notebooks/visualization/pipeline.json",
    help="Path to JSON file specifying inputs. See example under notebooks/visualization/pipeline.json.",
)
@click.option(
    "-of",
    "--output_file",
    default="map.html",
    help="Output HTML file name.",
)
@click.option(
    "-z",
    "--zoom_start",
    prompt=False,
    default=11,
    help="Zoom start for map",
)
@click.option(
    "-si",
    "--silent",
    is_flag=True,
    default=False,
    help="Set to silence stdout. Default is False.",
)
def main(pipeline, output_file, zoom_start, silent):
    verbose = not silent

    with open(pipeline) as json_file:
        payload = json.load(json_file)

    m = gtsa.plotting.plot_cogs_sites(
        payload,
        zoom_start=zoom_start,
        verbose=verbose,
    )
    m.save(output_file)
    if verbose:
        print("map saved to", output_file)

    return


if __name__ == "__main__":
    main()
