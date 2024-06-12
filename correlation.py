''' Calculate correlation between an index and a bunch of fields
    Should work fine with observational data, though time_dims 
        and correlation_member_trim will need changing in the config file, 
        though tread carefully because I haven't rigorously checked this 
        functionality
    1st argument is the path of the config file
    2nd argument is what data is being used  (one of my names, 
      i.e. MPI-GE, ACCESS-ESM1-5, CESM2-LE_025, etc)
   
 Jemma - 21/12/23
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

    # My relevant functions
    
    import importlib.util
    
    sys.path.append('/glade/u/home/jjeffree/ensemble-analogue-predictability/')
    import predictability_tools as pt

    # Config file - so I can run variants if necessary
    spec = importlib.util.spec_from_file_location("args", config_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["args"] = module
    spec.loader.exec_module(module)
    args = sys.modules["args"]
    print("Using config from "+config_file)

    t0 = time.time()

    # Load model data
    full_model_ss = pt.get_025_ss[data_name]()
    model_ss = args.correlation_member_trim(full_model_ss).load()
    print('Model data aquired; '+data_name+"; "+str(time.time()-t0)+' s')

    # Calculate index for correlations
    if type(args.calc_corr_index) == type(np.sum): #Yeah, I'm not happy about type(np.sum) either. We're fishing for "is it a function"
        corr_index = args.calc_corr_index(model_ss)
    else:
        corr_index = args.calc_corr_index

    print('Correlation index calculated; '+args.corr_index_name+'; '+str(time.time()-t0)+' s')
    print('Writing to'+ args.outfolder_loc)

    for init_month in args.init_months:
        month_model_ss = model_ss.where(model_ss['time.month']==init_month,drop=True).chunk(args.corr_chunks)
        month_corr_index = xr.concat([corr_index.shift(time=-l).where(corr_index['time.month']==init_month,drop=True)
                                      for l in args.leads],dim='L').assign_coords(L=args.leads)

        with warnings.catch_warnings():
            warnings.simplefilter('once')
            out = xr.corr(month_corr_index,
                                  month_model_ss,
                                  dim=(args.time_dims)).load()

        for l in args.leads:
            out_folder = args.weight_folder_name_func(data_name,init_month,l)
            if os.path.isdir(out_folder):
                if not args.overwrite_correlation:
                    print('skipping l='+str(l)+' init='+str(init_month))
                    continue
            else:
                os.mkdir(out_folder) # Should throw an error if there was something there
            out.sel(L=l).to_netcdf(out_folder+'/weights.nc')
        print('Correlation init month ',init_month,time.time()-t0)
    print('Done, '+str(time.time()-t0)+' s')
