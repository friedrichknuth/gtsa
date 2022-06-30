import pathlib
import gtsa

def resample_dem(dem_file_name, 
                 res=1, 
                 overwrite=True,
                 verbose=True):
    """
    dem_file_name : path to dem file
    res : target resolution
    
    Assumes crs is in UTM
    """
    res = str(res)
    out_fn = '_'.join([str(pathlib.Path(dem_file_name).with_suffix("")),
                       res+'m.tif'])
    
    if overwrite:
        pathlib.Path(out_fn).unlink(missing_ok=True)
    
    call = ['gdalwarp',
            '-r','cubic',
            '-tr', res, res,
            '-co','TILED=YES',
            '-co','COMPRESS=LZW',
            '-co','BIGTIFF=IF_SAFER',
            '-dstnodata', '-9999',
            dem_file_name,
            out_fn]
            
    gtsa.io.run_command(call, verbose=verbose)
    return out_fn