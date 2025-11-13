import numpy as np
#import matplotlib.pyplot as plt
import xarray as xr
# import cftime
#from xhistogram.xarray import histogram
# import scipy.stats
# import warnings
# import time

import sys
sys.path.append('/glade/u/home/jjeffree/ensemble-analogue-predictability/')
import predictability_tools as pt

time_dims = ('time','SMILE_M')

correlation_member_trim = lambda x: x.isel(SMILE_M = slice(None,10))
eof_member_trim = lambda x: x.isel(SMILE_M = slice(None,4))

leads = np.arange(37) #lead time ####np.array((0,6))#
init_months = np.arange(1,13) #Was 1,13, has been tweaked to finish running the eof script ####np.array((4,10))#

# For the correlations

def calc_corr_index(ss):
    return pt.average_region(ss.sel(var='tos'),pt.nino34_region,
                                lon_coord = 'lon', lat_coord ='lat',lon_dim='lon',lat_dim='lat')
corr_index_name = 'NINO34'

outfolder_loc = '/glade/derecho/scratch/jjeffree/pca_variations/area_correlation_weight/' ####
overwrite_correlation = False

corr_chunks = {'var':1,'lon':32}

# For the EOFs

def weight_folder_name_func(data_name,init_month,lead):
    return (outfolder_loc+data_name+'_I'+str(init_month)+'_'+corr_index_name+'_L'+str(lead)+'/')

calculate_eof_kwargs=dict(space_dims=('lat','lon','var'),
                               scaling_trim={'lon':0},   
                               keep_coords=[], #Turns out this only applies to extra coordinates, and not if it's on a regular grid where lat and lon are dimensions
                               n_modes=100,
                               time_dims = ('time','SMILE_M'))

# For the PCAs

calculate_pca_kwargs=dict(space_dims=('lat','lon','var'), 
                          time_dims = ('time','SMILE_M'),
                          nan_warning=False,
                         )
space_dims = ('lat','lon','var') # These turn out to be important for before the pca is passed through to the funciton
#check_coord = ('lat','lon')

# For the actual analogue forecasts
pca_step_n = 10 # How many ensemble members are in each pile for the pca analysis. 
# Not actually used by pca; used by analogues reading in the pca


analogue_output_folder = '/glade/work/jjeffree/results/area_corr/base/' # Warning: the last folder here is often overwritten by analogue scripts
trim_to_pacific = [False]
pacific_regrid = [None]
trim_coords = [{}]
n_analogues= 15
lib_size=5 #In ensemble members

analogue_time_slice = {'CESM2-LE_025':slice('1855','1945'),
                       'ACCESS-ESM1-5':slice('1855','1945'),
                       'MPI-GE':slice('1855','1945'),
                       'MIROC6':slice('1855','1945'),
                       'CanESM5':slice('1855','1945'),
                       'IPSL-CM6A-L':slice('1855','1945'),
                       'MIROC-ES2L':slice('1855','1945'),
                       'ERSSTv5':slice(None,'2021'),
                       'GFDL-ES2M':slice('1866','1956'),
                       'MPI-CMIP6':slice('1855','1945'),
                       'GFDL-CM2-1':slice('0005','0095'),
                       'CESM1_pi':slice('0405','0495'),
                       
                       'CESM2-LE_nomean':slice('1855','1945'),
                       'ACCESS-ESM1-5_nomean':slice('1855','1945'),
                       'MPI-GE_nomean':slice('1855','1945'),
                       'MIROC6_nomean':slice('1855','1945'),
                       'CanESM5_nomean':slice('1855','1945'),
                       'IPSL-CM6A-L_nomean':slice('1855','1945'),
                       'MIROC-ES2L_nomean':slice('1855','1945'),
                       'GFDL-ES2M_nomean':slice('1866','1956'),
                       'MPI-CMIP6_nomean':slice('1855','1945'),
                       'EC-Earth3_tos_nomean':slice('1855','1945'),
}

lib_dim_chunk_size = 115 #Should be the number of years in a library divided by the number of cores, plus a small buffer
# Used in calculating distance, getting this right gives you a ~10-300% time saving over various levels of wrong
