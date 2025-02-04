''' Make some analogue forecasts, using pre-calculated eofs, save everything
    1st argument is the config file
    2nd argument is the data used, i.e. "ACCESS-ESM1-5" (perfect model, ACCESS)
        or "ERSSTv5,ACCESS-ESM1-5" (using ACCESS to predict ERSST)
        or "ERSSTv5,ACCESS-ESM1-5,ERSSTv5" (using ACCESS to predict ERSST, with correlations/eofs from ERSST)
    3rd argument is the masks being used (i.e. "30P,30P30A")
    4th argument is variables being used (i.e. "tos,zos")
    5th argument is an integer; which of the libraries are being used. I expect the batch job to use all of these

    6th argument is a vector of lead times e.g "6,12,18"
    7th argument is a vector of initialisation months e.g. "1,7,11"

    branched from analogue_forecasting2 10th December 2024. 
    Changed to save all analogues from a set, but not to bother projecting forwards in time
    Idea is that this can be used for more finicky analysis and exploration

    I want all lead times and months to save to a separate output
'''


import dask
import distributed

if __name__ == "__main__":
    dask.config.set({'distributed.admin.large-graph-warning-threshold':'1024MB'})
    client = distributed.Client(threads_per_worker=1,memory_limit=0)

    import numpy as np
    import xarray as xr
    #import cftime
    import warnings
    import time
    import os

    import sys
    sys.path.append('/glade/u/home/jjeffree/ensemble-analogue-predictability/')
    import predictability_tools as pt

    #The things that might want to be changed all the time
    config_file = sys.argv[1]
    data_name_list = sys.argv[2].split(',')
    if len(data_name_list)==1:
        data_name = data_name_list[0]
        lib_data_name = data_name_list[0]
        corr_data_name = data_name_list[0]
    elif len(data_name_list)==2:
        data_name = data_name_list[0]
        lib_data_name = data_name_list[1]
        corr_data_name = data_name_list[1]
    elif len(data_name_list)==3:
        data_name = data_name_list[0]
        lib_data_name = data_name_list[1]
        corr_data_name = data_name_list[2]
    else:
        raise Exception("only 1-3 data_name values can be passed through (separated by a comma)")
    
    mask_list = sys.argv[3].split(',')
    vars = np.array(sys.argv[4].split(','))
    lib_mi = int(sys.argv[5])

    ###
    local_lead_times = np.array(sys.argv[6].split(','),dtype=int)
    local_init_months = np.array(sys.argv[7].split(','),dtype=int)
    assert not (sys.argv[7] is None), 'Need to specify lead times and init months'

    # Config file - so I can run variants if necessary
    import importlib.util
    spec = importlib.util.spec_from_file_location("args", config_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["args"] = module
    spec.loader.exec_module(module)
    args = sys.modules["args"]
    print("Using config from "+config_file)
    
    print("Lead times: "+", ".join(list(np.array(local_lead_times,dtype=str))))
    print("Init months: "+", ".join(list(np.array(local_init_months,dtype=str))))

    if (lib_mi*args.lib_size+args.lib_size)>pt.n_ensemble_members[lib_data_name]: #If end member (exclusive) is > than number of members
        print('Returning early; not enough ensemble members for this library')
        sys.exit()

    t0=time.time()

    # Read in data you need and calculate relevant indexes
    if not (('GFDL-CM2-1' == lib_data_name) or ('pi' in lib_data_name)):
        assert 'nomean' in lib_data_name, "Have some questions about why you're not taking ensemble mean here"
    
    lib_model_ss = pt.get_025_ss[lib_data_name]() #Used exclusively for getting ensemble member names
    # lib_index = calc_index(lib_model_ss)
    # print('Lib index calculated; '+lib_data_name+'; '+str(time.time()-t0)+' s')

    # if data_name == lib_data_name:
    #     data_index = lib_index
    #     print('Same "truth" data; '+str(time.time()-t0)+' s')
    # else:
    #     data_model_ss = pt.get_025_ss[data_name]()
    #     data_index = calc_index(data_model_ss)
    #     print('Truth index calculated; '+data_name+'; '+str(time.time()-t0)+' s')

        
    # Pick a 500 year library
    psn = args.pca_step_n #Easier to read than the full thing
    n_lib_files = np.ceil(pt.n_ensemble_members[lib_data_name]/psn).astype(int)
    lib_members = lib_model_ss.SMILE_M.isel(SMILE_M = slice(lib_mi*args.lib_size,lib_mi*args.lib_size+args.lib_size))
    lib_pca_trim = lambda x: x.sel(time=args.analogue_time_slice[lib_data_name],SMILE_M = lib_members
                                                                  ).stack({'lib_dim':('SMILE_M','time')})
    #full_lib_time = lib_index.time

    # Use everything else for verification
    n_obs_files = np.ceil(pt.n_ensemble_members[data_name]/psn).astype(int)
    obs_pca_trim = lambda x: x.sel(time=args.analogue_time_slice[data_name]).rename({'SMILE_M':'pred_SMILE_M'})
    #full_obs_time = data_index.time


    for m in mask_list:
        lib_pca_names = [lib_data_name+'_'+m+'_'+str(i*psn)+'-'+str(i*psn+psn)+'M' for i in range(n_lib_files)]
        if n_obs_files>1:
            obs_pca_names = [data_name+'_'+m+'_'+str(i*psn)+'-'+str(i*psn+psn)+'M' for i in range(n_obs_files)]
        else:
            obs_pca_names = [data_name+'_'+m]

        #output_i = []
        for init_month in local_init_months:
            #output_l = []
            for l in local_lead_times:
                out_filename = args.analogue_output_folder+'detail/'+'_'.join(data_name_list) +'_'+'_'.join(vars)+'/'+m+'_I'+str(init_month)+'_L'+str(l)+'_'+str(lib_mi)+'.nc'
                if not os.path.isdir('/'.join(out_filename.split('/')[:-2])):
                    assert False, 'Need directory '+'/'.join(out_filename.split('/')[:-2]) # I'm not making it manually because I'd rather someone double-checked it was needed
                if not os.path.isdir('/'.join(out_filename.split('/')[:-1])):
                    os.mkdir('/'.join(out_filename.split('/')[:-1])) # Should also throw an error if there's any other problems with this directory existing
                if os.path.isfile(out_filename):
                    warnings.warn('Skipping ' + out_filename)
                    continue
                else:
                    warnings.warn('Attempting to calculate ' + out_filename)

                
                pca_folder = (args.weight_folder_name_func(corr_data_name,init_month,l)+corr_data_name+'_'+m+'_'
                             +'_'.join(vars)
                             +'/')
    
                # Set up the initialisations
                obs_pca = xr.open_mfdataset([pca_folder+'pca_'+opn+'.nc' for opn in obs_pca_names],
                                            combine='nested',
                                            concat_dim=('SMILE_M',)).pca.load()
                obs_pca = obs_pca_trim(obs_pca)
                

                init_i = np.where(obs_pca['time.month']==init_month)[0]
                init_ens = (obs_pca.isel(time=xr.DataArray(init_i,dims='Y')) # Pick out the points where we're starting. 
                                                                             # In many cases this may not do anything
                                    .rename(time='pred_time')                # Separate predicted time from the time later used in archive
                                   )
                # Find me some analogue initialisations
                # Library/archive to find analogues in
                lib_pca = xr.open_mfdataset([pca_folder+'pca_'+lpn+'.nc' for lpn in lib_pca_names],
                                            combine='nested',
                                            concat_dim=('SMILE_M',)).pca.load()
                lib_pca = lib_pca_trim(lib_pca)
                lib_pca = lib_pca.where(lib_pca['time.month'] == init_month,drop=True)
                assert lib_pca.time.shape[0]>0, 'No library. Probably initialisation times don\'t match'
                #print(time.time()-t0)
                assert (np.sum(np.isnan(lib_pca))+np.sum(np.isnan(obs_pca)))==0, 'NaNs in your PCA. FIX'
                weights = xr.load_dataset(pca_folder+'eof.nc').variance_fraction
                distance = ((init_ens-lib_pca.chunk(lib_dim=args.lib_dim_chunk_size))**2*weights).sum('mode').load()
                analogue_i = distance.transpose('lib_dim',...).argsort(axis=0)[:args.n_analogues].reset_index('lib_dim',drop=True).rename({'lib_dim':'M'})
                assert not(('SMILE_M' in analogue_i.coords) or ('time' in analogue_i.coords)), 'Dunno where either came from but could stuff up analogue selection'
                analogue = distance.isel(lib_dim = analogue_i)
                #print(time.time()-t0)
                
                # Do some massaging to get the data back out again tidily
                # Update: We're only returning the analogues and not the forecast times here, because it's simpler and this is data for someone to play with later
                # analogue_forecast_time = full_lib_time.shift(time=-l).sel(time=analogue.time)
                # init_forecast_time = full_obs_time.shift(time=-l).sel(time=init_ens.pred_time)
            
                #print(time.time()-t0)
                forecast = (analogue
                 .drop_vars(('lib_dim','time','pred_time'))
                 .assign_coords({
                             'init_time':init_ens.pred_time.drop('pred_time'),
                             'analogue_init_time':analogue.time.drop(('lib_dim','pred_time','pred_SMILE_M'))
                             }
                               ).rename('analogue_distance').rename({'SMILE_M':'analogue_SMILE_M'})
                 .assign_coords({'L':l}).expand_dims('L')
                 .assign_coords({'init_month':init_month}).expand_dims('init_month')
                            )
                #output_l.append(forecast)

                if data_name == lib_data_name:
                    forecast = forecast.where(~forecast.pred_SMILE_M.isin(lib_members)) ### drop self-referential analogues

                out_data = xr.Dataset({'distance':forecast}
                             ).expand_dims({'mask':(m,),'lib_mi':(lib_mi,)})#.drop_vars(('var'))
        
                out_data.to_netcdf(out_filename)
                print(out_filename.split('/')[-1],str(time.time()-t0))
        
                #output_i.append(xr.concat(output_l,'L').assign_coords({'init_month':init_month}).expand_dims('init_month'))
                warnings.warn(str(lib_mi)+' '+str(init_month)+' '+str(time.time()-t0))
    
        #out =  xr.concat(output_i,'init_month')
        #ver = data_index.sel(time=out.pred_time,SMILE_M=out.pred_SMILE_M)
        #an_forecast = lib_index.sel(time=out.analogue_time,SMILE_M=out.analogue_SMILE_M)
    
        #trim_forecast = (an_forecast.mean('M'))
        # if data_name == lib_data_name:
        #     trim_forecast = trim_forecast.where(~trim_forecast.pred_SMILE_M.isin(lib_members)) ### drop self-referential analogues
        # if 'SMILE_M' in ver.coords:
        #     ver = ver.drop_vars('SMILE_M')
        
    print('done')

