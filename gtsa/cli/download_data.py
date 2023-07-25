import click
import gtsa

VALID_SITES = ["south-cascade", "mount-baker"]
VALID_PRODUCTS = ["dem", "ortho"]


@click.command(
    help="Downloads historical orthoimage and digital elevation model data from https://doi.org/10.5281/zenodo.7297154"
)
@click.option(
    "-s",
    "--site",
    prompt=True,
    type=click.Choice(VALID_SITES),
    default="south-cascade",
    help="Which site to download data for. Valid options are {VALID_SITES}. Default is 'south-cascade'.",
)
@click.option(
    "-od",
    "--outdir",
    prompt=True,
    default="data",
    help="Output directory path. Default is 'data'.",
)
@click.option(
    "-pr",
    "--product",
    prompt=True,
    type=click.Choice(VALID_PRODUCTS),
    default="dem",
    help="Which product to download. Valid options are {VALID_PRODUCTS}. Default is 'dem'.",
)
@click.option(
    "-ref",
    "--include_refdem",
    is_flag=True,
    default=True,
    help="Set to download reference DEM for site. Default is False.",
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
    help="Set to overwrite. Default is False.",
)
@click.option(
    "-si",
    "--silent",
    is_flag=True,
    default=True,
    help="Set to silence stdout. Default is False.",
)
def main(
    site,
    outdir,
    product,
    include_refdem,
    workers,
    overwrite,
    silent,
):
    verbose = not silent
    if not workers:
        workers = psutil.cpu_count(logical=True) - 1
    gtsa.dataquery.download_historical_data(
        site=site,
        product=product,
        output_directory=outdir,
        include_refdem=include_refdem,
        overwrite=overwrite,
        workers=workers,
        verbose=verbose,
    )

    if verbose:
        print("DONE")


if __name__ == "__main__":
    main()
