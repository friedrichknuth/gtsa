import gtsa
from bs4 import BeautifulSoup
from pathlib import Path
import requests
import shutil
import psutil
from tqdm import tqdm
import concurrent
import gdown

def download_data(output_directory,
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
        future_to_url = {pool.submit(download_data,
                                     output_directory,
                                     x): x for x in payload}
        for future in concurrent.futures.as_completed(future_to_url):
            pbar.update(1)
            
            
def download_rgi_01_02(output_directory = 'data/rgi',
                       region           = 'both',
                       overwrite        = True,
                       verbose          = True):
    
    '''
    Downloads GeoJSON files for RGI regions 01 and 02.
    
    Data originally downloaded from http://www.glims.org/RGI/rgi60_files/00_rgi60.zip
    Staged on Google Drive
    Shapefiles for RGI 01 and 02 converted to GeoJSON
    
    Input
    output_directory : path : location to save data
    region           : int  : either "1" or "2" for RGI 01 or RGI 02, or "both"
    
    Returns
    (path/to/01_rgi60_Alaska.geojson' , path/to/02_rgi60_WesternCanadaUS.geojson)
    '''
    print('Downloading GeoJSON files for RGI regions 01 and/or 02 to', output_directory)

    rgi01_gdrive_id = '18B0derwIUetJy1v5dBJaO-tTKFqqEV_u'
    rgi01_fn        = '01_rgi60_Alaska.geojson'
    rgi02_gdrive_id = '1fRjxyOcZYtTM95xGf6kgdnF4rDFp_lA3'
    rgi02_fn        = '02_rgi60_WesternCanadaUS.geojson'

    Path(output_directory).mkdir(parents=True, exist_ok=True)
 
    
    if str(region) == '1':
        rgi01_output = Path(output_directory, rgi01_fn)
        if rgi01_output.exists() and overwrite == False:
            print(rgi01_output.resolve(), 'already exists and overwrite option set to False. Skipping download.')
        else:
            print('Downloading', rgi01_fn)
            gdown.download(id=rgi01_gdrive_id, output=str(rgi01_output), quiet=~verbose)
        return rgi01_output
    
    elif str(region) == '2':
        rgi02_output = Path(output_directory, rgi02_fn)
        if rgi02_output.exists() and overwrite == False:
            print(rgi02_output.resolve(), 'already exists and overwrite option set to False. Skipping download.')
        else:
            print('Downloading', rgi02_fn)
            gdown.download(id=rgi02_gdrive_id, output=str(rgi02_output), quiet=~verbose)
        return rgi02_output
        
    elif region == 'both':
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
    

def download_historical_data(site = 'mount-baker',
                             product = 'dem',
                             output_directory = 'data',
                             include_refdem = False,
                             overwrite = False,
                             max_workers = None,
                             verbose = True,
                             ):
    '''
    Downloads 1m DEMs from https://zenodo.org/record/7297154
    
    input options:
    site : 'mount-baker' or 'south-cascade'
    product : 'dem' or 'ortho'
    '''
        
    if site != 'mount-baker' and site != 'south-cascade':
        print("site must be either 'baker' or 'south-cascade'")
        return
    
    if product != 'dem' and product != 'ortho':
        print("product must be either 'dem' or 'ortho'")
        return
     
    else:
        
        if product == 'dem':
            product_key = '1m_dem'
            
        elif product == 'ortho':
            product_key = 'ortho'
            
        if include_refdem:
            download_reference_dems(site = site,
                                    output_directory = output_directory,
                                    overwrite = overwrite,
                                    verbose = verbose,
                                   )
        
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

        output_directory = Path(output_directory,product+'s',site)
        output_directory.mkdir(parents=True, exist_ok=True)
        
        urls = []
        for link in soup.find_all('a'):
            url = link.get('href')
            if url:
                if product_key in url and site in url:
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
        if not omissions and not payload:
            print('No files available for download at', url)

def download_reference_dems(site = 'mount-baker',
                            output_directory = 'data',
                            overwrite = False,
                            verbose = True,
                             ):
    '''
    Downloads reference DEMs for DEMs at https://zenodo.org/record/7297154
    
    input options:
    site : 'mount-baker' or 'south-cascade'
    '''
    
    if site != 'mount-baker' and site != 'south-cascade':
        print("site must be either 'baker' or 'south-cascade'")
        return
    
    scg = '1m1DSnZ7tNIko6iU4WuPFsDODLkHX-E-6'
    scg_fn = 'WV_south-cascade_20151014_1m_dem.tif'
    baker = '1SXwGmjkjp3oCuF64XM9j894YJBR8bzs9'
    baker_fn = 'WADNR_mount-baker_20150827_1m_dem.tif'
    
    output_directory = Path(output_directory,'dems',site)
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
        print('Reference DEM file exists')
        print(output.as_posix())
    
    else:
        print('Downloading reference dem for', site)
        gdown.download(id=blob_id, output=output.as_posix(), quiet=not verbose)
        
    return

