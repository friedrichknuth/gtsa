import gtsa

from pathlib import Path

data_dirs = ['../../data/orthos/south-cascade',
             '../../data/orthos/mount-baker']

ortho_cogs = []

for data_dir in data_dirs:
    files = [x for x in sorted(Path(data_dir).glob('*.tif'))]
    output_directory = Path(data_dir,'cogs')


    out = gtsa.utils.create_cogs(files,
                                 output_directory = output_directory,
                                 crs = 'EPSG:4326', # required for visualization with folium and titiler
                                 overwrite = False,
                                 max_workers = None, 
                                 verbose = True)
    
    ortho_cogs.append(out)
    
print('DONE')