import numpy as np
import xarray as xr
import warnings
import os
import copy
import time

from .enso_indices import pacific_mask, regrid_pacific_mask

#My local fork of the eofs package that can deal with multiindexes
#That this mess is needed to import it is a little ridiculous
import sys
#Assume the updated-eofs-pkg is in the same directory as ensemble-analogue-predictability
sys.path.insert(0,'/'.join(__file__.split('/')[:-3])+'/') 
import updated_eof_pkg.lib.eofs as eof
import updated_eof_pkg.lib.eofs.xarray as eofxr
sys.path = sys.path[1:]


def prepare_for_eof(data,
                    scaling = None,
                    space_dims = ('nlat','nlon','var'),
                    time_dims = ('time',),
                    trim_coords = {'TLAT':slice(-10,10)},
                    trim_to_pacific = True,
                    pacific_new_grid = None,
                   ):
    
    '''
    Take some data and clean it up before you run an eof analysis through it
    
    space_dims should logically start with latitude, because it'll become latitude, but I don't
    think it should actually matter if you do the eof analysis with nlon becoming latitude or whatever
    It might try weight by latitude, but I'm pretty sure the examples have the weighting happening earlier
    time_dims is just in case you want to eof an ensemble
    
    trim_coords and trim_to_pacific subset the spacial area of the data'''
    
    #Rescale variables so that they equally contribute to EOFs
    if scaling is None:
        scaling = data.std([d for d in data.dims if d != "var"])
    data = data/scaling
    data['scaling'] = scaling #Assign as a coord so it survives the EOF, then becomes a variable later
    
    #Set the coordinates to be unchanging before subsetting
    for d in space_dims: 
        data = data.assign_coords({d:data[d].data})
        
    #Subset data to the pacific
    if trim_to_pacific:
        if pacific_new_grid is None:
            data = data.where(pacific_mask.astype(bool), drop =True)
        else:
            data = data.where(regrid_pacific_mask(pacific_new_grid).astype(bool), drop =True)
    
    #Subset data along whatever dimensions you want
    for c in trim_coords: #I suspect I'm only going to use this for TLAT, but it's here nonetheless
        start, stop = (trim_coords[c].start, trim_coords[c].stop)
        if not (start is None):
            data = data.where(data[c]>start, drop=True)
        if not (stop  is None):
            data = data.where(data[c]<stop,  drop=True)
            
#    # I suggest the alternative subsetting technique, because it'll work for longitude as well
#    for c in trim_coords: #I suspect I'm only going to use this for TLAT, but it's here nonetheless
#        start, stop = (trim_coords[c].start, trim_coords[c].stop)
#        if start is None:
#            start = -365
#        if stop is None:
#            stop = 365
#        if start<stop:
#            data = data.where((data[c]>start) & (data[c]<stop), drop=True)
#        else:
#            data = data.where((data[c]>start) | (data[c]<stop), drop=True)
        
    #Do some massaging for the EOFs package
    if 'latitude' in data.coords:
        data = data.rename({'latitude':'orig_latitude_coord'})
    if 'longitude' in data.coords:
        data = data.rename({'longitude':'orig_longitude_coord'}) #### CHECK AND FIX!!!!
        
    if not (space_dims[0] == 'latitude'):
        data = data.rename({space_dims[0]:'latitude'})
    if not (space_dims[1:] =='longitude'):
        data = data.stack({'longitude':space_dims[1:]})
    if len(time_dims) == 1:
        if time_dims[0] != 'time':
            data = data.rename({time_dims[0]:'time'})
    else:
        if 'time' in time_dims:
            data = data.rename({'time':'orig_time'}) #Updated 20/12/23 to address SMILEs
            new_time_dims = list(copy.copy(time_dims))
            new_time_dims[new_time_dims.index('time')] = 'orig_time'
            data = data.stack({'time':new_time_dims})
        else:
            data = data.stack({'time':time_dims})
    data = data.fillna(0)
    
    return data.transpose('time',...)

