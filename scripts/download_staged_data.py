#! /usr/bin/env python

import gtsa

gtsa.dataquery.download_hsfm_data(site             = 'rainier',
                                  output_directory = '../data/hsfm',
                                  overwrite        = True,
                                  verbose          = True)


gtsa.dataquery.download_earthdem_data(site             = 'rainier',
                                      output_directory = '../data/earthdem',
                                      overwrite        = True,
                                      verbose          = True)

# gtsa.dataquery.download_rgi_01_02(output_directory = '../data/rgi')

# gtsa.dataquery.download_wgms(output_directory = '../data/wgms')

# gtsa.dataquery.download_usgs_geodetic_data(output_directory = '../data/usgs_geodetic')