#! /usr/bin/env python


import argparse
from pathlib import Path
import gtsa

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="script to download staged data")
    
    # SITE
    help_str = '''study site | str | 
    rainier, 
    baker, 
    helens, 
    glacierpeak, 
    tetons, 
    scg, 
    gnp | 
    (default is all)
    '''
    parser.add_argument(
        "-site",
        dest="site",
        type=str,
        default='all',
        help=help_str
    )
    
    #HISTORICALS
    help_str = '''
    if set, download HSfM data for site(s)
    '''
    parser.add_argument(
        "-hsfm",
        dest="hsfm",
        action="store_true", 
        help=help_str
    )
    
    #EARTHDEM
    help_str = '''
    if set, download EarthDEM data for site(s)
    '''
    parser.add_argument(
        "-earthdem",
        dest="earthdem",
        action="store_true", 
        help=help_str
    )
    
    #RGI
    help_str = '''
    if set, download RGI glacier polygon data
    '''
    parser.add_argument(
        "-rgi",
        dest="rgi",
        action="store_true", 
        help=help_str
    )
    #RGI region
    help_str = '''download RGI region 1 and/or 2. flag -rgi must be set to initiate download | 
    int | 
    1 or 2 | 
    (default is both)
    '''
    parser.add_argument(
        "-rgi_region",
        dest="region",
        type=str,
        default='both',
        help=help_str
    )
    
    #USGS
    help_str = '''
    if set, download USGS geodetic benchmark glacier data
    '''
    parser.add_argument(
        "-usgs",
        dest="usgs",
        action="store_true", 
        help=help_str
    )
    
    #WGMS
    help_str = '''
    if set, download WGMS data.
    '''
    parser.add_argument(
        "-wgms",
        dest="wgms",
        action="store_true", 
        help=help_str
    )
    
    #output directory
    help_str = '''output directory path | path | 
    (default is ../data)
    '''
    parser.add_argument(
        "-outdir",
        dest="outdir",
        type=str,
        default='../data',
        help=help_str
    )
    
    #overwrite
    help_str = '''
    if set, will overwrite previously downloaded data
    '''
    parser.add_argument(
        "-overwrite", 
        dest="overwrite", 
        action="store_true", 
        help=help_str
    )
    
    args = parser.parse_args()
    
    if args.hsfm:
        if args.site in ['rainier', 'baker', 'helens', 'glacierpeak', 'tetons', 'scg', 'gnp']:
            gtsa.dataquery.download_hsfm_data(site             = args.site,
                                              output_directory = Path(args.outdir, 'hsfm'),
                                              overwrite        = args.overwrite,
                                              verbose          = True)
        else:
            print('No HSfM data staged for', args.site)
            
    if args.earthdem:
        if args.site in ['rainier', 'baker', 'glacierpeak', 'olympics', 'scg']:
            gtsa.dataquery.download_earthdem_data(site             = args.site,
                                                  output_directory = Path(args.outdir, 'earthdem'),
                                                  overwrite        = args.overwrite,
                                                  verbose          = True)
        else:
            print('No EarthDEM data staged for', args.site)

    if args.rgi:
        gtsa.dataquery.download_rgi_01_02(output_directory = Path(args.outdir, 'rgi'),
                                          region           = args.rgi_region,
                                          overwrite        = args.overwrite,
                                          verbose          = True)

    if args.wgms:
        gtsa.dataquery.download_wgms(output_directory = Path(args.outdir, 'wgms'),
                                     overwrite        = args.overwrite,
                                     verbose          = True)

    if args.usgs:
        gtsa.dataquery.download_usgs_geodetic_data(output_directory = Path(args.outdir, 
                                                                           'usgs_geodetic'),
                                                   overwrite        = args.overwrite,
                                                   verbose          = True)