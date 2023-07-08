import numpy as np
import xarray as xr
import warnings

def find_analogues(state, data, n,weights=None):
    '''Return the indices of the n closest states from data to state 
    (including the index of state, if it's in data)
    
    Currently can only handle two dimensional data: mode and whatever your data stack dim is.
    If you want to use this code without EOFs (ie lat and lon), you'll either need to stack data or
    rewrite the next few lines to cope with a few dimensions.
    If you have several time dimensions to look through (ie lead time and ensemble member), 
    then you definitely need to stack them, because argsort can't cope with multiple dimensions. Sorry.
    '''
    assert np.sum(np.isnan(data))==0, "Not sure nans work with this code, tread carefully. Replacing them with zeros is probably safe"
    
    if weights is None: #If no weights make an array of ones
        weights = xr.DataArray(np.ones(state.mode.shape),dims=('mode',))
    #Euclidian distance/least square
    distance = ((state-data)**2*weights).sum('mode')
    
    #Earliest entries of argsort are the smallest values
    return distance.argsort()[:n].data

def random_inits(pca,
                 n_years,
                 start_month):
    nov_pca = pca.where(np.isin(pca['time.month'],initial_month),drop=True)
    years = np.random.choice(nov_pca['time.year'],n_years)
    
    return nov_pca.isel(time=years)

def analog_ensemble(init_pca,
                    pca, 
                    weights, 
                    n_members,
                    initial_month = 11, #Should work with an array of months, but I haven't tested this functionality in detail
                    lead_times = np.arange(122),
                    mode_slice = slice(None,10), #How many EOFs to use. Pretty sure it doesn't matter much
                   ):
    '''Build a DPLE-style (dimension names etc) ensemble, based on the initial conditions suggested.
    
    init_pca:   The initial conditions you would like to find analogues for. Can be one or many
    pca: The pool of states to select from
    weights: Reative weighting of pca in the dimension 'mode'
    n_members: How many analogues ("ensemble members") to find
    initial_month: What months to select analogues from, to minimise seasonality issues
    lead_times: How far forwards/back you want those ensemble members
    mode_slice: How many modes of variability to bother using. Doesn't make much difference
    '''
                    
    #Initialise only from the same month to remove seasonality problems
    nov_pca = pca.where(np.isin(pca['time.month'],initial_month),drop=True)
    
    nearly_DPLE_i = []
    lead_increments = xr.DataArray(lead_times,dims=('L',))
    
    for init in init_pca: 
        year_i = pt.find_analogues(init.isel(mode=mode_slice), #find analogues for these years
                                   nov_pca.isel(mode=mode_slice,time=slice(None,-max(lead_times))), #from these years
                                   n_members,                                                       #this many of them
                                   weights=weights.isel(mode=mode_slice))
        
        start_times = nov_pca.time.isel(time=year_i)
        
        assert len(start_times.shape[0]) == 1, 'Not sure how this code will go with multidimensional analogues'
        
        #I can't find a better way to write this line
        full_i = xr.DataArray(np.where(np.isin(pca.time,start_times))[0],dims=('M'))
        nearly_DPLE_i.append(full_i+lead_increments)
    
    #Handing back the full pca rather than just the i, because it's less likely to be accidentally used wrong
    return pca.isel(time=xr.concat(nearly_DPLE_i,'Y').assign_coords(L = lead_times))
    
