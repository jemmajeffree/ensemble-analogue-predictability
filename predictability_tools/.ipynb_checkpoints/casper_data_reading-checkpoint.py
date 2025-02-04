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


def get_CESM2_ss():

    ## CHECK UNITS
    model_sst = correct_cesm_date(xr.open_mfdataset(
        '/glade/campaign/collections/cmip/CMIP6/timeseries-cmip6/b.e21.B1850.f09_g17.CMIP6-piControl.001/ocn/proc/tseries/month_1/*SST.*'
    ).SST)
    model_ssh = correct_cesm_date(xr.open_mfdataset(
        '/glade/campaign/collections/cmip/CMIP6/timeseries-cmip6/b.e21.B1850.f09_g17.CMIP6-piControl.001/ocn/proc/tseries/month_1/*SSH.*'
    ).SSH)/100 # centimetres 🤬

    model_ss = xr.concat((model_sst,model_ssh),'var').assign_coords(var=np.array(('sst','ssh')))

    model_ss = declim(model_ss)
    model_ss = model_ss.drop('z_t')
    return model_ss.squeeze()

def get_CESM2_lens_ss():
    data_name = 'CESM2-LE'

    relevant_years = ('185001-185912','186001-186912','187001-187912','188001-188912','189001-189912',
                     '190001-190912','191001-191912','192001-192912','193001-193912','194001-194912')

    first_half_of_filename = np.sort([f.split('/')[-1].split('SST')[0]
                                    for f in glob.glob('/glade/campaign/cgd/cesm/CESM2-LE/timeseries/ocn/proc/tseries/month_1/SST/*185001-185912.nc')])
    member_names = [fhof.split('LE2-')[-1][:8] for fhof in first_half_of_filename]
    ss = []
    var_list = ('SST','SSH')

    for var in var_list:
        filepaths = []
        for ry in relevant_years:
            filepaths.append(['/glade/campaign/cgd/cesm/CESM2-LE/timeseries/ocn/proc/tseries/month_1/'+var+'/'+fhof+var+'.'+ry+'.nc' for fhof in first_half_of_filename])

        ss.append(xr.open_mfdataset(filepaths,
                            coords='minimal',
                            compat='override',
                            combine = 'nested',
                            concat_dim = ('time','SMILE_M'),
                            preprocess = lambda x: x[var],
                           parallel = True))

        assert 'CESM' in data_name,"don't correct time if not CESM"
        ss[-1] = correct_cesm_date(ss[-1])
        
        if var =='SSH':
             ss[-1]= ss[-1]/100

    full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).squeeze().drop('z_t').assign_coords({'SMILE_M':member_names})

    seasonal_mean = xr.load_dataset('/glade/work/jjeffree/SMILE_means/CESM2-LE.nc').seasonal_mean_only
    full_model_ss = full_model_ss-seasonal_mean
    #full_model_ss = declim(full_model_ss)
    #full_model_ss = full_model_ss - full_model_ss.mean('SMILE_M')
    full_model_ss = full_model_ss.assign_coords({'nlat':full_model_ss.nlat,'nlon':full_model_ss.nlon})
    
    return full_model_ss

