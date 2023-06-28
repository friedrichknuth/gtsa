import gtsa
from bs4 import BeautifulSoup
from pathlib import Path
import requests
import shutil
import psutil
from tqdm import tqdm
import concurrent
import gdown

def download_rgi_01_02(output_directory = '../data/rgi',
                       region           = 'all',
                       overwrite        = True,
                       verbose          = True):
    
    '''
    Downloads GeoJSON files for RGI regions 01 and 02.
    
    Data originally downloaded from http://www.glims.org/RGI/rgi60_files/00_rgi60.zip
    Staged on Google Drive
    Shapefiles for RGI 01 and 02 converted to GeoJSON
    
    Input
    output_directory : path : location to save data
    region           : int  : either "1" or "2" for RGI 01 or RGI 02
    
    Returns
    (path/to/01_rgi60_Alaska.geojson' , path/to/02_rgi60_WesternCanadaUS.geojson)
    '''
    print('Downloading GeoJSON files for RGI regions 01 and 02 to', output_directory)

    rgi01_gdrive_id = '1fRjxyOcZYtTM95xGf6kgdnF4rDFp_lA3'
    rgi01_fn        = '01_rgi60_Alaska.geojson'
    rgi02_gdrive_id = '18B0derwIUetJy1v5dBJaO-tTKFqqEV_u'
    rgi02_fn        = '02_rgi60_WesternCanadaUS.geojson'

    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    if region == 1:
        rgi01_output = Path(output_directory, rgi01_fn)
        if rgi01_output.exists() and overwrite == False:
            print(rgi01_output.resolve(), 'already exists and overwrite option set to False. Skipping download.')
        else:
            print('Downloading', rgi01_fn)
            gdown.download(id=rgi01_gdrive_id, output=str(rgi01_output), quiet=~verbose)
        return rgi01_output
    
    elif region == 2:
        rgi02_output = Path(output_directory, rgi02_fn)
        if rgi02_output.exists() and overwrite == False:
            print(rgi02_output.resolve(), 'already exists and overwrite option set to False. Skipping download.')
        else:
            print('Downloading', rgi02_fn)
            gdown.download(id=rgi02_gdrive_id, output=str(rgi02_output), quiet=~verbose)
        return rgi02_output
        
    elif region == 'all':
        rgi01_output = Path(output_directory, rgi01_fn)
        if rgi01_output.exists() and overwrite == False:
            print(rgi01_output.resolve(), 'already exists and overwrite option set to False. Skipping download.')
        else:
            print('Downloading', rgi01_fn)
            gdown.download(id=rgi01_gdrive_id, output=str(rgi01_output), quiet=~verbose)
        
        if rgi02_output.exists() and overwrite == False:
            print(rgi02_output.resolve(), 'already exists and overwrite option set to False. Skipping download.')
        else:
            print('Downloading', rgi02_fn)
            gdown.download(id=rgi02_gdrive_id, output=str(rgi02_output), quiet=~verbose)
            
        return rgi01_output, rgi02_output
    

def download_wgms(output_directory = '../data/wgms',
                  overwrite        = True,
                  verbose          = True):
    '''
    Downloads 2022-09 version of WGMS csv from https://wgms.ch/data_databaseversions/
    '''
    
    url = 'http://wgms.ch/downloads/DOI-WGMS-FoG-2022-09.zip'
    out = Path(output_directory,url.split('/')[-1])

    Path(output_directory).mkdir(parents=True, exist_ok=True)
    
    if out.exists() and overwrite == False:
        print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
    else:
        print('Downloading', url)
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
            print('Downloading EarthDEM data for', site)
            ID = site_ids[site]
            out = Path(output_directory,site)
            if out.exists() and overwrite == False:
                print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
            else:
                out_tmp = Path(out.as_posix()+'.tar.gz')
                gdown.download(id=ID, output=str(out_tmp), quiet=~verbose)
                if out_tmp.exists():
                    call = ['tar', 'zxvf', out_tmp.as_posix(), '--directory', output_directory.as_posix()]
                    gtsa.io.run_command(call,verbose=verbose)
                    print('Deleting',out_tmp.as_posix())
                    out_tmp.unlink(missing_ok=True)
        except:
            print('Download for', site, 'failed')
            print('Ensure it is one of', site_ids.keys())
            print('If receiving "Access denied" error try again later or use direct link in browser')
            pass
    
    # download all sites
    else:
        for site in site_ids.keys():
            try:
                print('Downloading EarthDEM data for', site)
                ID = site_ids[site]
                out = Path(output_directory,site)
                if out.exists() and overwrite == False:
                    print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
                else:
                    out_tmp = Path(out.as_posix()+'.tar.gz')
                    gdown.download(id=ID, output=str(out_tmp), quiet=~verbose)
                    if out_tmp.exists():
                        call = ['tar', 'zxvf', out_tmp.as_posix(), '--directory', output_directory.as_posix()]
                        gtsa.io.run_command(call,verbose=verbose)
                        print('Deleting',out_tmp.as_posix())
                        out_tmp.unlink(missing_ok=True)
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
            print('Downloading HSfM data for', site)
            ID = site_ids[site]
            out = Path(output_directory,site)
            if out.exists() and overwrite == False:
                print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
            else:
                out_tmp = Path(out.as_posix()+'.tar.gz')
                gdown.download(id=ID, output=str(out_tmp), quiet=~verbose)
                if out_tmp.exists():
                    call = ['tar', 'zxvf', out_tmp.as_posix(), '--directory', output_directory.as_posix()]
                    gtsa.io.run_command(call,verbose=verbose)
                    print('Deleting',out_tmp.as_posix())
                    out_tmp.unlink(missing_ok=True)
        except:
            print('Download for', site, 'failed')
            print('Ensure it is one of', site_ids.keys())
            print('If receiving "Access denied" error try again later or use direct link in browser')
            pass
    
    # download all sites
    else:
        for site in site_ids.keys():
            try:
                print('Downloading HSfM data for', site)
                ID = site_ids[site]
                out = Path(output_directory,site)
                if out.exists() and overwrite == False:
                    print(out.resolve(), 'already exists and overwrite option set to False. Skipping.')
                else:
                    out_tmp = Path(out.as_posix()+'.tar.gz')
                    gdown.download(id=ID, output=str(out_tmp), quiet=~verbose)
                    if out_tmp.exists():
                        call = ['tar', 'zxvf', out_tmp.as_posix(), '--directory', output_directory.as_posix()]
                        gtsa.io.run_command(call,verbose=verbose)
                        print('Deleting',out_tmp.as_posix())
                        out_tmp.unlink(missing_ok=True)
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

