from pathlib import Path
import gtsa

def resample_dem(dem_file_name, 
                 res=1,
                 out_file_name=None,
                 overwrite=True,
                 verbose=True):
    """
    dem_file_name : path to dem file
    res : target resolution
    
    Assumes crs is in UTM
    """
    res = str(res)
    
    if not out_file_name:
        out_file_name = '_'.join([str(Path(dem_file_name).with_suffix("")),res+'m.tif'])
    
    Path(out_file_name).parent.mkdir(parents=True, exist_ok=True)
    
    if Path(out_file_name).exists() and not overwrite:
        return out_file_name
    
    if overwrite:
        Path(out_file_name).unlink(missing_ok=True)
        
    call = ['gdalwarp',
            '-r','cubic',
            '-tr', res, res,
            '-co','TILED=YES',
            '-co','COMPRESS=LZW',
            '-co','BIGTIFF=IF_SAFER',
            '-dstnodata', '-9999',
            dem_file_name,
            out_file_name]
            
    gtsa.io.run_command(call, verbose=verbose)
    return out_file_name