def get_CESM2_025_lens_ss():
    data_name = 'CESM2-LE_025'
    time_slice = slice('1850','1949')

    first_half_of_filename = np.sort([f.split('tos')[-1].split('i1p1f1')[0]
                                    for f in glob.glob('/glade/campaign/cgd/cas/nmaher/cesm2_lens/Omon/tos/tos_*_g025.nc')])
    member_names = [fhof.split('_r')[-1][:8] for fhof in first_half_of_filename]
    ss = []
    var_list = ('tos','zos')

    

    for var in var_list:
        filepaths = ['/glade/campaign/cgd/cas/nmaher/cesm2_lens/Omon/'+var+'/'+var+fhof+'i1p1f1_g025.nc' for fhof in first_half_of_filename]

        

        ss.append(xr.open_mfdataset(filepaths,
                            coords='minimal',
                            compat='override',
                            combine = 'nested',
                            concat_dim = ('SMILE_M',),
                            preprocess = lambda x: x[var], ####
                            chunks={'time':-1,'lat':-1,'lon':-1,'SMILE_M':1},
                           parallel = True))
        
        if var =='zos':
             ss[-1]= ss[-1]/100 #centimetres
        assert 'CESM' in data_name,"don't correct time if not CESM"
        
        ss[-1] = correct_cesm_date(ss[-1]).sel(time=time_slice) ####
    
    full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).squeeze().drop('z_t').assign_coords({'SMILE_M':member_names})

    means_file = '/glade/work/jjeffree/SMILE_means/CESM2-LE_025.nc'
    if not(os.path.isfile(means_file)):
        SMILE_means(full_model_ss,means_file)
    
    #Strip seasonal variability
    seasonal_mean = xr.load_dataset(means_file).seasonal_mean
    full_model_ss = strip_climatology(full_model_ss,clim=seasonal_mean)
    seasonal_mean.close()#
    
    #Strip global mean
    zos_global_mean = xr.load_dataset(means_file).zos_global_mean
    #full_model_ss.loc[{'var':'zos'}] -= zos_global_mean # Doesn't work in a recent xarray update, weirdly. Can't be bothered finding out why
    #I'm pretty sure this isn't an intented use of "where", but I can't think why it wouldn't work
    full_model_ss = full_model_ss.where(~(full_model_ss['var']=='zos'),full_model_ss-zos_global_mean)
    zos_global_mean.close()#
    
    return full_model_ss
get_025_ss['CESM2-LE_025'] = get_CESM2_025_lens_ss

def get_CESM1_025_SMILE_ss():
    #assert False, 'zos data is currently full of zeros'

    data_name = 'CESM1-LE'
    
    time_slice = slice('1850','1949')
    
    filenames = np.sort([f.split('/')[-1]
                                    for f in glob.glob('/glade/campaign/cgd/cas/nmaher/cesm1_lens/Omon/tos/tos_Omon_CESM1-CAM5_historical_rcp85_r*_g025.nc')])
    member_names = np.arange(40,dtype=int)+1
    middle_bit = '_Omon_CESM1-CAM5_historical_rcp85_r'
    ss = []
    var_list = ('tos','zos')
    
    for var in var_list:
        filepaths = ['/glade/campaign/cgd/cas/nmaher/cesm1_lens/Omon/'+var+'/'+var+middle_bit+str(mn)+'i1p1_192001-210012_g025.nc' for mn in member_names]
    
        ss.append(xr.open_mfdataset(filepaths,
                            coords='minimal',
                            compat='override',
                            combine = 'nested',
                            concat_dim = ('SMILE_M'),
                            preprocess = lambda x: x[var].sel(time=time_slice),
                            
                            parallel = True))

        assert 'CESM' in data_name,"don't correct time if not CESM"
        ss[-1] = correct_cesm_date(ss[-1])
        
        if var =='zos':
             ss[-1]= ss[-1]/100 #centimetres
    
    
    full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).squeeze().assign_coords({'SMILE_M':member_names})

    means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
    if not(os.path.isfile(means_file)):
        SMILE_means(full_model_ss,means_file)

    #Strip seasonal variability
    seasonal_mean = xr.load_dataset(means_file).seasonal_mean
    full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean

    #Strip global mean
    zos_global_mean = xr.load_dataset(means_file).zos_global_mean
    full_model_ss.loc[{'var':'zos'}] -= zos_global_mean

    return full_model_ss

# def get_ACCESS_ESM1_5_025_SMILE_ss():

#     data_name = 'ACCESS-ESM1-5'
    
#     time_slice = slice('1850','1949')
    
#     filenames = np.sort([f.split('/')[-1]
#                                     for f in glob.glob('/glade/campaign/cgd/cas/nmaher/access_lens/Omon/tos/tos_mon_ACCESS-ESM1-5_historical*_g025.nc')])
#     member_names = [fhof.split('_')[4] for fhof in filenames]
#     middle_bit = '_mon_ACCESS-ESM1-5_historical_'
#     ss = []
#     var_list = ('tos','zos')
    
#     for var in var_list:
#         filepaths = ['/glade/campaign/cgd/cas/nmaher/access_lens/Omon/'+var+'/'+var+middle_bit+mn+'_g025.nc' for mn in member_names]
    
#         ss.append(xr.open_mfdataset(filepaths,
#                             coords='minimal',
#                             compat='override',
#                             combine = 'nested',
#                             concat_dim = ('SMILE_M'),
#                             preprocess = lambda x: x[var].sel(time=time_slice),
#                             chunks = {'lat':-1,'lon':-1,'time':-1,'SMILE_M':1},
#                            parallel = True))
    
    
#     full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).squeeze().assign_coords({'SMILE_M':member_names})

