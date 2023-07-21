import click
import gtsa

@click.command()
@click.option(
    "--site",
    prompt=True,
    default="south-cascade",
    help="'mount-baker' or 'south-cascade'",
)

@click.option(
    "--outdir",
    prompt=True,
    default="data",
    help="output directory",
)

@click.option(
    "--product",
    prompt=True,
    default="dem",
    help="'dem' or 'ortho'",
)

@click.option(
    "--include_refdem",
    is_flag=True, 
    default=False, 
    help="Set to download reference DEM for site"
)

@click.option(
    "--max_workers", 
    default=None, 
    help="Set to integer matching cores to be used"
)

@click.option(
    "--silent", 
    is_flag=True, 
    default=True, 
    help="Set to silence printed information"
)

@click.option(
    "--overwrite", 
    is_flag=True, 
    default=False, 
    help="Set to overwrite existing outputs"
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