import gtsa
from pathlib import Path
from tqdm import tqdm
import concurrent
import shutil

sites = ['baker', 'gnp', 'helens', 'rainier', 'hinman', 'scg', 'tetons']
sites = ['gnp', ]
base_directory = '/mnt/storage/knuth/sites/analysis_ready_data/'
bucket = 'petrichor'
product = 'dems'
verbose = True
overwrite = False
suffix = '_COG.tif'

for s in sites:
    input_directory = Path(base_directory, s, product).as_posix()
    output_directory = Path(base_directory, s, product, 'cogs').as_posix()

    Path(output_directory).mkdir(parents=True, exist_ok=True)

    files = sorted(Path(input_directory).glob('*.tif'))
    for f in files:
        print(f.as_posix())


    calls = []
    for fn in files:
        out_fn = Path(output_directory,fn.with_suffix('').name+'_reproj.tif')
        if not out_fn.exists() or overwrite:
            call = ['gdalwarp',
                    '-r', 
                    'cubic', 
                    '-t_srs', 
                    'EPSG:4326', 
                    fn.as_posix(), 
                    out_fn.as_posix()]
            calls.append(call)

    if calls:
        with tqdm(total=len(calls)) as pbar:
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)
            futures = {pool.submit(gtsa.io.run_command, x): x for x in calls}
            for future in concurrent.futures.as_completed(futures):
                r = future.result()
                pbar.update(1)

    files = sorted(Path(output_directory).glob('*reproj.tif'))
    for f in files:
        print(f.as_posix())
        
    calls = []
    for fn in files:
        out_fn = Path(output_directory,fn.with_suffix('').name+suffix)
        if not out_fn.exists() or overwrite:
            call = ['/mnt/working/knuth/sw/miniconda3/envs/hsfm/bin/gdal_translate',
                    fn.as_posix(), 
                    out_fn.as_posix(),
                    '-of', 'COG',
                    '-co', 'BLOCKSIZE=512',
                    '-co', 'RESAMPLING=BILINEAR',
                    '-co', 'COMPRESS=DEFLATE',
                    '-co', 'BIGTIFF=YES'
                   ]
            calls.append(call)
    if calls:
        with tqdm(total=len(calls)) as pbar:
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)
            futures = {pool.submit(gtsa.io.run_command, x): x for x in calls}
            for future in concurrent.futures.as_completed(futures):
                r = future.result()
                pbar.update(1)
        for fn in files:
            Path(fn).unlink(missing_ok=True)
            
            
    files = sorted(Path(output_directory).glob('*reproj_COG.tif'))
    for f in files:
        print(f.as_posix())
        
        
    call = ['aws',
            's3', 'cp', str(output_directory)+'/.', 
            's3://'+bucket+'/'+s+'/'+ product + '/ --recursive --exclude "*" --include "*.tif"']
    call = ' '.join(call)
    print(call)
    gtsa.io.run_command(call,verbose=True)
    
print('DONE')
    
    