#     means_file = '/glade/work/jjeffree/SMILE_means/ACCESS-ESM1-5-LE_025.nc'
#     if not(os.path.isfile(means_file)):
#         SMILE_means(full_model_ss,means_file)

#     #Strip seasonal variability
#     seasonal_mean = xr.load_dataset(means_file).seasonal_mean
#     #full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean
#     full_model_ss = strip_climatology(full_model_ss,clim = seasonal_mean)

#     #Strip global mean
#     zos_global_mean = xr.load_dataset(means_file).zos_global_mean
#     #full_model_ss.loc[{'var':'zos'}] -= zos_global_mean #This breaks with xarray after 2024. No clue why
#     #I'm pretty sure this isn't an intented use of "where", but I can't think why it wouldn't work
#     full_model_ss = full_model_ss.where(~(full_model_ss['var']=='zos'),full_model_ss-zos_global_mean)
    
#     return full_model_ss
# get_025_ss['ACCESS-ESM1-5'] = get_ACCESS_ESM1_5_025_SMILE_ss
    
# def get_ACCESS_ESM1_5_SMILE_ss():
#     '''Old alias'''
#     warnings.warn('Old name for getting data, has been renamed to get_ACCESS_ESM1_5_025_SMILE_ss()')
#     return get_ACCESS_ESM1_5_025_SMILE_ss()

# def get_MPI_025_SMILE_ss():

#     data_name = 'MPI-GE'
    
#     time_slice = slice('1850','1949')
    
#     # filenames = np.sort([f.split('/')[-1]
#     #                                 for f in glob.glob('/glade/campaign/cgd/cas/nmaher/mpi_lens/Omon/tos/tos_mon_ACCESS-ESM1-5_historical*_g025.nc')])
#     member_names = np.char.zfill(np.arange(1,101,dtype=int).astype(str),3)
#     middle_bit = '_Omon_MPI-ESM_historical_rcp85_r'
#     ss = []
#     var_list = ('tos','zos')
    
#     for var in var_list:
#         filepaths = ['/glade/campaign/cgd/cas/nmaher/mpi_lens/Omon/'+var+'/'+var+middle_bit+mn+'i1p1_185001-209912_g025.nc' for mn in member_names]
    
#         ss.append(xr.open_mfdataset(filepaths,
#                             coords='minimal',
#                             compat='override',
#                             combine = 'nested',
#                             concat_dim = ('SMILE_M'),
#                             preprocess = lambda x: x[var].sel(time=time_slice),
#                             chunks = {'lat':-1,'lon':-1,'time':-1,'SMILE_M':1},
#                            parallel = True))
    
    
#     full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).squeeze().assign_coords({'SMILE_M':member_names})

#     means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
#     if not(os.path.isfile(means_file)):
#         SMILE_means(full_model_ss,means_file)

#     #Strip seasonal variability
#     seasonal_mean = xr.load_dataset(means_file).seasonal_mean
#     #full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean
#     full_model_ss = strip_climatology(full_model_ss,clim=seasonal_mean)

#     #Strip global mean
#     zos_global_mean = xr.load_dataset(means_file).zos_global_mean
#     #full_model_ss.loc[{'var':'zos'}] -= zos_global_mean
#     full_model_ss = full_model_ss.where(~(full_model_ss['var']=='zos'),full_model_ss-zos_global_mean)

    # return full_model_ss


# def get_MIROC6_025_SMILE_ss():

#     data_name = 'MIROC6'
    
#     time_slice = slice('1850','1949')

#     member_names = np.arange(1,51,dtype=int).astype(str)
#     middle_bit = '_mon_MIROC6_historical_r'
#     ss = []
#     var_list = ('tos','zos')
    
#     for var in var_list:
#         filepaths = ['/glade/campaign/cgd/cas/nmaher/miroc6_lens/Omon/'+var+'/'+var+middle_bit+mn+'i1p1f1_g025.nc' for mn in member_names]
    
