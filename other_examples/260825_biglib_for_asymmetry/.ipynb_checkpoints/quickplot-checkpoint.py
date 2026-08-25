from dask.distributed import Client

if __name__ == "__main__":
    client = Client(memory_limit=0,threads_per_worker=1)

    import xarray as xr
    import matplotlib.pyplot as plt
    import numpy as np
    import sys
    sys.path.append('/glade/u/home/jjeffree/ensemble-analogue-predictability/')
    import predictability_tools as pt

    models = ['CESM2-LE','ACCESS-ESM1-5','MPI-GE','MIROC6','CanESM5','IPSL-CM6A-L','MIROC-ES2L','GFDL-ES2M','MPI-CMIP6']
    models.sort()

    r={}
    for i in range(len(models)):
        model_name = models[i]
        fct = xr.open_mfdataset('/glade/work/jjeffree/results/multiindex/'+model_name+'_nomean_tos_zos/*30*P_*.nc')
        assert '30-5P' in fct.mask
        assert '30-5P' in fct.mask
        assert '30P' in fct.mask
        r[model_name] = xr.corr(fct.verification,fct.forecast,('Y','pred_SMILE_M','lib_mi')).load()
        fct.close()
        print(model_name)

    pt.n_ensemble_members['CESM2-LE']=100

    _,phantom_ax = plt.subplots(1,1,figsize=(1,1))
    n=9
    fig, axs = plt.subplots(2,n,figsize=(n*4,8.2*2*1.5),sharey=True,sharex=True)
    for i,model_name in enumerate(models):
        if i==0:
            cb_axs=axs[:,:]
        else:
            cb_axs=(phantom_ax,phantom_ax)
        pt.plot.incremental_sailboat(r[model_name].sel(index_lon='nino34'),N=91*pt.n_ensemble_members[model_name]*((pt.n_ensemble_members[model_name])//5-1),
                         start_mask=('30-5P','5-30P'),
                         later_mask=('30P','30P'),
                         fig=fig,axs=axs[:,i],cb_axs=cb_axs)
        old_title = axs[0,i].get_title()
        axs[0,i].set_title(model_name+'\n'+old_title,size=24)
        axs[1,i].set_xticks([7,13],['Jul','Jan'],size=32)
    axs[0,0].set_ylabel('North Tropical Pacific (add to S)\n\nlead time (months)',size=32)
    axs[1,0].set_ylabel('South Tropical Pacific (add to N)\n\n lead time (months)',size=32)
    plt.savefig('medium_asymmetric_pacific2.pdf')