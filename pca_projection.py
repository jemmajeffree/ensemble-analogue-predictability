''' Take the rest of the model data, weight it, and project it 
    onto the eofs calculated from the representative sample

    1st argument is the path of the config file
    2nd argument is what data is being used  (one of my names, 
      e.g. MPI-GE, ACCESS-ESM1-5, CESM2-LE_025, etc, or two 
      separated by commas e.g. ERSSTv5,MPI-GE, where the first data is
      projected onto the second)
    3rd argument is a single mask (e.g. "30P") or list separated by commas 
     (e.g. "30P,30P30A,30P30I") as defined in pt.mask_definitions
    4th argument is whatever variables you're using, separated by commas 
     (e.g. "tos,zos")
    5th & 6th arguments are the start and end ensemble members to project
      in this particular job. Inclusive of start, exclusive of end. If these
      are both zero, then there is no subselection by ensemble member

'''

import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import cftime
from xhistogram.xarray import histogram
import scipy.stats
import warnings
import time
import os
import sys

from dask.distributed import Client

if __name__ == "__main__":
    client = Client(memory_limit=0,threads_per_worker=1)

    config_file = sys.argv[1]
    data_name_list = sys.argv[2].split(',')
    if len(data_name_list)==1:
        data_name = data_name_list[0]
        eof_data_name = data_name_list[0]
    elif len(data_name_list)==2:
        data_name = data_name_list[0]
        eof_data_name = data_name_list[1]
    else:
        raise Exception("only one or two data_name values can be passed through (separated by a comma)")
    
    mask_list = sys.argv[3].split(',')
    vars = np.array(sys.argv[4].split(','))
    Mi_slice = slice(int(sys.argv[5]),int(sys.argv[6]))
    
    # My relevant functions
    sys.path.append('/glade/u/home/jjeffree/ensemble-analogue-predictability/')
    import predictability_tools as pt

    # Config file - so I can run variants if necessary
    import importlib.util
    spec = importlib.util.spec_from_file_location("args", config_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["args"] = module
    spec.loader.exec_module(module)
    args = sys.modules["args"]
    print("Using config from "+config_file)

    if Mi_slice.start>=pt.n_ensemble_members[data_name]: #If there are literally no members
        print('Returning early; no ensemble members')
        sys.exit()
    
    t0=time.time()

    full_model_ss = pt.get_025_ss[data_name]()
    print('Model data read; '+str(time.time()-t0)+' s')

    #Trim to subset of ensemble members, if requested
    if (Mi_slice.start == 0) and (Mi_slice.stop == 0):
        model_ss = full_model_ss
        member_string = ''
    elif Mi_slice.start<Mi_slice.stop:
        model_ss = full_model_ss.isel(SMILE_M=Mi_slice)
        member_string = '_'+str(Mi_slice.start)+'-'+str(Mi_slice.stop)+'M'
    else:
        raise Exception('ensemble member slice is not zero but not increasing')
    
    model_ss = model_ss.sel(var=vars).load()
    print('Model data loaded; '+str(time.time()-t0)+' s')
    print("Ensemble members "+str(Mi_slice))
    print("Variables "+str(model_ss['var'].data))

    for init_month in args.init_months:
        month_model_ss = model_ss.where(((model_ss['time.month']==init_month)
                                               ),drop=True)#.assign_coords({'nlat':model_ss.nlat,'nlon':model_ss.nlon})
        if np.prod(month_model_ss.shape)==0:
            warnings.warn("Skipping month "+str(init_month)+", couldn't find any data")
            continue
        for m in mask_list:
            trim_model_ss=month_model_ss.where(pt.mask_dict[m],drop=True)
            b = trim_model_ss.stack({'loc':args.space_dims,'time_stack':args.time_dims})

            for l in args.leads:
                weightfolder_name = args.weight_folder_name_func(eof_data_name,init_month,l)
                weights = xr.load_dataarray(weightfolder_name+'weights.nc')
                #weights = weights.assign_coords({'nlon':weights.nlon,'nlat':weights.nlat})

                weighted_b = b*weights.stack({'loc':args.space_dims})

                eof_folder = (weightfolder_name+'/'
                                +eof_data_name+'_'+m+'_'
                                +'_'.join(trim_model_ss['var'].data)
                                +'/')

                pt.fast_calculate_weighted_pca(weighted_b,
                                       eof_folder=eof_folder,
                                       data_name = data_name+'_'+m+member_string,
                                       **args.calculate_pca_kwargs
                                      )
            print(init_month, m, time.time()-t0)