#         ss.append(xr.open_mfdataset(filepaths,
#                             coords='minimal',
#                             compat='override',
#                             combine = 'nested',
#                             concat_dim = ('SMILE_M'),
#                             chunks = {'lat':-1,'lon':-1,'time':-1,'SMILE_M':1},
#                             preprocess = lambda x: x[var].sel(time=time_slice),
#                            parallel = True))
    
    
#     full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).squeeze().assign_coords({'SMILE_M':member_names})

#     means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
#     if not(os.path.isfile(means_file)):
#         SMILE_means(full_model_ss,means_file) ###

#     #Strip seasonal variability
#     seasonal_mean = xr.load_dataset(means_file).seasonal_mean
#     full_model_ss = strip_climatology(full_model_ss,clim=seasonal_mean)
#     #full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean

#     #Strip global mean
#     zos_global_mean = xr.load_dataset(means_file).zos_global_mean
#     #full_model_ss.loc[{'var':'zos'}] -= zos_global_mean
#     full_model_ss = full_model_ss.where(~(full_model_ss['var']=='zos'),full_model_ss-zos_global_mean)

#     return full_model_ss

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
        filepaths = [location+var+'/'+var+middle_bit+mn+tail for mn in member_names]
    
        ss.append(xr.open_mfdataset(filepaths,
                            coords='minimal',
                            compat='override',
                            combine = 'nested',
                            concat_dim = ('SMILE_M'),
                            preprocess = lambda x: x[var].sel(time=time_slice),
                            chunks = {'lat':-1,'lon':-1,'time':-1,'SMILE_M':1},
                           parallel = True))
    
    
    full_model_ss = xr.concat(ss,'var').assign_coords({'var':np.array(var_list)}).assign_coords({'SMILE_M':member_names})

    means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
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
                            location='/glade/campaign/cgd/cas/nmaher/access_lens/Omon/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,41,dtype=int).astype(str),
                           middle_bit = '_mon_ACCESS-ESM1-5_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025.nc')

get_025_ss['MPI-GE'] = lambda: get_model_regrid_025_ss(data_name='MPI-GE',
                            location='/glade/campaign/cgd/cas/nmaher/mpi_lens/Omon/',
                            time_slice=slice('1850','1949'),
                            member_names=np.char.zfill(np.arange(1,101,dtype=int).astype(str),3),
                           middle_bit = '_Omon_MPI-ESM_historical_rcp85_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1_185001-209912_g025.nc')

get_025_ss['MIROC6'] = lambda: get_model_regrid_025_ss(data_name='MIROC6',
                            location='/glade/campaign/cgd/cas/nmaher/miroc6_lens/Omon/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,51,dtype=int).astype(str),
                           middle_bit = '_mon_MIROC6_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025.nc')

get_025_ss['CanESM5'] = lambda: get_model_regrid_025_ss(data_name='CanESM5',
                            location='/glade/campaign/cgd/cas/nmaher/canesm5_lens/Omon/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,41,dtype=int).astype(str),
                           middle_bit = '_mon_CanESM5_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p2f1_g025.nc')

get_025_ss['IPSL-CM6A-L'] = lambda : get_model_regrid_025_ss(data_name='IPSL-CM6A-L',
                            location='/glade/campaign/cgd/cas/nmaher/ipsl_cm6a_lens/Omon/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,33,dtype=int).astype(str),
                           middle_bit = '_mon_IPSL-CM6A-LR_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_g025.nc')

get_025_ss['MIROC-ES2L'] = lambda : get_model_regrid_025_ss(data_name='MIROC-ES2L',
                            location='/glade/campaign/cgd/cas/nmaher/miroc_esm2l_lens/Omon/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,31,dtype=int).astype(str),
                           middle_bit = '_mon_MIROC-ES2L_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f2_g025.nc')
get_025_ss['GFDL-ES2M'] = lambda : get_model_regrid_025_ss(data_name='GFDL-ES2M',
                            location='/glade/campaign/cgd/cas/nmaher/gfdl_esm2m_v2_lens/Omon/',
                            time_slice=slice('1861','1960'),
                            member_names=np.arange(1,31,dtype=int).astype(str),
                           middle_bit = '_GFDL-ESM2M_hist_rcp85_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1_186101-210012.nc')
