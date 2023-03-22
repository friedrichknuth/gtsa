import gtsa
from bs4 import BeautifulSoup
from pathlib import Path
import requests
import shutil
import gdown

def download_rgi_01_02(output_directory = '../data/rgi',
                       verbose          = True):
    
    '''
    Downloads GeoJSON files for RGI regions 01 and 02.
    
    Data originally downloaded from http://www.glims.org/RGI/rgi60_files/00_rgi60.zip
    Staged on Google Drive
    Shapefiles for RGI 01 and 02 converted to GeoJSON
    
    Returns
    (path/to/01_rgi60_Alaska.geojson' , path/to/02_rgi60_WesternCanadaUS.geojson)
    '''
    print('Downloading GeoJSON files for RGI regions 01 and 02 to', output_directory)

    rgi01_gdrive_id = '1fRjxyOcZYtTM95xGf6kgdnF4rDFp_lA3'
    rgi01_fn        = '01_rgi60_Alaska.geojson'
    rgi02_gdrive_id = '18B0derwIUetJy1v5dBJaO-tTKFqqEV_u'
    rgi02_fn        = '02_rgi60_WesternCanadaUS.geojson'

    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    print('Downloading', rgi01_fn)
    rgi01_output = Path(output_directory, rgi01_fn)
    gdown.download(id=rgi01_gdrive_id, output=str(rgi01_output), quiet=~verbose)
    
    print('Downloading', rgi02_fn)
    rgi02_output = Path(output_directory, rgi02_fn)
    gdown.download(id=rgi02_gdrive_id, output=str(rgi02_output), quiet=~verbose)
    
    return rgi01_output, rgi02_output
    

def download_wgms(output_directory = '../data/wgms',
                  verbose          = True):
    '''
    Downloads 2022-09 version of WGMS csv from https://wgms.ch/data_databaseversions/
    '''
    
    url = 'http://wgms.ch/downloads/DOI-WGMS-FoG-2022-09.zip'
    out = Path(output_directory,url.split('/')[-1])

    Path(output_directory).mkdir(parents=True, exist_ok=True)

    call = ['wget', '-O', str(out), url]
    gtsa.io.run_command(call,verbose=True)

    call = ['unzip', str(out), '-d', output_directory]
    gtsa.io.run_command(call,verbose=verbose)
    
def download_earthdem_data(site             = 'all',
                           output_directory = '../data/earthdem',
                           overwrite        = True,
                           verbose          = True):
    '''
    Downloads staged EarthDEM data.
    
    site             : str  : must be valid side_id or 'all'
    output_directory : str  : output path
    overwrite        : bool : overwrite existing folder for site in outpute_directory
    verbose          : bool : print stdout and stderror
    '''
    site_ids = {'rainier'      : '1AmuCpZEM3Pz11coF3nCO1C4rVnwyEl53',
                'baker'        : '1wbtM1wX_lEvWq--hGS8FPQlxHmU6JI6-',
                'glacierpeak'  : '1HaY8gDDHA646pyVOYa_QjaRM99uhOhPz',
                'olympics'     : '1MhM9qTqtd7cZ7MiR_B8Kcgp7AE1hu59_',
                'scg'          : '1enen-oFOXZLrNHu65j_jRvqtKhnZAujX'
    }
    # make the output directory
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    # download site only, if specified 
    if not site == 'all':
        try:
            print('Downloading EarthDEM', site)
            ID = site_ids[site]
            out = Path(output_directory,site)
            if out.exists() and overwrite == False:
                print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
            else:
                call = ['gdown', ID]
                gtsa.io.run_command(call,verbose=verbose)

                if Path(site+'.tar.gz').exists():

                    call = ['tar', 'zxvf', site+'.tar.gz']
                    gtsa.io.run_command(call,verbose=verbose)

                    shutil.rmtree(out, ignore_errors=True)
                    print('Moving to', str(out.resolve()))
                    Path(site).rename(out)

                    print('Deleting',site+'.tar.gz')
                    Path(site+'.tar.gz').unlink(missing_ok=True)
        except:
            print('Download for', site, 'failed')
            print('Ensure it is one of', site_ids.keys())
            print('If receiving "Access denied" error try again later or use direct link in browser')
            pass
    
    # download all sites
    else:
        for site in site_ids.keys():
            try:
                print('Downloading EarthDEM', site)
                ID = site_ids[site]
                out = Path(output_directory,site)
                if out.exists() and overwrite == False:
                    print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
                else:
                    call = ['gdown', ID]
                    gtsa.io.run_command(call,verbose=verbose)

                    if Path(site+'.tar.gz').exists():
                        call = ['tar', 'zxvf', site+'.tar.gz']
                        gtsa.io.run_command(call,verbose=verbose)

                        shutil.rmtree(out, ignore_errors=True)
                        print('Moving to', str(out.resolve()))
                        Path(site).rename(out)

                        print('Deleting',site+'.tar.gz')
                        Path(site+'.tar.gz').unlink(missing_ok=True)
            except:
                print('If receiving "Access denied" error try again later or use direct link in browser')
                pass
    print('DONE')
    