def calculate_eof(eof_ready_data,
                  n_eofs,
                  lat_name = 'nlat',
                  keep_coords = ('TLONG','TLAT'),
                  scaling_trim = {'nlon':0}, #Cheat's dimension reduction
                 ):
    '''Take some preprepared data and actually run an eof solver over it, 
    then tidy things up nicely back into an xarray dataset and give it back'''
    
    #Strip the scaling off coords before it becomes a problem later
    scaling = eof_ready_data.unstack().scaling.reset_coords('scaling',drop=True).isel(scaling_trim)
    eof_ready_data = eof_ready_data.reset_coords('scaling',drop=True)
    
    
    solver = eofxr.Eof(eof_ready_data)
    eof = solver.eofsAsCovariance(neofs=n_eofs)
    pca = solver.pcs(npcs=n_eofs, pcscaling=1)
    
    variance_fraction = solver.varianceFraction(neigs=n_eofs)
    
    #I'm not sure I'll every need these two bits, so maybe delete them at some point?
    variance_fraction_error = solver.northTest(neigs=n_eofs, vfscaled=True)
    total_variance = solver.totalAnomalyVariance()
    
    eof_xr = xr.Dataset({'eof':eof.unstack(),
                     'pca':pca.unstack(), #Updated 20/12/23 for SMILEs
                     'variance_fraction':variance_fraction,
                     'variance_fraction_error':variance_fraction_error,
                     'total_variance':total_variance,
                     'scaling':scaling
                    })
    
    eof_xr = eof_xr.rename({'latitude':lat_name})
    
    if 'orig_latitude_coord' in eof_xr.coords:
        eof_xr = eof_xr.rename({'orig_latitude_coord':'latitude','orig_longitude_coord':'longitude'})
    
    if 'orig_time' in eof_xr.coords:
        eof_xr = eof_xr.rename({'orig_time':'time'}) #Added 20/12/23 for SMILEs
     
    
    for c in keep_coords:
        if c == 'latitude':
            eof_xr = eof_xr.assign_coords({c:(eof_ready_data['orig_latitude_coord']
                                              .unstack()
                                              .rename({'latitude':lat_name})
                                              .rename({'orig_latitude_coord':'latitude','orig_longitude_coord':'longitude'}))})
        elif c == 'longitude':
            eof_xr = eof_xr.assign_coords({c:(eof_ready_data['orig_longitude_coord']
                                              .unstack()
                                              .rename({'latitude':lat_name})
                                              .rename({'orig_latitude_coord':'latitude','orig_longitude_coord':'longitude'}))})
        else:
            print(c,eof_ready_data[c])
            eof_xr = eof_xr.assign_coords({c:eof_ready_data[c].unstack().rename({'latitude':lat_name})})
    

    return eof_xr

def trim_to_eof(ss,eof_stats, 
                trim_dim = ('nlon','nlat','var',),
                check_coord = ('TLONG','TLAT',),
                ):
    '''Take a bunch of data and some eofs that you want to project the data onto, and throw away all of
    the data which isn't a variable in the eofs
    ss is the data you're going to project later
    eof_stats is what you'll be projecting it onto
    
    ss is trimmed to the values of trim_dims in eof_stats
    We then double check that the check_coords also line up nicely
    All these dimensions/coordinates should be present on both, 
         and ideally all dims are coords too
    '''
    for d in trim_dim: #Trim data
        ss = ss.sel({d:eof_stats[d]})
      
    for c in check_coord: #Double check all the coordinates line up nicely
        assert ((ss[c]-eof_stats[c])**2).sum()<10**-6, "Looks like coordinate "+c+" doesn't match on the data and EOF stats.\n Check that all dimensions, especially on eof_stats, are also coordinates"
    
    return ss

def project_onto_eof(data, eof, filename=None, space_dims = ('nlon','nlat'),time_dims = ('Y','L','M')):
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

def project_onto_EOF(**kwargs):
    warnings.warn('I\'ve renamed this function project_onto_eof. Please use the updated version')
    return project_onto_eof(kwargs)
                
def redimensionalise(pca,eof):
    '''Take a reduced dimension set of data and reinflate it to the full thing
    
    pca is something in the dimension space defined by eof_stats'''
    
    return (eof*pca).sum('mode')

def loc_string(trim_to_pacific,
               trim_coords,
              var_list):
    '''How to shove those three variables together consistently, for the sake of naming saved EOFs'''

    return (str(trim_to_pacific)+'P_' +
            '_'.join([str(trim_coords[k].start)+'_'+str(trim_coords[k].stop)+k for k in trim_coords])+
            '_'+'_'.join(var_list))