get_025_ss['MPI-CMIP6'] = lambda : get_model_regrid_025_ss(data_name='MPI-CMIP6',
                            location='/glade/campaign/cgd/cas/nmaher/mpi_lens_cmip6/Omon/',
                            time_slice=slice('1850','1949'),
                            member_names=np.arange(1,51,dtype=int).astype(str),
                           middle_bit = '_Omon_MPI-ESM1-2-LR_historical_r',
                           var_list = ('tos','zos'),
                           tail = 'i1p1f1_gn_185001-201412_g025.nc')
get_025_ss['EC-Earth3_tos'] = lambda: get_model_regrid_025_ss(data_name = 'EC-Earth3',
                                    location = '/glade/campaign/cgd/cas/nmaher/ec-earth3_lens/Omon/',
                                    time_slice = slice('1850','1949'),
                                    member_names = np.concatenate((np.arange(1,5,dtype=int).astype(str),np.arange(6,8,dtype=int).astype(str),np.arange(9,25,dtype=int).astype(str))),
                                    middle_bit = '_EC-Earth_hist_r',
                                    var_list = ('tos',),
                                    tail = 'i1p1f1_185001-201412.nc')

get_025_ss['composite_1'] = lambda: xr.load_dataarray('/glade/work/jjeffree/model_data/composite_1.nc').expand_dims({'SMILE_M':(1,)})
get_025_ss['composite_2'] = lambda: xr.load_dataarray('/glade/work/jjeffree/model_data/composite_2.nc').expand_dims({'SMILE_M':(1,)})
get_025_ss['composite_3'] = lambda: xr.load_dataarray('/glade/work/jjeffree/model_data/composite_3.nc').expand_dims({'SMILE_M':(1,)})
get_025_ss['composite_4'] = lambda: xr.load_dataarray('/glade/work/jjeffree/model_data/composite_4.nc').expand_dims({'SMILE_M':(1,)})
get_025_ss['composite_5'] = lambda: xr.load_dataarray('/glade/work/jjeffree/model_data/composite_5.nc').expand_dims({'SMILE_M':(1,)})

def get_GFDL_CM2_1_025_ss():

    data_name = 'GFDL-CM2-1'

    tos = xr.open_dataset('/glade/work/jjeffree/model_data/GFDL-CM2-1/cm2-1_pi_tos_025.nc',chunks={'time':1200}).sst
    zos = xr.open_dataset('/glade/work/jjeffree/model_data/GFDL-CM2-1/cm2-1_pi_zos_025.nc',chunks={'time':1200}).ssh
    
    ss = xr.concat((tos,zos),'var').assign_coords({'var':np.array(('tos','zos'))})
    new_time = ss.time.isel(time=slice(None,1200))
    full_model_ss = ss.coarsen(time=1200).construct(time=('SMILE_M','time')).assign_coords({'time':new_time,'SMILE_M':np.arange(1,41,dtype=int)})
    
    means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
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
    
get_025_ss['GFDL-CM2-1'] = get_GFDL_CM2_1_025_ss

def get_CESM1_pi_025_ss():

    '''Data this reads was generated running the output of these lines:
    print("module load cdo")
    print("TARGET_FILE=/glade/campaign/cgd/cas/nmaher/access_lens/Omon/tos/tos_mon_ACCESS-ESM1-5_historical_r10i1p1f1_g025.nc")
    filenames = glob.glob('/glade/campaign/cesm/collections/cesmLE/CESM-CAM5-BGC-LE/ocn/proc/tseries/monthly/SST/b.e11.B1850C5CN.f09_g16.005*')
    for f in filenames:
        print("cdo remapdis,$TARGET_FILE "+f+" "+f.split('/')[-1][:-3]+"_025.nc")
    filenames = glob.glob('/glade/campaign/cesm/collections/cesmLE/CESM-CAM5-BGC-LE/ocn/proc/tseries/monthly/SSH/b.e11.B1850C5CN.f09_g16.005*')
    for f in filenames:
        print("cdo remapdis,$TARGET_FILE "+f+" "+f.split('/')[-1][:-3]+"_025.nc")
    '''

    data_name = 'CESM1_pi'

    tos = xr.open_mfdataset('/glade/work/jjeffree/model_data/CESM1/*SST*025.nc',chunks={'time':1200}).SST
    zos = xr.open_mfdataset('/glade/work/jjeffree/model_data/CESM1/*SSH*025.nc',chunks={'time':1200}).SSH
    
    ss = xr.concat((tos,zos),'var').assign_coords({'var':np.array(('tos','zos'))})
    
    assert 'CESM' in data_name, "Only correct CESM dates"
    ss = correct_cesm_date(ss)
    
    new_time = ss.time.isel(time=slice(None,1200))
    full_model_ss = ss.coarsen(time=1200,boundary='trim').construct(time=('SMILE_M','time')).assign_coords({'time':new_time,'SMILE_M':np.arange(5,23,dtype=int)})
    
    means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
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
get_025_ss['CESM1_pi'] = get_CESM1_pi_025_ss

