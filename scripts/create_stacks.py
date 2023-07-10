import gtsa

from pathlib import Path
import shutil
import psutil
import pandas as pd


data_dir = '../test_data/south-cascade_1m_dems/'
# data_dir = '../test_data/mount-baker_1m_dems/'


dems = [x.as_posix() for x in sorted(Path(data_dir).glob('*.tif'))]
date_strings = [x[1:-1] for x in gtsa.io.parse_timestamps(dems,
                                                          date_string_pattern='_........_')]
# ensure chronological sorting 
date_strings, dems = list(zip(*sorted(zip(date_strings, dems))))
date_times = [pd.to_datetime(x, format="%Y%m%d") for x in date_strings]

ref_dem = dems[-1]

ds = gtsa.io.xr_stack_geotifs(dems,
                              date_times,
                              ref_dem,
                              resampling="bilinear",
                              save_to_nc = True,
                              nc_out_dir = Path(data_dir,'nc_files').as_posix(),
                              overwrite = False)

ds_zarr = gtsa.io.create_zarr_stack(ds,
                                    output_directory = Path(data_dir,'stack').as_posix(),
                                    overwrite = False)
    
print('DONE')