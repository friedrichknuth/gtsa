import gtsa
import pandas as pd
from pathlib import Path
import shutil

import warnings
warnings.filterwarnings("ignore")

bucket = 'petrichor'
aws_server_url = 's3.us-west-2.amazonaws.com'
product = 'dems'
base_directory = './stacks'
cleanup = False

sites = gtsa.io._get_test_sites(bucket)

for s in sites:
    folder = gtsa.io.Path(s, product).as_posix()
    
    cog_urls = gtsa.io.parse_urls_from_S3_bucket(bucket,
                                                 aws_server_url = aws_server_url,
                                                 folder = folder)
    
    date_times = [pd.to_datetime(x) for x in gtsa.io.parse_timestamps(cog_urls)]
    
    ref_dem = cog_urls[-1]
    
    nc_output_directory = Path(base_directory, s, 'nc_files').as_posix()
    Path(nc_output_directory).mkdir(parents=True, exist_ok=True)

    ds = gtsa.io.xr_stack_geotifs(cog_urls,
                                  date_times,
                                  ref_dem,
                                  resampling="bilinear",
                                  save_to_nc = True,
                                  nc_out_dir = nc_output_directory,
                                  overwrite = False)
    
    ds['band1'].data = ds['band1'].data.rechunk({0:'auto', 1:'auto', 2:'auto'}, 
                                                        block_size_limit=1e8, 
                                                        balance=True)
    
    zarr_output_directory = Path(base_directory, s, 'stack').as_posix()
    Path(zarr_output_directory).mkdir(parents=True, exist_ok=True)
    
    ds_zarr = gtsa.io.create_zarr_stack(ds,
                                        output_directory = zarr_output_directory,
                                        overwrite = False,
                                        cleanup = cleanup)
    
    call = ['aws',
            's3', 'cp', str(zarr_output_directory)+'/.', 
            's3://'+bucket+'/'+s+'/'+ 'stack' + '/ --recursive']
    call = ' '.join(call)
    print(call)
    gtsa.io.run_command(call,verbose=True)
    
    if cleanup:
        shutil.rmtree(nc_output_directory, ignore_errors=True)
    
print('DONE')