# DO NOT USE A FOR LOOP TO GENERATE THIS KIND OF THING BECAUSE THE 
# LAMBDAS DON'T RUN (AND USE VARIABLES) UNTIL AFTER THE FOR LOOP AS 
# EXITED SO THEY ALL USE THE FINAL VALUE FROM THE FOR LOOP

get_025_ss['ACCESS-ESM1-5_nomean'] = lambda : strip_ensemble_mean(get_025_ss['ACCESS-ESM1-5'](),
'/glade/work/jjeffree/SMILE_means/ACCESS-ESM1-5_ensemble_mean.nc')
get_025_ss['MPI-GE_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MPI-GE'](),
'/glade/work/jjeffree/SMILE_means/MPI-GE_ensemble_mean.nc')
get_025_ss['MIROC6_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MIROC6'](),
'/glade/work/jjeffree/SMILE_means/MIROC6_ensemble_mean.nc')
get_025_ss['CanESM5_nomean'] = lambda : strip_ensemble_mean(get_025_ss['CanESM5'](),
'/glade/work/jjeffree/SMILE_means/CanESM5_ensemble_mean.nc')
get_025_ss['IPSL-CM6A-L_nomean'] = lambda : strip_ensemble_mean(get_025_ss['IPSL-CM6A-L'](),
'/glade/work/jjeffree/SMILE_means/IPSL-CM6A-L_ensemble_mean.nc')
get_025_ss['MIROC-ES2L_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MIROC-ES2L'](),
'/glade/work/jjeffree/SMILE_means/MIROC-ES2L_ensemble_mean.nc')
get_025_ss['GFDL-ES2M_nomean'] = lambda : strip_ensemble_mean(get_025_ss['GFDL-ES2M'](),
'/glade/work/jjeffree/SMILE_means/GFDL-ES2M_ensemble_mean.nc')
get_025_ss['MPI-CMIP6_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MPI-CMIP6'](),
'/glade/work/jjeffree/SMILE_means/MPI-CMIP6_ensemble_mean.nc')
get_025_ss['CESM2-LE_nomean'] = lambda : strip_ensemble_mean(get_025_ss['CESM2-LE_025'](),
                                                                  '/glade/work/jjeffree/SMILE_means/CESM2_025_ensemble_mean.nc')
get_025_ss['EC-Earth3_tos_nomean'] = lambda : strip_ensemble_mean(get_025_ss['EC-Earth3_tos'](),
'/glade/work/jjeffree/SMILE_means/EC-Earth_tos_ensemble_mean.nc')
# get_025_ss['CanESM5_nomean'] = lambda : strip_ensemble_mean(get_025_ss['CanESM5'](),
#                                                    '/glade/work/jjeffree/SMILE_means/CanESM5_025_ensemble_mean.nc')
# get_025_ss['ACCESS-ESM1-5_nomean'] = lambda : strip_ensemble_mean(get_025_ss['ACCESS-ESM1-5'](),
#                                                    '/glade/work/jjeffree/SMILE_means/ACCESS-ESM1-5_025_ensemble_mean.nc')
# get_025_ss['MIROC6_nomean'] = lambda : strip_ensemble_mean(get_025_ss['MIROC6'](),
#                                                    '/glade/work/jjeffree/SMILE_means/MIROC6_025_ensemble_mean.nc')


