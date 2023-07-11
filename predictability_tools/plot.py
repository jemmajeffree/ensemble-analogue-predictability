''' A place for generic graphs and plots that I make a lot of. 
These can be less precise and generic than the rest of the library
'''


import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import warnings

#This script builds off everything else
from .statistics import *

plt.rcParams.update({'font.size': 14})


def DJF_predictability(data, m_method, ylabel,
                        colorbyyear = False,
                        n_climatology_samples = 256,
                        n_significance_samples = 256,
                        p_value = 0.99,
                        climatology = None,
                        quantiles = (0.05,0.5,0.95),
                      ):
    ''' do m_method to data (preferably described by y label), and plot this.
        Also bootstrap a climatology out of data, and then apply m_method to this and plot it
        Use relative entropy to show how long the data stats are significantly different to climatology'''
    warnings.warn('This is the function I fixed and then accidenatlly overwrote with the old version, so the statistical significance band is definitely buggy')
    
    '''CALCULATE NUMBERS'''
    #What the ensemble does
    ensemble_metric = m_method(data).transpose('L','Y')
    em_spread = ensemble_metric.quantile(quantiles,'Y').data
    
    #What the climatology does
    if (climatology is None):
        climatology = m_method(bootstrap_samples(data,n_Y=n_climatology_samples,n_samples=1,n_M=data.M.shape[0])).squeeze()
    clim_spread = climatology.quantile(quantiles,'Y').data
    
    #Relative entropy and significance
    rent = relative_entropy(ensemble_metric,
                            climatology).data
    
    assert n_significance_samples>(1-p_value)**(-1)*2, 'High p values require more samples to capture distribution tails'
    insignificant_realities = bootstrap_samples(data,n_samples=n_significance_samples,n_Y=data.Y.shape[0],n_M=data.M.shape[0])
    sample_rent = relative_entropy(m_method(insignificant_realities),
                                   climatology)
    sig_rent_threshold = sample_rent.quantile(p_value,'sample').data
    
    
    '''PLOTS'''
    #Plots
    fig, ax = plt.subplots(2,1,gridspec_kw={'height_ratios': (1,0.3)},sharex=True)
    plt.sca(ax[0])
    
    #Plot the ensemble
    plt.plot(ensemble_metric.L,ensemble_metric,c='k',linewidth=0.1,marker='o',markersize=1)
    plt.fill_between(ensemble_metric.L,em_spread[0],em_spread[2],
                    facecolor='grey',alpha=0.4)
    plt.plot(ensemble_metric.L,em_spread[1],c='black',alpha=0.5)
    
    #Check if there's any coherency between years
    if colorbyyear:
        for i in range(data.L.shape[0]):
            plt.scatter(data.Y*0+data.L[i],ensemble_metric[i],marker='o',s=3,
                        c=np.argsort(np.argsort(ensemble_metric[9].data)),
                        #c = data.Y,
                        zorder=10,cmap='gnuplot')
            
    #Plot background climatology
    plt.axhline(clim_spread[1],c='k')
    plt.axhspan(clim_spread[0], clim_spread[2],
                    facecolor='red',alpha=0.2)
    
    plt.ylabel(ylabel)
    
    #Bootstrap what's significant
    plt.sca(ax[1])
    
    plt.plot(ensemble_metric.L,rent,c='blue',marker='+')
    plt.ylabel('Relative\nentropy',color='blue')
    plt.yticks(color='blue')

    plt.axhspan(0,sig_rent_threshold,color='blue',alpha=0.1)
    plt.ylim(0,0.99)
    plt.xlabel('lead time (months)')
    
    fig.subplots_adjust(hspace=0)
    
    
def movie_images(stat,
                 folder,
                 title = '',
                 clabel = '',
                 cmap = 'viridis',
                 movie_time_dim = 'L',
                 vmin = None,
                 vmax = None,
                ):
    
    ''' Take some statistic which is 2D + time, and plot each timestep the merge them into a video'''

    assert stat[movie_time_dim].shape[0]<1000, 'Only saving figures to 3 digits; can\'t handle more than 1000 leads'
    assert folder[-1] == '/', 'folder should specify a directory'
    
    if not os.path.isdir(folder):
        cont = input('Folder doesn\'t currently exist. Press enter to create or type anything to abort')
        if cont == '':
            os.mkdir(folder)
        else:
            return

    if vmin is None:
        vmin = np.min(stat)
    if vmax is None:
        vmax = np.max(stat)
        
    for i,l in enumerate(stat[movie_time_dim]):
        plt.figure(figsize=(10,4))
        ax = plt.axes()
        plotdata = stat.sel({movie_time_dim:l})
        plt.pcolormesh(plotdata,cmap=cmap,vmin=10**-5,vmax=1,norm='log')
        cbar = plt.colorbar()
        cbar.set_label(clabel)
        ax.axis('off')
        plt.title(title+'\n {:2d} months lead'.format(l))
        plt.tight_layout()
        plt.savefig(folder+'{:03d}.png'.format(i),dpi=200)
        plt.close()
        
    (
    ffmpeg
        .input(folder+'%03d.png', framerate=10)
        .output(folder+folder.split('/')[-2]+'.mp4', pix_fmt = 'yuv420p')
        .run(overwrite_output=True)
    )
        
    return