def download_hi_res_refdems(site = 'mount-baker',
                            output_directory = 'test_data',
                            overwrite = False,
                            verbose = True,
                             ):
    '''
    Downloads reference DEMs for DEMs at https://zenodo.org/record/7297154
    
    input options:
    site : 'mount-baker' or 'south-cascade'
    '''
    scg = '1m1DSnZ7tNIko6iU4WuPFsDODLkHX-E-6'
    scg_fn = 'WV_south-cascade_20151014_1m_dem.tif'
    baker = '1SXwGmjkjp3oCuF64XM9j894YJBR8bzs9'
    baker_fn = 'WADNR_mount-baker_20150827_1m_dem.tif'
    
    output_directory = Path(output_directory,site+'_1m_dems')
    output_directory.mkdir(parents=True, exist_ok=True)

        
    if site == 'mount-baker':
        blob_id = baker
        output = Path(output_directory, baker_fn)
    elif site == 'south-cascade':
        blob_id = scg
        output = Path(output_directory, scg_fn)
    else:
        print("site must be specified as either 'baker' or 'south-cascade'")
        return
    
    if overwrite:
        print('overwrite set to True')
    else:
        print('overwrite set to False')
        
    if output.exists() and not overwrite:
        print('File exists')
        print(output.as_posix())
    
    else:
        gdown.download(id=blob_id, output=output.as_posix(), quiet=not verbose)
        
    return

def download_hi_res_test_data(site = 'mount-baker',
                              output_directory = 'test_data',
                              overwrite = False,
                              max_workers = None,
                             ):
    '''
    Downloads 1m DEMs from https://zenodo.org/record/7297154
    
    input options:
    site : 'mount-baker' or 'south-cascade'
    '''
        
    if site != 'mount-baker' and site != 'south-cascade':
        print("site must be specified as either 'baker' or 'south-cascade'")
        return

    else:
        print('Downloading data from https://zenodo.org/record/7297154 for', site)
        
        if not max_workers:
            max_workers = psutil.cpu_count(logical=True)-1

        if overwrite:
            print('overwrite set to True')
        else:
            print('overwrite set to False')
        
        base = 'https://zenodo.org/'
        url  = base + 'record/7297154'

        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.text, 'html.parser')

        output_directory = Path(output_directory,site+'_1m_dems')
        output_directory.mkdir(parents=True, exist_ok=True)
        
        urls = []
        for link in soup.find_all('a'):
            url = link.get('href')
            if url:
                if '1m_dem' in url and site in url:
                    urls.append(base+url[1:])
        urls = sorted(set(urls))
        outputs = [Path(output_directory,
                        url.split('/')[-1].split('?')[0]) for url in urls]
        
        payload = []
        omissions = []
        for i,v in enumerate(outputs):
            if v.exists() and not overwrite:
                omissions.append(str(v))
            else:
                zipped = list(zip([urls[i],str(v)]))
                payload.append((zipped[0][0], zipped[1][0]))
                
        if omissions:
            print('Skipping:')
            for i in omissions:
                print(i)
            
        if payload:
            print('Downloading:')
            for i in payload:
                print(i[0])
            print('Writing to', str(output_directory))

            thread_downloads(output_directory, 
                             payload,
                             max_workers=max_workers,
                            )

def download_test_data(output_directory,
                       payload):
    url, out = payload
    r = requests.get(url)
    open(out, 'wb').write(r.content)
    return out
        
def thread_downloads(output_directory, 
                     payload,
                     max_workers= None):
    
    if not max_workers:
        max_workers = psutil.cpu_count(logical=True)-1
    
    with tqdm(total=len(payload)) as pbar:
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        future_to_url = {pool.submit(download_test_data,
                                     output_directory,
                                     x): x for x in payload}
        for future in concurrent.futures.as_completed(future_to_url):
            pbar.update(1)