n_ensemble_members = {'CESM2-LE_025':100,
                      'CESM2-LE':100,
                      'ACCESS-ESM1-5':40,
                      'MPI-GE':100,
                      'MIROC6':50,
                      'CanESM5':40,
                      'IPSL-CM6A-L':32,
                      'MIROC-ES2L':30,
                      'ERSSTv5':1,
                      'OISST-AVISO':1,
                      'GFDL-ES2M':30,
                      'MPI-CMIP6':50,
                      'GFDL-CM2-1':40,
                      'CESM1_pi':18,
                      'EC-Earth3_tos':22,
                      'composite_1':1,
                      'composite_2':1,
                      'composite_3':1,
                      'composite_4':1,
                      'composite_5':1,

                      'CESM2-LE_nomean':100,
                      'ACCESS-ESM1-5_nomean':40,
                      'MPI-GE_nomean':100,
                      'MIROC6_nomean':50,
                      'CanESM5_nomean':40,
                      'IPSL-CM6A-L_nomean':32,
                      'MIROC-ES2L_nomean':30,
                      'ERSSTv5_nomean':1,
                      'OISST-AVISO_nomean':1,
                      'GFDL-ES2M_nomean':30,
                      'MPI-CMIP6_nomean':50,
                      'EC-Earth3_tos_nomean':22,


}

def get_obs_025_ss():

    data_name = 'OISST-AVISO'
    var_list=('tos','zos')
    time_slice = slice('1993-02','2023-05')
    warnings.warn("Be aware that these aren't rounded years")

    sst = xr.open_dataset('/glade/work/jjeffree/observations/oisst.mon.mean_025.nc').sst
    ssh = xr.open_dataset('/glade/work/jjeffree/observations/dataset-satellite-sea-level-global_025.nc').sla
    
    full_model_ss = xr.concat((sst,ssh),'var').assign_coords({'var':np.array(var_list)}).squeeze()
    full_model_ss = full_model_ss.sel(time=time_slice).expand_dims('SMILE_M')
    

    means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
    if not(os.path.isfile(means_file)):
        SMILE_means(full_model_ss,means_file) ###

    #Strip seasonal variability
    seasonal_mean = xr.load_dataset(means_file).seasonal_mean
    full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean

    #Strip global mean
    zos_global_mean = xr.load_dataset(means_file).zos_global_mean
    full_model_ss.loc[{'var':'zos'}] -= zos_global_mean.squeeze()

    return full_model_ss

def get_ersstv5_025_ss():

    data_name = 'ERSSTv5'
    var_list=('tos',)
    time_slice = slice('1854-01','2023-12')

    sst = xr.open_dataset('/glade/work/jjeffree/observations/ersstv5.mnmean_025.nc').sst.squeeze()
    
    full_model_ss = xr.concat((sst,),'var').assign_coords({'var':np.array(var_list)})
    full_model_ss = full_model_ss.sel(time=time_slice).expand_dims('SMILE_M')
    

    means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
    if not(os.path.isfile(means_file)):
        SMILE_means(full_model_ss,means_file,zos_var=None) ###

    #Strip seasonal variability
    seasonal_mean = xr.load_dataset(means_file).seasonal_mean
    full_model_ss = strip_climatology(full_model_ss,clim=seasonal_mean)

    return full_model_ss
get_025_ss['ERSSTv5']=get_ersstv5_025_ss

def get_obs_CESM2_ss():
    ''' Observations, but on a CESM2 grid'''
    assert False, "zos global mean lat weighting isn't sorted out yet. Just use the regridded CESM2"

    data_name = 'OISST-AVISO'
    var_list=('tos','zos')
    time_slice = slice('1993-02','2023-05')
    warnings.warn("Be aware that these aren't rounded years")

    sst = xr.open_dataset('/glade/work/jjeffree/observations/oisst.mon.mean_CESM2_grid.nc').sst
    ssh = xr.open_dataset('/glade/work/jjeffree/observations/dataset-satellite-sea-level-global_CESM2_grid.nc').sla
    
    full_model_ss = xr.concat((sst,ssh),'var').assign_coords({'var':np.array(var_list)}).squeeze()
    full_model_ss = full_model_ss.sel(time=time_slice)
    

    means_file = '/glade/work/jjeffree/SMILE_means/'+data_name+'_025.nc'
    if not(os.path.isfile(means_file)):
        SMILE_means(full_model_ss.expand_dims('SMILE_M'),means_file) ###

    #Strip seasonal variability
    seasonal_mean = xr.load_dataset(means_file).seasonal_mean
    full_model_ss = full_model_ss.groupby('time.month')-seasonal_mean

    #Strip global mean
    zos_global_mean = xr.load_dataset(means_file).zos_global_mean
    full_model_ss.loc[{'var':'zos'}] -= zos_global_mean.squeeze()

    return full_model_ss