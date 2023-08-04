''' A place for generic graphs and plots that I make a lot of. 
These can be less precise and generic than the rest of the library
'''


import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import warnings
from xhistogram.xarray import histogram

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
        plt.pcolormesh(plotdata,cmap=cmap,vmin=vmin,vmax=vmax,norm='log')
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

def rank_histogram(rank,rank_min = None, rank_max = None,bin_width = 1):
    ''' Make a histogram from rank data. I'm not entirely certain why I decided this needed
    it's own function, but here we are'''
        
    if rank_min is None:
        rank_min = np.min(rank)
    if rank_max is None:
        rank_max = np.max(rank)
    bins = np.arange(rank_min-0.5,rank_max+1.5,bin_width)
    
    hist_data = histogram(rank,dim='Y',bins=bins,density=True)
    plt.bar((bins[1:]+bins[:-1])/2,
            hist_data,width=bin_width-0.1)
    return hist_data

def analogue_goodness(this_obs,
                          this_ens,
                           title):
    
    n_members = this_ens.M.shape[0]
    fig, axs = plt.subplots(2,2,figsize=(8,8))
    plt.suptitle(title)
    
    axs[0,0].axis('off')
    axs[0,0].text(0.1,0.5,'R$^2$ ='+str(round(float(R2(this_obs,this_ens.mean('M'))),3)),size=22,alpha=0.8)
    axs[0,0].set_title('a) Predictive skill', fontsize=12, loc='left')
    
    plt.sca(axs[0,1])
    #plt.title('R$^2$ '+str(round(float(R2(this_obs,this_ens.mean('M'))),3)))
    plt.scatter(this_obs,this_ens.mean('M'))
    plt.plot(this_obs.quantile((0,1)),this_obs.quantile((0,1)),c='k',linewidth=3,alpha=0.5)
    plt.ylabel('prediction')
    plt.xlabel('validation')

    
    
    plt.sca(axs[1,0])
    rank_histogram(rank_obs(this_obs,this_ens))
    plt.xlim(-0.5,n_members+0.5)
    plt.plot((-1,n_members+1),np.ones(2)/(n_members+1),c='k',linewidth=3,alpha=0.5)
    plt.xlabel('rank',fontsize=12)
    plt.ylabel('frequency',fontsize=12)

    
    
    plt.sca(axs[1,1])
    x = np.arange(1,n_members+2)
    legit_dist = np.linspace(0,1,n_members+2)[1:]
    legit_dist[:-1] -=0.5/(n_members) #A uniform distribution losing the tails slightlys
    
    hist_data = histogram(rank_obs(this_obs,this_ens),dim='Y',bins=np.arange(-0.5,n_members+1.5,1),density=True)
    
    plt.plot(x,hist_data.cumsum('rank_bin'),linestyle='dashed',marker='.',linewidth=0.5,zorder=4)
    KS_test_stat = np.max(np.abs(legit_dist-hist_data.cumsum('rank_bin').data))
    plt.plot(x,legit_dist,c='k',linewidth=2,alpha=0.3)
    axs[1,1].text(1,0.75,str(round(float(KS_test_stat),3)),size=16,alpha=0.8)
   
    plt.xlabel('rank',fontsize=12)
    plt.ylabel('cumulative frequency',fontsize=12)
    
    #Don't think is right
#     if(KS_test_stat<scipy.stats.kstwo.ppf((0.01),n_members+1)):
#         axs[1,1].text(1,0.75,'KS ='+str(round(float(KS_test_stat),3))+'\n insig. diff',size=16,alpha=0.8)
#     else:
#         axs[1,1].text(1,0.75,'KS ='+str(round(float(KS_test_stat),3))+'\n sig. diff',size=16,alpha=0.8)

    quant_dist = rank_obs(this_obs,this_ens).quantile((0,0.25,0.75,1)).diff('quantile')
    dispersion = (quant_dist[1]-quant_dist[0]-quant_dist[2])/n_members
    
    
    std = rank_obs(this_obs,this_ens).var()
    uniform_std = np.concatenate((np.arange(n_members),np.arange(1,n_members+1))).var()
    #print(std,uniform_std)
    #print('overdispersion (variance):   '+str(round(float((uniform_std-std)/uniform_std)*100,0))+'%')
    plt.title('overdispersion (quartiles): '+str(round(-float(dispersion)*100,0))+'%\n'
             +'overdispersion (variance): '+str(round(float((uniform_std-std)/uniform_std)*100,0))+'%',fontsize=12)
    
        
    plt.subplots_adjust(hspace=0.5,wspace=0.45)