def calculate_weighted_eof(weighted_ss,
                           trim_to_pacific,
                           pacific_new_grid,
                           trim_coords,
                           weightfolder_name,
                           data_name,
                           space_dims=('nlat','nlon','var'),
                           scaling_trim = {'nlon':0},
                           keep_coords=('TLONG','TLAT'),
                           time_dims = ('time',),
                           n_modes=50):
    ''' Take a dataset (ie model or observational sst or ssh) which has already been weighted grid-wise,
    trim it down to the area you want, and EOF it. Save this EOF to file
    
    the weight multiplication happens outside this function because I think I can shave a factor of 2 
    off by not doing it several times for different regions
    
    
    weighted_ss       - whatever you want to EOF. This should have been multiplied by weights and
                        temporally trimmed to a short-ish timeseries, possibly of only one calendar month
    trim_to_pacific   - boolean "do you want to exclude everything not Pacific"
    trim_coords       - a dictionary of coordinates to trim the data before EOFing ie {'TLAT':slice(-10,10)}
    weightfolder_name - Wherever you pulled the weights from, ideally 
                        (ie /glade/.../pca_variations/correlation_weight/CESM2_DJF_NINO34_L10/)
    data_name         - Name of the other part of weighted_ss (ie CESM2)    
    n_modes           - how many EOFs to calculate. Even 50 is way under how much data you would have without
                          dimension reduction
                          '''
    
    
    #Output path
    folder = (weightfolder_name+'/'
                +data_name+'_'
                +loc_string(trim_to_pacific,trim_coords,weighted_ss['var'].data))
    filename = (folder
                +'/eof.nc'
               )
    
    if not os.path.isdir(folder):
        os.mkdir(folder)
    
    
    eof_ready_data = prepare_for_eof(weighted_ss,
                                        time_dims=time_dims,
                                        trim_to_pacific=trim_to_pacific,
                                        pacific_new_grid = pacific_new_grid,
                                        space_dims=space_dims,
                                        trim_coords=trim_coords).squeeze()
    eof_ready_data.load() #Can't do the EOF analysis with dask arrays, for some reason?
    
    eof = calculate_eof(eof_ready_data,
                           n_modes,
                        lat_name=space_dims[0],
                        scaling_trim=scaling_trim,
                        keep_coords=keep_coords)
    
    eof.to_netcdf(filename)
    
    return

def calculate_trimmed_weighted_eof(weighted_ss,
                           weightfolder_name,
                           data_name,
                           space_dims=('nlat','nlon','var'),
                           scaling_trim = {'nlon':0},
                           keep_coords=('TLONG','TLAT'),
                           time_dims = ('time',),
                           n_modes=50):
    ''' Take a dataset (ie model or observational sst or ssh) which has already been weighted grid-wise and trimmed, and EOF it. Save this EOF to file.
    Same as above function, except the trimming is expected to be outside
    
    
    weighted_ss       - whatever you want to EOF. This should have been multiplied by weights and
                        temporally trimmed to a short-ish timeseries, possibly of only one calendar month
    weightfolder_name - Wherever you pulled the weights from, ideally 
                        (ie /glade/.../pca_variations/correlation_weight/CESM2_DJF_NINO34_L10/)
    data_name         - Name of the other part of weighted_ss (ie CESM2-LE)    
    n_modes           - how many EOFs to calculate. Even 50 is way under how much data you would have without
                          dimension reduction
                          '''
    
    
    #Output path
    folder = (weightfolder_name+'/'
                +data_name+'_'
                +'_'.join(weighted_ss['var'].data))
    filename = (folder
                +'/eof.nc'
               )
    #print(folder)
    if not os.path.isdir(folder):
        os.mkdir(folder)
    
    
    eof_ready_data = prepare_for_eof(weighted_ss,
                                        time_dims=time_dims,
                                        trim_to_pacific= False,
                                        pacific_new_grid = None,
                                        space_dims=space_dims,
                                        trim_coords={}).squeeze()
    eof_ready_data.load() #Can't do the EOF analysis with dask arrays, for some reason?
    
    eof = calculate_eof(eof_ready_data,
                           n_modes,
                        lat_name=space_dims[0],
                        scaling_trim=scaling_trim,
                        keep_coords=keep_coords)
    
    eof.to_netcdf(filename)
    
    return

def calculate_weighted_pca(weighted_ss,
                           eof_folder,
                           data_name, #Data being projected!!
                           n_modes=50,
                           space_dims=('nlon','nlat','var'),
                           keep_coords = ('TLONG','TLAT'),
                          time_dims = ('time',)):
    ''' Take a dataset (ie model or observational sst or ssh) which has already been weighted grid-wise,
    trim it down to the area you want, and EOF it. Save this EOF to file
    
    the weight multiplication happens outside this function because I think I can shave a factor of 2 
    off by not doing it several times for different regions
    
    
    weighted_ss       - whatever you want to EOF. This should have been multiplied by weights and
                        temporally trimmed to a short-ish timeseries, possibly of only one month
    eof_folder        - wherever the eof is (and, consequentially, wherever you want to put the pca)
    data_name         - whatever weighted_ss contains, in addition to weights (ie. CESM2)
    n_modes           - how many EOFs to calculate. Even 50 is way under how much data you would have without
                          dimension reduction (looks like it's not used? so maybe doesn't need to be here?)
                          '''
    
    
    #Output path
    t0 = time.time()
    eof = xr.load_dataset(eof_folder+'eof.nc')
    
    trim_model_ss = trim_to_eof(weighted_ss,eof.eof,
                                trim_dim=space_dims,
                               check_coord=keep_coords)
    
    pca = project_onto_eof(trim_model_ss.squeeze()/eof.scaling,
                                  eof.eof,
                                  space_dims = space_dims,
                                  time_dims=time_dims)
    
    pca.rename('pca').to_netcdf(eof_folder+'pca_'+data_name+'.nc')
    

