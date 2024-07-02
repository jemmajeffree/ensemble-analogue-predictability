''' A place for generic graphs and plots that I make a lot of. 
These can be less precise and generic than the rest of the library
'''


import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import warnings
from xhistogram.xarray import histogram
from matplotlib.collections import LineCollection
import matplotlib.patheffects as path_effects

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


def add_iso_line(ax, data, value,x_shift,y_shift,linekwargs={'colors':'grey','lw':2}):
    '''Adapted from https://stackoverflow.com/questions/63458863/way-to-contour-outer-edge-of-selected-grid-region-in-python/63459354#63459354
    Draws a contour around the edges of cells, instead of interpolating like contour does'''
    v = np.diff(data>value,axis=1)
    h = np.diff(data>value,axis=0)
    

    l = np.argwhere(v.T).astype(float)  
    l[:,0]+=0.5+x_shift
    l[:,1]+=-0.5+y_shift
    vlines = np.array(list(zip(l, np.stack((l[:,0], l[:,1]+1)).T)))
    

    l = np.argwhere(h.T).astype(float) 
    l[:,0]+=-0.5+x_shift
    l[:,1]+=0.5+y_shift
    hlines = np.array(list(zip(l, np.stack((l[:,0]+1, l[:,1])).T)))#-0.5

    lines = np.vstack((vlines, hlines))

    assert len(lines>0), "No lines to plot; contour probably doesn't exist"

    ax.add_collection(LineCollection(lines, path_effects=[path_effects.Stroke(capstyle="round")],**linekwargs))

def sailboat(skill,
                    N = 40*90*7,
                    start_mask = '30P',
                    later_mask=('30P30A','30P30I','60P'),
                    skill_type='corr',
                    vlim=(-0.1,0.1),
             fig = None,
             axs = None,
             cb_axs=None,

    ):
    assert not(0 in skill.init_month), 'Month should have coordinates'
    if skill_type=='corr':
        diff_func = lambda x,y: np.tanh(np.arctanh(y)-np.arctanh(x))
        cmap = 'BrBG'
        def stat_sig(r,r1):
            S = np.sqrt(1/(N-3))

            z = (np.arctanh(r1)-np.arctanh(r))/S
            
            stat_sig = xr.ones_like(z).where(np.abs(z)>1.96)
            if np.any(~np.isnan(stat_sig)) and np.any(np.isnan(stat_sig)):
                add_iso_line(plt.gca(), stat_sig.roll(init_month=-4).T, 0.01,x_shift = 5, y_shift = 0,linekwargs={'colors':'grey','lw':0.8,'linestyle':'dotted'}) #I think xshift is 1st month???

            stat_sig = xr.ones_like(z).where(np.abs(z)>2.58)
            if np.any(~np.isnan(stat_sig)) and np.any(np.isnan(stat_sig)):
                add_iso_line(plt.gca(), stat_sig.roll(init_month=-4).T, 0.01,x_shift = 5, y_shift = 0,linekwargs={'colors':'grey','lw':1,}) #I think xshift is 1st month???
        clabel0 = 'r'
        clabel = '$\Delta$r'

    elif skill_type=='mse':
        diff_func = lambda x,y: ((y-x)/x)*100
        cmap = 'BrBG_r'

        def stat_sig(r,r1):
                F = r1/r

                p_good = scipy.stats.f.cdf(r1/r,N-2,N-2)
                p_bad = scipy.stats.f.cdf(r/r1,N-2,N-2)
                p = np.min((p_good,p_bad),axis=0)
                
                stat_sig = xr.ones_like(F).where(p<0.01)
                if np.any(~np.isnan(stat_sig)) and np.any(np.isnan(stat_sig)):
                    add_iso_line(plt.gca(), stat_sig.roll(init_month=-4).T, 0.01,x_shift = 5, y_shift = 0,linekwargs={'colors':'grey','lw':0.8,})#'linestyle':'dotted' #I think xshift is 1st month???

        clabel0 = 'MSE'
        clabel = '% MSE change'
    else:
        assert False, 'need a skill type'

    if fig is None:
        assert axs is None, 'Either pass both axs and fig or neither'
        fig, axs = plt.subplots(1,len(later_mask)+1,figsize=((len(later_mask)+1)*4,8),
                               sharex=True,sharey=True)
    if cb_axs is None:
        cb_axs=axs[0],axs[1:]

    plt.sca(axs[0])
    plt.title(start_mask)
    r = skill.sel(mask=start_mask)
    scatter = plt.scatter((r.init_month+r.L*0-5)%12+5,
            r.init_month*0+r.L,
            c=r,
            cmap='YlGn',marker='s',s=100,vmin=0,vmax=1)
    plt.xlabel('Initialisation month')
    plt.ylabel('Lead time (months)')
    
    fig.colorbar(scatter, ax=cb_axs[0],orientation='horizontal', fraction=.05,
             extend='both',label = clabel0)

    for ax_i in range(len(later_mask)):
        plt.sca(axs[ax_i+1])


        r1 = skill.sel(mask=later_mask[ax_i])

        scatter = plt.scatter((r.init_month+r.L*0-5)%12+5,
            r.init_month*0+r.L,
            c=diff_func(r,r1),
            cmap=cmap,marker='s',s=100,vmin=vlim[0],vmax=vlim[1])
        # print(diff_func(r,r1).sel(L=12,init_month=8).load())
        # print(diff_func(1.319,1.28))
        # print('---------')
        # print(r.sel(L=12,init_month=8))
        # print(r1.sel(L=12,init_month=8))

        stat_sig(r,r1)

        plt.xticks((13,16,7,10),('Jan','Apr','Jul','Oct'))
        plt.title(start_mask+' -> '+later_mask[ax_i])
        plt.xlabel('Initialisation month')

    fig.colorbar(scatter, ax=cb_axs[1],orientation='horizontal', fraction=.05,
             extend='both',label = clabel,aspect=20*len(later_mask))
    return axs

