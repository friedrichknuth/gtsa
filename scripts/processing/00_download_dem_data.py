import gtsa

sites = ["mount-baker", "south-cascade"]
output_directory = "../../data"
product = "dem"
include_refdem = True
overwrite = True

for site in sites:
    gtsa.dataquery.download_historical_data(
        site=site,
        product=product,
        output_directory=output_directory,
        include_refdem=include_refdem,
        overwrite=overwrite,
    )

print("DONE")
