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
    help="Output HTML file name. Default is 'map.html'.",
)
@click.option(
    "-z",
    "--zoom_start",
    prompt=False,
    default=11,
    help="Zoom start for map. Default is 11.",
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
def main(pipeline, output_file, zoom_start, silent, overwrite):
    verbose = not silent

    with open(pipeline) as json_file:
        payload = json.load(json_file)

    m = gtsa.plotting.plot_cogs_sites(
        payload,
        zoom_start=zoom_start,
        verbose=verbose,
    )
    if not Path(output_file).exists() or overwrite:
        m.save(output_file)
        if verbose:
            print("map saved to", output_file)
    elif Path(output_file).exists() and not overwrite:
        print(f"{output_file} exists. Set --overwrite to overwrite.")
    return


if __name__ == "__main__":
    main()