def fast_calculate_weighted_pca(b,
                           eof_folder,
                           data_name, #Data being projected!!
                           space_dims=('nlon','nlat','var'),
                           keep_coords = ('TLONG','TLAT'),
                          time_dims = ('time',),
                               nan_warning = True):
    ''' Take a dataset (ie model or observational sst or ssh) which has already been weighted grid-wise,
    trim it down to the area you want, and EOF it. Save this EOF to file
    
    this has been optimised for casper, which probably has problems with memory, and so it might not be
    as good on another system. Basically, I spent a whole day getting all the "where" and "stack" operations
    out of the innermost for loop
    
    
    weighted_ss       - whatever you want to EOF. This should have been multiplied by weights and
                        temporally trimmed to a short-ish timeseries, possibly of only one month
    eof_folder        - wherever the eof is (and, consequentially, wherever you want to put the pca)
    data_name         - whatever weighted_ss contains, in addition to weights (ie. CESM2-LE_30P30I_0-10M)
                          '''
    
    
    #Output path
    eof = xr.load_dataset(eof_folder+'eof.nc')
    
    #Rescale according to eof (all other b modification happens a loop level up)
    b = b.squeeze()/eof.scaling.broadcast_like(b.isel(time_stack=0).unstack()).stack({'loc':space_dims})
        
    #Set up linear algebra
    A = eof.eof.stack({'loc':space_dims}
                 ).transpose('loc','mode').to_numpy()
    mode_coord = eof.mode
    
    time_stack = b.time_stack
    
    if (np.sum(np.isnan(b))>0):
        if nan_warning:
            warnings.warn('Replacing nans with 0 before linear algebra. You ought to deal with them earlier though...')
        b = b.fillna(0)

    b = b.data
    
    #Actual projection
    ataat = np.linalg.inv(A.T@A)@A.T
    x = ataat@b
    
    #Reassemble into xarray dataset
    pca = xr.DataArray(x,dims=('mode','time_stack'),coords={'mode':eof.mode,
                                                  'time_stack':time_stack}).unstack().rename('pca')
    
    pca.rename('pca').to_netcdf(eof_folder+'pca_'+data_name+'.nc')

    
    
def save_weighted_eof_set(ss,
                           #weights,
                           trim_to_pacific,
                           pacific_new_grid,
                           trim_coords,
                           weightfolder_name,
                           data_name,
                           keep_coords = ('TLAT','TLONG'),
                           space_dims=('nlon','nlat','var'),
                           scaling_trim={'nlat':0},
                           n_modes=50):
    ''' Take a dataset (ie model or observational sst or ssh) and multiply it by a set of weights,
    then pass to a function to calculate the EOF and dump to file
    
    

    ss                - whatever you want to EOF. Should be temporally trimmed
    #weights           - The things you're multiplying data by (ie correlation maps)
    trim_to_pacific   - A LIST OF boolean "do you want to exclude everything not Pacific"
    trim_coords       - A LIST OF a dictionary of coordinates to trim the data before EOFing ie {'TLAT':slice(-10,10)}
    weightfolder_name - Wherever you pulled the weights from, ideally 
                        (ie /glade/.../pca_variations/correlation_weight/CESM2_DJF_NINO34_L10/)
    data_name         - Name of the other part of weighted_ss (ie CESM2)    
    n_modes           - how many EOFs to calculate. Even 50 is way under how much data you would have without
                          dimension reduction
                          '''
    assert 'var' in ss.dims, 'Need to have a "var" dimension otherwise weights will accidentally generate one'
    weights = xr.load_dataarray(weightfolder_name+'weights.nc')
    weighted_ss = (weights*ss).load()
    
    assert type(trim_to_pacific) is list, 'need things to step through'
    assert type(trim_coords) is list, 'need things to step through'
    
    for i in range(len(trim_to_pacific)):
        
        calculate_weighted_eof(weighted_ss.isel(time=slice(None,300)),
                               trim_to_pacific = trim_to_pacific[i],
                               pacific_new_grid = pacific_new_grid[i],
                               trim_coords = trim_coords[i],
                               weightfolder_name = weightfolder_name,
                               scaling_trim=scaling_trim,
                               data_name = data_name,
                               n_modes=n_modes,
                               space_dims=space_dims,
                               keep_coords=keep_coords,
                              )
        
        eof_folder = (weightfolder_name+'/'
                +data_name+'_'
                +loc_string(trim_to_pacific[i],trim_coords[i],ss['var'].data)
                +'/')
        
        calculate_weighted_pca(weighted_ss,
                               eof_folder=eof_folder,
                               data_name = data_name,
                               n_modes=n_modes,
                               space_dims=space_dims,
                               keep_coords=keep_coords,
                              )
        
        