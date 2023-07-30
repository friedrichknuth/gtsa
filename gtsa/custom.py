import numpy as np
import xarray as xr

def func(ds, variable_name='band1'):
    '''
    The `gtsa` command line utilitiy will look for a function called `func` in gtsa.custom and pass the xarray DataArray to it.
    You can use this function to do whatever you want with the DataArray. As an example, this function computes the nmad along the time axis.
    '''

    def nmad(array):
        if np.all(~np.isfinite(array)):
            return np.nan
        else:
            return 1.4826 * np.nanmedian(np.abs(array - np.nanmedian(array)))
        
    result = xr.apply_ufunc(nmad, 
                            ds[variable_name],
                            input_core_dims=[['time']],
                            vectorize=True, 
                            dask='parallelized',
                            output_dtypes=[float],
                        )
    
    # result = xr.apply_ufunc(
    #     nmad,
    #     ds[variable_name],
    #     dask="allowed",
    # )

    return result
    