def download_hsfm_data(site             = 'all',
                       output_directory = '../data/hsfm',
                       overwrite        = True,
                       verbose          = True):
    '''
    Downloads staged HSfM data.
    
    site             : str  : must be valid side_id or 'all'
    output_directory : str  : output path
    overwrite        : bool : overwrite existing folder for site in outpute_directory
    verbose          : bool : print stdout and stderror
    '''
    site_ids = {'rainier'      : '1W1Bemlqbd8pKoNaI2yunjgqfSqg9MXrz',
                'baker'        : '1IyZkinKoshxWW036wGAsKxdLCk05tWti',
                'helens'       : '1jr4GETIdVzMxEEWeRN0dvxvCIdHZbrVQ',
                'glacierpeak'  : '1qvDgA1IH9Y7p8WWjnANc0HgccgrVyB_t',
                'tetons'       : '1CKQxGHV2hnB4_s4k685kmQYR4GF0VlLk',
                'scg'          : '1CAmBSj1tq_Xjl9VSkeVeGZ_taZZ8Kh_D',
                'gnp'          : '1-Upe30BWPnJtbDU7xrtH3ltYC7VuVEUt',
    }
    # make the output directory
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    # download site only, if specified 
    if not site == 'all':
        try:
            print('Downloading HSfM', site)
            ID = site_ids[site]
            out = Path(output_directory,site)
            if out.exists() and overwrite == False:
                print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
            else:
                call = ['gdown', ID]
                gtsa.io.run_command(call,verbose=verbose)

                if Path(site+'.tar.gz').exists():

                    call = ['tar', 'zxvf', site+'.tar.gz']
                    gtsa.io.run_command(call,verbose=verbose)

                    shutil.rmtree(out, ignore_errors=True)
                    print('Moving to', str(out.resolve()))
                    Path(site).rename(out)

                    print('Deleting',site+'.tar.gz')
                    Path(site+'.tar.gz').unlink(missing_ok=True)
        except:
            print('Download for', site, 'failed')
            print('Ensure it is one of', site_ids.keys())
            print('If receiving "Access denied" error try again later or use direct link in browser')
            pass
    
    # download all sites
    else:
        for site in site_ids.keys():
            try:
                print('Downloading HSfM', site)
                ID = site_ids[site]
                out = Path(output_directory,site)
                if out.exists() and overwrite == False:
                    print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
                else:
                    call = ['gdown', ID]
                    gtsa.io.run_command(call,verbose=verbose)

                    if Path(site+'.tar.gz').exists():
                        call = ['tar', 'zxvf', site+'.tar.gz']
                        gtsa.io.run_command(call,verbose=verbose)

                        shutil.rmtree(out, ignore_errors=True)
                        print('Moving to', str(out.resolve()))
                        Path(site).rename(out)

                        print('Deleting',site+'.tar.gz')
                        Path(site+'.tar.gz').unlink(missing_ok=True)
            except:
                print('If receiving "Access denied" error try again later or use direct link in browser')
                pass
    print('DONE')
    
    
def download_usgs_geodetic_data(output_directory = '../data/usgs_geodetic',
                                overwrite        = True,
                                verbose          = True):
    '''
    Downloads USGS geodetic data for Benchmark glaciers.
    Source: https://alaska.usgs.gov/products/data/glaciers/benchmark_geodetic.php
    
    output_directory : str  : output path
    overwrite        : bool : overwrite existing folder for site in outpute_directory
    verbose          : bool : print stdout and stderror
    '''
    print('Downloading data from https://alaska.usgs.gov/products/data/glaciers/benchmark_geodetic.php')
    
    # make the output directory
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    # retrieve file urls
    url = 'https://alaska.usgs.gov/products/data/glaciers/benchmark_geodetic.php'
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'html.parser')

    # request data
    for link in soup.find_all('a'):
        url = link.get('href')
        if 'DEM' in url or 'Ortho' in url:
            print('Downloading', url)
            r = requests.get(url)
            out = Path(output_directory,url.split('/')[-1])
            if out.exists() and overwrite == False:
                print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
            else:
                print('Writing to', str(out.resolve()))
                open(out, 'wb').write(r.content)

        