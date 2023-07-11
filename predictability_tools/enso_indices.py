import numpy as np
import xarray as xr
import warnings


nino34_region = np.array((190,240,-5,5))
nino3_region = np.array((210,270,-5,5))
nino4_region = np.array((160,210,-5,5))
wholeP_region = np.array((140,280,-5,5))
#pacific_mask = xr.open_dataarray('./../ocean_basin_mask.nc').sel(region='Pacific Ocean')

'''All of these CESM functions can be generalised for other models, 
or other data naming systems (ie CMORised), but I'll update them when I know what 
else I'm working with and what's needed'''

def dedrift(data):
    ''' Pretty self explanitory, and I'm not sure if I'll use it or the one liner'''
    return data-data.mean(('Y','M'))

def CESM_average_region(data, region, filename=None):
    '''Calculate the spacial average of CESM data over a box, 
    and potentially write to filename
    i.e. calculate the NINO34 index given SST data and the NINO34 box
        data is an xarray data array with CESM naming conventions
        region is lon1, lon2, lat1, lat2 of the averaging region
        filename is optional dump path
'''
    
    assert np.all((data.TLONG>=0) & (data.TLONG<=360)) #Just check periodic coordinates
    assert np.all((region[:2]>=0) & (region[:2]<=360))
    
    index = data.where((data.TLONG>region[0]) &
                      (data.TLONG<region[1]) & 
                      (data.TLAT>region[2]) & 
                      (data.TLAT<region[3]),
                      #drop = True #Fails with more recent xarray, dunno why, but not important with the load straight after
                      ).mean(('nlat','nlon')).load()
    if not(filename is None):
        index.to_netcdf(filename)
    return index

def CESM_peak_longitude(data, lon_smoothing, filename=None,peak = 'either'):
    ''' Take the meridional average of anomalies, and then find the peak 
    with a given longitudinal smoothing
    data is an xarray data array OF ANOMALIES with CESM naming conventions
    lon_smoothing is an integer - the number of lon gridsteps to smooth
    filename is an optional dump path
    peak is one of 'either', 'negative', or 'positive', describing the type of peak anomaly to find'''
    
    smoothed_mean = data.mean('nlat').rolling(nlon=lon_smoothing).mean()
    smoothed_mean.load()

    smoothed_mean = smoothed_mean.transpose('nlon',...)
    nan_mask = np.all(np.isnan(smoothed_mean.data),axis=0)
    smoothed_mean.data[:,nan_mask] = -1000

    #Find peak
    if peak == 'either':
        max_i = np.abs(smoothed_mean).argmax('nlon')
    elif peak == 'positive':
        max_i = smoothed_mean.argmax('nlon')
    elif peak == 'negative':
        max_i = (-1*smoothed_mean).argmax('nlon')
    else:
        assert False, "peak must be one of 'either', 'positive' or 'negative'"

    #Find the amplitude and location this responds to
    max_amp = smoothed_mean.sel(         nlon=max_i)
    max_loc = data.TLONG.mean('nlat').sel(nlon=max_i).load()

    max_amp.data[nan_mask] = np.nan
    max_loc.data[nan_mask] = np.nan

    if not (filename is None):
        xr.Dataset({'amplitude':max_amp, 'longitude':max_loc}).to_netcdf(filename)

    return max_amp, max_loc
    
    
def CESM_ELI(sst,sst_threshold, filename =None):
    '''Calculate ENSO Longitude Index (ELI), after Williams & Patricola (2018)
    
    It's not 100% clear to me what longitude they use as the western boundary of the Pacific, so this function takes the full extent of the data given and averages that
    
    sst is an xarray data array with CESM naming conventions
        (used as sst not data because the function is a specific index and not generalisable)
    sst_threshold has the same dimensions as sst, but missing nlat and nlon
         it describes the mean sst over the tropics at that point in time'''
    
    ELI = sst.TLONG.where(sst>sst_threshold).mean(('nlon','nlat'))
    ELI.load()
    if not (filename is None):
        ELI.to_netcdf(filename)
        
    return ELI

def project_onto_EOF(data, eof, filename=None, space_dims = ('nlon','nlat'),time_dims = ('Y','L','M')):
    ''' Calculating EOFs takes time and memory, and linear algebra is fast
    This function linearly projects a dataset onto pre-calculated EOFs, which can be generated using a much smaller subset of the data, because 1000 years of control run are not needed to find the dominant eigenvectors.
    
    Does not remove seasonality (I'd recommend removing this, and drift or whatever, prior to projecting)
    
    data is an xarray data array of whatever you want to project
    eof is an xarray data array with dimensions (spacial dims of data, mode)
       - It has presumably been spat out by the eofs package, but it never hurts to try and stop yourself doing stupid things, so I'm insisting on the same dimensions being reapplied before using it for projection
    '''
    
    #Set up linear algebra
    A = eof.stack({'loc':space_dims}
                 ).transpose('loc','mode').to_numpy()
    mode_coord = eof.mode
    
    b = data.stack({'loc':space_dims,'time_stack':time_dims})
    time_stack = b.time_stack
    if np.sum(np.isnan(b))>0:
        warnings.warn('Replacing nans with 0 before linear algebra. You ought to deal with them earlier though...')
        b = b.fillna(0)
    b = b.data
    
    #Actual projection
    ataat = np.linalg.inv(A.T@A)@A.T
    x = ataat@b

    #Reassemble into xarray dataset
    pca = xr.DataArray(x,dims=('mode','time_stack'),coords={'mode':eof.mode,
                                                  'time_stack':time_stack}).unstack().rename('pca')

    #Output
    if not(filename is None):
        pca.to_netcdf(filename)
    return pca


