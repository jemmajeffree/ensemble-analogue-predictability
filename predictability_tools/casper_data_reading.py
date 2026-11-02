from .temporal import *
import xarray as xr
import numpy as np
import glob
import warnings
import os

get_025_ss = {} # Dictionary lookup for how to read in data from Nicola's archive

def SMILE_means(data,filename,zos_var='zos',lat_var='lat',M_var='SMILE_M'):
    ''' Calculate and save some means that get in the way of the signal'''

    #Seasonal cycle
    seasonal_mean = (data).groupby('time.month').mean().mean(M_var).load() #this order of operations because of files

    if zos_var is None:
        zos_global_mean = np.nan
    else:
        #Total volume in ocean
        lat_weight = np.cos(np.deg2rad(data[lat_var]))
        zos_global_mean = ((strip_climatology(data,clim=seasonal_mean).sel(var=zos_var) *lat_weight).sum(('lat','lon'))
                           /((~np.isnan(data.isel(SMILE_M=0,time=0)).sel(var=zos_var))*lat_weight).sum(('lat','lon'))).load()


    out_means = xr.Dataset({'seasonal_mean':seasonal_mean,
                            'zos_global_mean':zos_global_mean})
    out_means.to_netcdf(filename)

def strip_ensemble_mean(data,filename,M_var='SMILE_M'):
    '''A quick wrapper to pull the ensemble mean off anything,
    specifically so that I can check what difference it makes to the CanESM5'''

    if os.path.isfile(filename):
        ensemble_mean = xr.load_dataset(filename).ensemble_mean
    else:
        ensemble_mean = data.mean(M_var).load()

        out_means = xr.Dataset({'ensemble_mean':ensemble_mean})
        out_means.to_netcdf(filename)
    return data-ensemble_mean



def get_model_regrid_025_ss(data_name,
                            location,
                            time_slice,
                            member_names,
                           middle_bit,
                           var_list,
                           tail,
                           ):

    ss = []
    
    for var in var_list:
        filepaths = [location.format(var=var)+'/'+var+middle_bit+mn+tail for mn in member_names]
    
        ss.append(xr.open_mfdataset(filepaths,
                            coords='minimal',
                            compat='override',
                            combine = 'nested',
                            concat_dim = ('SMILE_M'),
                            preprocess = lambda x: x[var].sel(time=time_slice),
                            chunks = {'lat':-1,'lon':-1,'time':-1,'SMILE_M':1},
                           parallel = True))
    
    
    full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).assign_coords({'SMILE_M':member_names})

    means_file = '/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/'+data_name+'_025.nc'
    if not(os.path.isfile(means_file)):
        SMILE_means(full_model_ss,means_file) ###

    #Strip seasonal variability
    seasonal_mean = xr.load_dataset(means_file).seasonal_mean
    full_model_ss = strip_climatology(full_model_ss,clim=seasonal_mean)

    #Strip global mean
    zos_global_mean = xr.load_dataset(means_file).zos_global_mean
    full_model_ss = full_model_ss.where(~(full_model_ss['var']=='zos'),full_model_ss-zos_global_mean)
    
    expected_dims = ('var','SMILE_M','time','lat','lon')
    for d in full_model_ss.dims:
        if d not in expected_dims:
            full_model_ss = full_model_ss.squeeze(d,drop=True)
    return full_model_ss

get_025_ss['ACCESS-ESM1-5'] = lambda: get_model_regrid_025_ss(data_name='ACCESS-ESM1-5',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/ACCESS-ESM1-5/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,41,dtype=int).astype(str),
                           middle_bit = '_Omon_ACCESS-ESM1-5_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025_185001-201412.nc')

