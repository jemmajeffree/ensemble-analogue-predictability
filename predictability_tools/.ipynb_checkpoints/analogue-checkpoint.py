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
    
    assert type(distance) is xr.DataArray, 'Stuff must come out to a DataArray (not Dataset) here'
    
    #Earliest entries of argsort are the smallest values
    return distance.argsort()[:n].data

def random_inits(pca,
                 n_years,
                 initial_month):
    '''Randomly select n_years states from pca in the time dimension, limited
    to only be in the months start_month
    
    Intended for use creating an analogue ensemble when you don't really care about initialisations'''
    
    nov_pca = pca.where(pca['time.month'].isin(initial_month),drop=True)
    years = np.random.choice(nov_pca['time.year'],n_years)
    
    return nov_pca.isel(time=years)

def arg_month_year(archive_time,
                   years,
                   m,
                  ):
    '''Match up a bunch of years (that you might have picked out from seasonal averages, for example)
    with the original timestamps of your archive, prescribing what month they came from
    
    years: the years to match (presumably initial conditions for analogue ensembles)
    archive_time: the time to match the years in
    m: what month to look for in each year
    
    returns the indices needed to find those years/months in archive_time'''
    
    return xr.DataArray(np.where(archive_time['time.year'].isin(years) & (archive_time['time.month'] == m))[0],dims='time')

def pseudo_ensemble(initial_i,
                    archive,
                    leads):
    '''Given a prescribed set of start times (eg. all the biggest El Niño events in the archive),
    pick them out of the archive and reshape them to get an ensemble thing
    STILL ASSUMING THAT archive has a time dimension and everything else you want to keep.
    
    initial_i: the indexes for start conditions in axis time. Can be a numpy array (if there's no inherent coordinates to preserve), 
               or a DataArray. If a DataArray, coordinates should be ('M',), or possibly ('M','Y'). It should cope okay with other coordinates, 
               which will just be what the ensemble coordinates spit out, but it's better not to use 'time' if you're selecting from time
    archive: where the initial conditions (and the rest of the ensemble) come from
    lead_times: what lead times to consider. Positive ones mean after initial_i, (ie ENSO imapcts)
         negative ones mean before initial_i (ie ENSO precursors)
         '''
    if type(initial_i) == np.ndarray:
        initial_i = xr.DataArray(initial_i,dims='M')
        
    if not('M' in initial_i.dims):
        warnings.warn('Look, you really ought to sort out your initial_i dimensions yourself (eg rename time to M) or who knows what will happen')
    
    # Lose the events that run off the start or end of the simulation
    initial_i = initial_i.where(((initial_i+np.max(leads)<archive.time.shape[0]) &
                           (initial_i+np.min(leads)>0)),
                           drop=True).astype(int) 
    #print(archive.isel(time=initial_i+xr.DataArray(leads,dims='L')).dims)
    #out = out.rename({'time':'M'}).assign_coords({'M': np.arange(M)})
    
    return archive.isel(time=initial_i+xr.DataArray(leads,dims='L')).assign_coords(L = leads)

def analogue_ensemble(init_pca,
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
    nov_pca = pca.where(pca['time.month'].isin(initial_month),drop=True)
    
    nearly_DPLE_i = []
    #lead_increments = xr.DataArray(lead_times,dims=('L',))
    
    init_pca = init_pca.transpose(...,'mode')
    for init in init_pca: 
        assert len(init.shape) == 1, 'Not sure how this code will go with multidimensional analogues'
        
        year_i = find_analogues(init.isel(mode=mode_slice), #find analogues for this year
                                   nov_pca.isel(mode=mode_slice,time=slice(None,nov_pca.time.shape[0]-max(lead_times))), #from these years
                                   n_members,                                                       #this many of them
                                   weights=weights.isel(mode=mode_slice))
        
        full_i = arg_month_year(pca, #Now work out where those analogues came from originally
                                     nov_pca['time.year'].isel(time=year_i),
                                     initial_month,
                                     ).rename({'time':'M'}) #We've selected times, but as ensemble members

        nearly_DPLE_i.append(pseudo_ensemble(full_i,pca,lead_times))
    
    #Handing back the full pca rather than just the i, because it's less likely to be accidentally used wrong
    return xr.concat(nearly_DPLE_i,'Y')
    
