import click
import gtsa

@click.command(
    help='Downloads historical orthoimage and digital elevation model data from https://doi.org/10.5281/zenodo.7297154'
)

@click.option(
    "--site",
    prompt=True,
    default="south-cascade",
    help="Use 'mount-baker' or 'south-cascade' (without quotes).",
)

@click.option(
    "--outdir",
    prompt=True,
    default="data",
    help="Your desired output directory path.",
)

@click.option(
    "--product",
    prompt=True,
    default="dem",
    help="Use 'dem' or 'ortho' (without quotes).",
)

@click.option(
    "--include_refdem",
    is_flag=True, 
    default=False, 
    help="Set to download reference DEM for site."
)

@click.option(
    "--max_workers", 
    default=None, 
    help="Set to integer matching cores to be used."
)

@click.option(
    "--silent", 
    is_flag=True, 
    default=True, 
    help="Set to silence information printed to stdout."
)

@click.option(
    "--overwrite", 
    is_flag=True, 
    default=False, 
    help="Set to overwrite existing outputs."
)

def main(
    site,
    outdir,
    product,
    include_refdem,
    max_workers,
    silent,
    overwrite,
):
    gtsa.dataquery.download_historical_data(
        site=site,
        product=product,
        output_directory=outdir,
        include_refdem=include_refdem,
        overwrite=overwrite,
        max_workers = max_workers,
        verbose=silent,
    )
    
    print("DONE")

if __name__ == "__main__":
    main()