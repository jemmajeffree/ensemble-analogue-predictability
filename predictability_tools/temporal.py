import numpy as np
import xarray as xr
import warnings
import cftime

def DJF_mean(x):
    warnings.warn('Old DJF_mean, perhaps switch to using seasonal_mean?')
    return x.rolling({'L':3},center=True).mean().sel(L=np.arange(10)*12+2)

def seasonal_mean(x,season, remove_half_seasons = True):
    '''Average over a single season and return that data for each year
    DJF is defined by the JF year, not the D year
    
    x is whatever you want to take the average of
    season is a string (eg. 'DJF') which specifies which season is being averaged
    remove_half_seasons determines the behaviour with seasons that are incomplete
    '''
    
    def tweak_djf(t):
        '''Move December into the next year'''
        if t.month == 12:
            return t.replace(year=t.year+1)
        else:
            return t
        
    if season =='DJF':
        x = x.assign_coords({'time':xr.apply_ufunc(tweak_djf,x.time,vectorize=True)})
         
    if remove_half_seasons:
        keep_years = ((x['time.season']==season).groupby('time.year').sum()==3)
    else:
        keep_years = np.ones_like((x['time.season']==season).groupby('time.year').sum(),dtype=bool)
            
        
    return x.where(x['time.season']==season).groupby('time.year').mean()[keep_years].rename({'year':'time.year'})

def correct_cesm_date(x,time_dim = 'time'):
    '''Redo all the timestamps in x to be one month earlier, to fix the CESM problem about 
    saving things with the wrong encoding for cftime.
    This function also flags that it's corrected the date, and checks if it's already been called,
    to minimise the risk of doing anything stupid that ends up with shifting two months earlier
    
    x: whatever you would like to fix up the coordinates on
    time_dim: the coordinate on x which you would like to fix
    '''
    
    def fix_month(t):
        if t.month == 1:
            return t.replace(year = t.year-1, month = 12)
        else:
            return t.replace(month = t.month-1)
    if 'cesm_date_corrected' in x.attrs:
        warnings.warn('This data may have already been corrected for the cesm month thing, but you\'ve asked me to do it again. - Double check that this is what you want to do')

    return x.assign_coords({time_dim:xr.apply_ufunc(fix_month, x[time_dim], vectorize=True,dask='parallelized',output_dtypes=['object'])}).assign_attrs({'cesm_date_corrected':True})
