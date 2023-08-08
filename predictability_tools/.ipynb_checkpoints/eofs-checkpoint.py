import numpy as np
import xarray as xr
import warnings

from .enso_indices import pacific_mask

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
        data = data.where(pacific_mask.astype(bool), drop =True)
    
    #Subset data along whatever dimensions you want
    for c in trim_coords: #I suspect I'm only going to use this for TLAT, but it's here nonetheless
        start, stop = (trim_coords[c].start, trim_coords[c].stop)
        if not (start is None):
            data = data.where(data[c]>start, drop=True)
        if not (stop  is None):
            data = data.where(data[c]<stop,  drop=True)
        
    #Do some massaging for the EOFs package
    data = data.rename({space_dims[0]:'latitude'}).stack({'longitude':space_dims[1:]})
    if len(time_dims) == 1:
        data = data.rename({time_dims[0]:'time'})
    else:
        data = data.stack({'time':time_dims})
    data = data.fillna(0)
    
    return data

def calculate_eof(eof_ready_data,
                  n_eofs,
                  lat_name = 'nlat', #Probably always the case
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
                     'pca':pca,
                     'variance_fraction':variance_fraction,
                     'variance_fraction_error':variance_fraction_error,
                     'total_variance':total_variance,
                     'scaling':scaling
                    })
    
    for c in keep_coords:
        eof_xr = eof_xr.assign_coords({c:eof_ready_data[c].unstack()})

    return eof_xr.rename({'latitude':'nlat'})

def trim_to_eof(ss,eof_stats, 
                trim_dim = ('nlon','nlat','var',),
                check_coord = ('TLONG','TLAT',)
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