# DO NOT USE A FOR LOOP TO GENERATE THIS KIND OF THING BECAUSE THE 
# LAMBDAS DON'T RUN (AND USE VARIABLES) UNTIL AFTER THE FOR LOOP AS 
# EXITED SO THEY ALL USE THE FINAL VALUE FROM THE FOR LOOP
get_025_ss['ACCESS-ESM1-5_nomean'] = lambda : strip_ensemble_mean(get_025_ss['ACCESS-ESM1-5'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/ACCESS-ESM1-5_ensemble_mean.nc')

get_025_ss['CanESM5'] = lambda: get_model_regrid_025_ss(data_name='CanESM5',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/CanESM5/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,41,dtype=int).astype(str),
                           middle_bit = '_Omon_CanESM5_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p2f1_g025_185001-201412.nc')
get_025_ss['CanESM5_nomean'] = lambda : strip_ensemble_mean(get_025_ss['CanESM5'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/CanESM5_ensemble_mean.nc')

get_025_ss['CESM2'] = lambda: get_model_regrid_025_ss(data_name='CESM2',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/CESM2/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,41,dtype=int).astype(str),
                           middle_bit = '_Omon_CanESM5_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p2f1_g025_185001-201412.nc')
get_025_ss['CanESM5_nomean'] = lambda : strip_ensemble_mean(get_025_ss['CanESM5'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/CanESM5_ensemble_mean.nc')


get_025_ss['IPSL-CM6A-LR'] = lambda: get_model_regrid_025_ss(data_name='IPSL-CM6A-LR',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/IPSL-CM6A-LR/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,33,dtype=int).astype(str),
                           middle_bit = '_Omon_IPSL-CM6A-LR_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025_185001-201412.nc')
get_025_ss['IPSL-CM6A-LR_nomean'] = lambda : strip_ensemble_mean(get_025_ss['IPSL-CM6A-LR'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/IPSL-CM6A-LR_ensemble_mean.nc')

get_025_ss['MIROC6'] = lambda: get_model_regrid_025_ss(data_name='MIROC6',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/MIROC6/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,51,dtype=int).astype(str),
                           middle_bit = '_Omon_MIROC6_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025_185001-201412.nc')
get_025_ss['MIROC6_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MIROC6'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/MIROC6_ensemble_mean.nc')

get_025_ss['MIROC-ES2L'] = lambda: get_model_regrid_025_ss(data_name='MIROC-ES2L',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/MIROC-ES2L/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,31,dtype=int).astype(str),
                           middle_bit = '_Omon_MIROC-ES2L_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f2_g025_185001-201412.nc')
get_025_ss['MIROC-ES2L_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MIROC-ES2L'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/MIROC-ES2L_ensemble_mean.nc')

get_025_ss['GFDL-ESM2M'] = lambda: get_model_regrid_025_ss(data_name='GFDL-ESM2M',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/GFDL-ESM2M/',
                            time_slice=slice('1861','1960'),
                            member_names=np.arange(1,31,dtype=int).astype(str),
                           middle_bit = '_Omon_GFDL-ESM2M_historical_rcp85_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1_g025_186101-210012.nc')
get_025_ss['GFDL-ESM2M_nomean'] = lambda : strip_ensemble_mean(get_025_ss['GFDL-ESM2M'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/GFDL-ESM2M_ensemble_mean.nc')

get_025_ss['MPI-ESM'] = lambda: get_model_regrid_025_ss(data_name='MPI-ESM',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/MPI-ESM/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,101,dtype=int).astype(str),
                           middle_bit = '_Omon_MPI-ESM_historical_rcp85_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1_g025_185001-209912.nc')
get_025_ss['MPI-ESM_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MPI-ESM'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/MPI-ESM_ensemble_mean.nc')

get_025_ss['MPI-ESM1-2-LR'] = lambda: get_model_regrid_025_ss(data_name='MPI-ESM1-2-LR',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/MPI-ESM1-2-LR/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,51,dtype=int).astype(str),
                           middle_bit = '_Omon_MPI-ESM1-2-LR_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025_185001-201412.nc')
get_025_ss['MPI-ESM1-2-LR_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MPI-ESM1-2-LR'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/MPI-ESM1-2-LR_ensemble_mean.nc')

get_025_ss['CESM2'] = lambda: get_model_regrid_025_ss(data_name='CESM2',
                            location='/g/data/su28/MMLEAv2/ocean/monthly/{var}/CESM2/',
                            time_slice=slice('1850','1949'),
                            member_names=np.array(['1251.003', '1001.001', '1231.005', '1161.009', '1301.003', '1281.003', '1251.004', '1301.009', '1301.005', '1281.001', '1231.001', '1101.006', '1251.001', '1301.004', '1231.007', '1301.006', '1251.002', '1301.010', '1281.005', '1061.004', '1281.007', '1251.007', '1281.004', '1021.002', '1231.009', '1301.007', '1041.003', '1301.008', '1141.008', '1281.006', '1231.008', '1081.005', '1231.006', '1231.010', '1281.002', '1251.005', '1231.003', '1301.002', '1181.010', '1301.001', '1231.002', '1251.008', '1281.010', '1281.009', '1121.007', '1231.004', '1251.006', '1251.009', '1281.008', '1251.010']), # I DO NOT CARE IF THESE ARE SORTED OR WHATEVER

                           middle_bit = '_Omon_CESM2_cmip6_historical_ssp370_',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025_185001-210012.nc')
get_025_ss['CESM2_nomean'] = lambda : strip_ensemble_mean(get_025_ss['CESM2'](),
'/scratch/x77/jj8842/analogue_asymmetry/SMILE_means/CESM2_ensemble_mean.nc')


## CESM2

n_ensemble_members = {

                      'CESM2-LE_nomean':50,
                      'ACCESS-ESM1-5_nomean':40,
                      'MPI-ESM_nomean':100,
                      'MIROC6_nomean':50,
                      'CanESM5_nomean':40,
                      'IPSL-CM6A-LR_nomean':32,
                      'MIROC-ES2L_nomean':30,
                      'ERSSTv5_nomean':1,
                      'OISST-AVISO_nomean':1,
                      'GFDL-ESM2M_nomean':30,
                      'MPI-ESM1-2-LR_nomean':50,
                      # 'EC-Earth3_tos_nomean':22,


}

# def get_obs_025_ss():

#     data_name = 'OISST-AVISO'
#     var_list=('tos','zos')
#     time_slice = slice('1993-02','2023-05')
#     warnings.warn("Be aware that these aren't rounded years")

#     sst = xr.open_dataset('/glade/work/jjeffree/observations/oisst.mon.mean_025.nc').sst
#     ssh = xr.open_dataset('/glade/work/jjeffree/observations/dataset-satellite-sea-level-global_025.nc').sla
    
#     full_model_ss = xr.concat((sst,ssh),'var').assign_coords({'var':np.array(var_list)}).squeeze()
#     full_model_ss = full_model_ss.sel(time=time_slice).expand_dims('SMILE_M')
    

#     means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
#     if not(os.path.isfile(means_file)):
#         SMILE_means(full_model_ss,means_file) ###

#     #Strip seasonal variability
#     seasonal_mean = xr.load_dataset(means_file).seasonal_mean
#     full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean

#     #Strip global mean
#     zos_global_mean = xr.load_dataset(means_file).zos_global_mean
#     full_model_ss.loc[{'var':'zos'}] -= zos_global_mean.squeeze()

#     return full_model_ss

# def get_ersstv5_025_ss():

#     data_name = 'ERSSTv5'
#     var_list=('tos',)
#     time_slice = slice('1854-01','2023-12')

#     sst = xr.open_dataset('/glade/work/jjeffree/observations/ersstv5.mnmean_025.nc').sst.squeeze()
    
#     full_model_ss = xr.concat((sst,),'var').assign_coords({'var':np.array(var_list)})
#     full_model_ss = full_model_ss.sel(time=time_slice).expand_dims('SMILE_M')
    

#     means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
#     if not(os.path.isfile(means_file)):
#         SMILE_means(full_model_ss,means_file,zos_var=None) ###

#     #Strip seasonal variability
#     seasonal_mean = xr.load_dataset(means_file).seasonal_mean
#     full_model_ss = strip_climatology(full_model_ss,clim=seasonal_mean)

#     return full_model_ss
# get_025_ss['ERSSTv5']=get_ersstv5_025_ss

# def get_obs_CESM2_ss():
#     ''' Observations, but on a CESM2 grid'''
#     assert False, "zos global mean lat weighting isn't sorted out yet. Just use the regridded CESM2"

#     data_name = 'OISST-AVISO'
#     var_list=('tos','zos')
#     time_slice = slice('1993-02','2023-05')
#     warnings.warn("Be aware that these aren't rounded years")

#     sst = xr.open_dataset('/glade/work/jjeffree/observations/oisst.mon.mean_CESM2_grid.nc').sst
#     ssh = xr.open_dataset('/glade/work/jjeffree/observations/dataset-satellite-sea-level-global_CESM2_grid.nc').sla
    
#     full_model_ss = xr.concat((sst,ssh),'var').assign_coords({'var':np.array(var_list)}).squeeze()
#     full_model_ss = full_model_ss.sel(time=time_slice)
    

#     means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
#     if not(os.path.isfile(means_file)):
#         SMILE_means(full_model_ss.expand_dims('SMILE_M'),means_file) ###

#     #Strip seasonal variability
#     seasonal_mean = xr.load_dataset(means_file).seasonal_mean
#     full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean

#     #Strip global mean
#     zos_global_mean = xr.load_dataset(means_file).zos_global_mean
#     full_model_ss.loc[{'var':'zos'}] -= zos_global_mean.squeeze()

#     return full_model_ss