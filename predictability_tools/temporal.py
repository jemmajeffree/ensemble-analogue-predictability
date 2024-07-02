import numpy as np
import xarray as xr
import warnings
import cftime

def dedrift(data):
    ''' Pretty self explanitory, and I'm not sure if I'll use it or the one liner'''
    return data-data.mean(('Y','M'))

def declim(data,timedim='time'):
    '''Strip a seasonally varying climatology from the data'''
    warnings.warn('Screwing up the chunking; use strip_climatology')
    return data.groupby(timedim+'.month')-data.groupby(timedim+'.month').mean()

def strip_climatology(ds, 
                      clim = None, 
                      time_dim = 'time',
                      seasonal_dim = 'month',
                     ):
    '''
    Removes the climatology/seasonal variation of a dataset. This function should 
    return the same as ds.groupby('time.month')-ds.groupby('time.month').mean(),
    but it does so without rechunking in the time dimension, and in some instances
    can be 100x faster

    Parameters
    ----------
    ds : xr.DataArray 
        dataarray to remove climatology from
        (probably works with a xr.Dataset, but I haven't tested this functionality rigourously
    clim : None or xr.DataArray
        climatology of dataset, if already calculated
    time_dim : str
        dimension over which to calculate the climatology
    seasonal_dim: str
        variable over which to calculate climatologies
        Together, time_dim and seasonal_dim (ie 'time.month') form what goes into the groupby
    
    Returns
    -------
    ds_anomaly: xr.DataArray
        ds, with the climatology removed
        should be chunked in the same way as ds, and not expand the dask graph too much
    
    With MANY thanks to @rabernat from github for bringing this solution to my attention; 
    This code is adapted from 
    https://nbviewer.org/gist/rabernat/30e7b747f0e3583b5b776e4093266114
    
    '''
    
    def calculate_anomaly(ds,clim,time_dim,seasonal_dim):
        gb = ds.groupby(time_dim+'.'+seasonal_dim)
        if clim is None:
            clim = gb.mean()
        return gb - clim

    return xr.map_blocks(calculate_anomaly,
                         ds.chunk({'time':-1}),
                         kwargs={'clim':clim,'time_dim':time_dim,'seasonal_dim':seasonal_dim},
                         template=ds.assign_coords({seasonal_dim:ds[time_dim+'.'+seasonal_dim]})
                        )

def calc_climatology(ds, 
                      time_dim = 'time',
                      seasonal_dim = 'month',
                     ):
    '''
    As above, but returns the climatology not the subtracted thing
    
    '''
    
    def calculate_climatology(ds,time_dim,seasonal_dim):
        gb = ds.groupby(time_dim+'.'+seasonal_dim)
        clim = gb.mean()
        return clim

    return xr.map_blocks(calculate_climatology,
                         ds,
                         kwargs={'time_dim':time_dim,'seasonal_dim':seasonal_dim},
                         template=ds.isel(time_dim=0).assign_coords({seasonal_dim:ds[time_dim+'.'+seasonal_dim]})
                        )

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
        keep_years = ((x['time.season']==season).groupby('time.year').sum('time')==3)
    else:
        keep_years = np.ones_like((x['time.season']==season).groupby('time.year').sum('time'),dtype=bool)
            
        
    return x.where(x['time.season']==season).groupby('time.year').mean().transpose('year',...)[keep_years].rename({'year':'time.year'})

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