def incremental_sailboat(skill,
                    N = 40*90*7,
                    start_mask = ('30P','30P','30P'),
                    later_mask=('30P30A','30P30I','60P'),
                    skill_type='corr',
                    vlim=(-0.1,0.1),
             fig = None,
             axs = None,
             cb_axs=None,

    ):
    assert not(0 in skill.init_month), 'Month should have coordinates'
    if skill_type=='corr':
        diff_func = lambda x,y: np.tanh(np.arctanh(y)-np.arctanh(x))
        cmap = 'BrBG'
        def stat_sig(r,r1):
            S = np.sqrt(1/(N-3))

            z = (np.arctanh(r1)-np.arctanh(r))/S
            
            stat_sig = xr.ones_like(z).where(np.abs(z)>1.96)
            if np.any(~np.isnan(stat_sig)) and np.any(np.isnan(stat_sig)):
                add_iso_line(plt.gca(), stat_sig.roll(init_month=-4).T, 0.01,x_shift = 5, y_shift = 0,linekwargs={'colors':'grey','lw':0.8,'linestyle':'dotted'}) #I think xshift is 1st month???

            stat_sig = xr.ones_like(z).where(np.abs(z)>2.58)
            if np.any(~np.isnan(stat_sig)) and np.any(np.isnan(stat_sig)):
                add_iso_line(plt.gca(), stat_sig.roll(init_month=-4).T, 0.01,x_shift = 5, y_shift = 0,linekwargs={'colors':'grey','lw':1,}) #I think xshift is 1st month???
        clabel0 = 'r'
        clabel = '$\Delta$r'

    elif skill_type=='mse':
        diff_func = lambda x,y: ((y-x)/x)*100
        cmap = 'BrBG_r'

        def stat_sig(r,r1):
                F = r1/r

                p_good = scipy.stats.f.cdf(r1/r,N-2,N-2)
                p_bad = scipy.stats.f.cdf(r/r1,N-2,N-2)
                p = np.min((p_good,p_bad),axis=0)
                
                stat_sig = xr.ones_like(F).where(p<0.01)
                if np.any(~np.isnan(stat_sig)) and np.any(np.isnan(stat_sig)):
                    add_iso_line(plt.gca(), stat_sig.roll(init_month=-4).T, 0.01,x_shift = 5, y_shift = 0,linekwargs={'colors':'grey','lw':0.8,})#'linestyle':'dotted' #I think xshift is 1st month???

        clabel0 = 'MSE'
        clabel = '% MSE change'
    else:
        assert False, 'need a skill type'

    if fig is None:
        assert axs is None, 'Either pass both axs and fig or neither'
        fig, axs = plt.subplots(1,len(later_mask)+1,figsize=((len(later_mask)+1)*4,8),
                               sharex=True,sharey=True)
    elif axs is None:
        assert False, 'Either pass both axs and fig or neither'
        
    if cb_axs is None:
        cb_axs=axs

    assert len(later_mask) == len(start_mask), 'later and start mask must be paired'
    for ax_i in range(len(later_mask)):
        plt.sca(axs[ax_i])

        r = skill.sel(mask=start_mask[ax_i])
        r1 = skill.sel(mask=later_mask[ax_i])

        scatter = plt.scatter((r.init_month+r.L*0-5)%12+5,
            r.init_month*0+r.L,
            c=diff_func(r,r1),
            cmap=cmap,marker='s',s=100,vmin=vlim[0],vmax=vlim[1])
        stat_sig(r,r1)

        plt.xticks((13,16,7,10),('Jan','Apr','Jul','Oct'))
        plt.title(start_mask[ax_i]+' -> '+later_mask[ax_i])
        plt.xlabel('Initialisation month')

    fig.colorbar(scatter, ax=cb_axs,orientation='horizontal', fraction=.05,
             extend='both',label = clabel,aspect=20*len(later_mask))
    return axs
