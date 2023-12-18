from .temporal import *
import xarray as xr
import numpy as np


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