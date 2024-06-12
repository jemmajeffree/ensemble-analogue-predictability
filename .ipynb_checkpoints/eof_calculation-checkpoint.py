''' Take a representative sample of model (or other) data, multiply it by
    precalculated weights (most likely correlations) and calculate the eofs
    of this data. Each month and lead time (affecting weights) has its own eof

    1st argument is the path of the config file
    2nd argument is what data is being used  (one of my names, 
      e.g. MPI-GE, ACCESS-ESM1-5, CESM2-LE_025, etc)
    3rd argument is a single mask (e.g. '30P') as defined in pt.mask_definitions

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
    data_name = sys.argv[2]
    mask = sys.argv[3]
    vars = np.array(sys.argv[4].split(','))
    
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

    t0 = time.time()

    # Load model data
    full_model_ss = pt.get_025_ss[data_name]()

    model_ss = args.eof_member_trim(full_model_ss).sel(var=vars).load()
    warnings.warn('Model data aquired; '+data_name+"; "+str(time.time()-t0)+' s')
    print('Model data aquired; '+data_name+"; "+str(model_ss['var'].data)+'; '+str(time.time()-t0)+' s')

    warnings.warn('Calculating '+mask)
    print(mask)
    
    for init_month in args.init_months:
        month_model_ss = model_ss.where(((model_ss['time.month']==init_month)
                                                   ),drop=True)
        
        masked_model_ss = month_model_ss.where(pt.mask_dict[mask],drop=True)
        for l in args.leads:
            weightfolder_name = args.weight_folder_name_func(data_name,init_month,l)
            weights = xr.load_dataarray(weightfolder_name+'weights.nc')
            weighted_model_ss = masked_model_ss*weights
            assert (model_ss.dims == weighted_model_ss.dims), "weights are changing the dimensions of the data (BAD!!!). Check that you haven't lost the 'var' dim on model_ss"

            pt.calculate_trimmed_weighted_eof(weighted_model_ss,
                               weightfolder_name = weightfolder_name,
                               data_name = data_name+'_'+mask,
                               **args.calculate_eof_kwargs,
                              )
            
        print(init_month, time.time()-t0)
