import click
import gtsa


@click.command(
    help="Downloads historical orthoimage and digital elevation model data from https://doi.org/10.5281/zenodo.7297154"
)
@click.option(
    "-s",
    "--site",
    prompt=True,
    default="south-cascade",
    help="Use 'mount-baker' or 'south-cascade' (without quotes).",
)
@click.option(
    "-od",
    "--outdir",
    prompt=True,
    default="data",
    help="Your desired output directory path.",
)
@click.option(
    "-pr",
    "--product",
    prompt=True,
    default="dem",
    help="Use 'dem' or 'ortho' (without quotes).",
)
@click.option(
    "-ref",
    "--include_refdem",
    is_flag=True,
    default=False,
    help="Set to download reference DEM for site.",
)
@click.option(
    "-mw",
    "--workers",
    default=None,
    type=int,
    help="Number of workers (cores) to be used.",
)
@click.option(
    "-ow",
    "--overwrite",
    is_flag=True,
    default=False,
    help="Set to overwrite existing outputs.",
)
@click.option(
    "-si",
    "--silent",
    is_flag=True,
    default=True,
    help="Set to silence information printed to stdout.",
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
