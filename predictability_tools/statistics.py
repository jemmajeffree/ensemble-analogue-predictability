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
