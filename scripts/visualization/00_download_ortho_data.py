import gtsa

sites = ['mount-baker', 'south-cascade']
output_directory = '../../data'
product = 'ortho'
overwrite = False

for site in sites:
    gtsa.dataquery.download_historical_data(site = site,
                                             product = product,
                                             output_directory = output_directory,
                                             overwrite = overwrite,
                                            )