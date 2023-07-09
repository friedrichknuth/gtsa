import gtsa

sites = ['mount-baker', 'south-cascade']
output_directory = 'test_data'
include_refdem = True
overwrite = True

for site in sites:
    gtsa.dataquery.download_hi_res_test_data(site = site,
                                             output_directory = output_directory,
                                             include_refdem = include_refdem,
                                             overwrite = overwrite,
                                            )
    
print('DONE')
    
    