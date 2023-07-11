import numpy as np
import xarray as xr
import warnings
import scipy.stats

def relative_entropy(ensemble, climatology, mean_var_c = None, dim_e = 'Y',dim_c = 'Y'): 
    '''Calculate the relative entropy between ensemble and climatology pdfs 
    from just the mean and std terms, after Fang et al 2022 JClim
    
    PDFs are calculated in the dimensions dim_e and dim_c respectively, 
          (probably multiple dimensions work but I haven't tested this)
          all other dimensions should vectorise nicely
    climatology can be provided as a set of samples, 
        or as precalculated mean and variance (mean_var_c)
        '''
    

    #Calculate ensemble stats
    mean = ensemble.mean(dim_e)
    var = ensemble.std(dim_e)**2
    
    #Calculate climatology stats, or fish them out of the provided mean_var_c
    if mean_var_c is None:
        assert climatology[dim_c].shape[0]>5, 'Climatology must contain sufficiently many "year" samples to calculate mean and variance'
        mean_c = climatology.mean(dim_c)
        var_c_inv = (climatology.std(dim_c)**(-2))
    else:
        assert climatology is None, 'Only one of climatology or mean_var_c (the stats from the climatology) should be supplied'
        mean_c = mean_var_c[0]
        var_c_inv = mean_var_c[1]**(-1)
        
    #Formula directly lifted from Fang et al 2022
    P = ((0.5*(mean-mean_c)**2*var_c_inv)
            +(-0.5*np.log(var*var_c_inv)+0.5*(var*var_c_inv-1)))
    return 1-np.exp(-P)

#I have no idea why these two functions are here - JJ, 2023-07-07
def diff_mean(ensemble,climatology,mean_c = None,dim_e = 'Y',dim_c = 'Y'):
    ''' Return the difference between the ensemble mean, calculated along dim_e
    and the climatology mean, calculated along dim_c'''
    if mean_c is None:
        mean_c = climatology.mean(dim_c)
    return ensemble.mean(dim_e)-mean_c

def diff_std(ensemble,climatology,std_c = None,dim_e = 'Y',dim_c = 'Y'):
    ''' Return the difference between the ensemble standard deviation, calculated along dim_e
    and the climatology standard deviation, calculated along dim_c'''
    if std_c is None:
        std_c = climatology.mean(dim_c)
    return ensemble.mean(dim_e)-std_c

def bootstrap_samples(data, n_samples, n_Y = 1, n_M = 40):
    ''' Cut up data to return a dataset with dimensions {'M':n_M, 'Y':n_Y, 'sample':n_samples}
    In *most* situations, only one of n_samples or n_Y needs to be > 1, 
    but sometimes I'll apply functions to both
    Feel free to subset data as much as you want before handing it here'''

    #A randomly selected n_M,n_Y,n_samples points, to imitate any set of members, years, and a bonus dim
    y0 = xr.DataArray(np.random.choice(data.Y,(n_M,n_Y,n_samples)),dims=('new_M','new_Y','sample'))
    m0 = xr.DataArray(np.random.choice(data.M,(n_M,n_Y,n_samples)),dims=('new_M','new_Y','sample'))
    l0 = xr.DataArray(np.random.choice(data.L,(n_M,n_Y,n_samples)),dims=('new_M','new_Y','sample'))
    
    return data.sel(L=l0,Y=y0,M=m0).rename({'new_M':'M','new_Y':'Y'})

def naive_stat_test(ens,
                       clim,
                       stat_test = lambda x,y: scipy.stats.ttest_ind(x,y).pvalue,
                      chunk = {'nlon':64,'nlat':64}):
    
    '''Apply some stat test to ensemble, with a background of clim.
    For example, you might want to check the difference in means of the ensemble at some lead
            and the climatology
    Any raw test which I write would be much faster, but this can take any function which understands
            a one dimensional ndarray in the place of stat test
    All dimensions are hardcoded (sorry) and will remain that way until I work out
        what sort of versatility is required
    Currently assumes that you never want to mix up different months of year
        (which took forever to write)
    
    ens: an ensemble, with dimensions M, L, [spacial dims]
    clim: the climatology, with dimensions time, [spacial dims]
    stat_test: ie lambda x,y: scipy.stats.ttest_ind(x,y).pvalue
    chunk: How to cut up the data for parallelization. Needs to be something, or it'll try to do
            everything on a single core. '''
    
    # Get a month for each lead time, rather than time.month sitting on (L,M)
    # All ensemble members should start at the same month, because seasonality
    assert np.all(ens['time.month'] == ens['time.month'].isel(M=0)), 'If your ensemble members are happening at different times of year rewrite this code'
    new_m = ens['time.month'].isel(M=0).astype(int)
    del new_m['time']
    ens = ens.assign_coords({'month':new_m})
    
    if 'L' in ens.dims:
        # Reshape the climatology so it can be iterated through/vectorized along dimension L, 
        #    and every lead time gets the right month climatology
        # Could be slightly more efficient, but it runs in 2 seconds, where the stat test takes 2-20 minutes,
        #    so speed is not particularly important
        reshaped_clim = xr.concat(
            [clim.groupby('time.month')[int(ens.isel(L=l).month)].drop_indexes('time') for l in ens.L],
             'L',
            coords='minimal',compat='override', #Ignore issues with time coordinate being reshapen
                          ).assign_coords({'L':ens.L})
    else:
        #If there's only one month, just grab the bit of clim that you need
        reshaped_clim = clim.groupby('time.month')[int(ens.month)]
    
    return xr.apply_ufunc(stat_test,                          # Do this stat test
               ens.chunk(chunk).chunk({'L':-1}),              # To these two DataArrays 
               reshaped_clim.chunk(chunk).chunk({'time':-1}), #     Chunked in space, but time needs grouping and L might be weird
               input_core_dims = [['M'],['time']],            # Leave the ensemble member and time dimensions on each, respectively
               vectorize=True,                                # But hand everything else to the stat test one at a time
               dask='parallelized',                           # Use different cores for each stat test, please
              ) 