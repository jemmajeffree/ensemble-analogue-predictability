import xarray as xr
import numpy as np

# Develop the set of masks we'll be using here
full_mask = xr.open_dataarray('/glade/u/home/jjeffree/ensemble-analogue-predictability/ocean_basin_mask_g025.nc')

atlantic_mask = full_mask.sel(region='Atlantic Ocean').astype(bool).drop_vars('region')
pacific_mask = full_mask.sel(region='Pacific Ocean').astype(bool).drop_vars('region')
indian_mask = full_mask.sel(region='Indian Ocean').astype(bool).drop_vars('region')
ocean_mask = full_mask.sel(region='Global').astype(bool).drop_vars('region')

mask_dict = {}

# Single number and letter is a symmetric shape that many degrees from the equator
# P is Pacific Ocean
# 5P would be 5S-5N in the Pacific Ocean
mask_dict['5P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<5,0)
mask_dict['10P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<10,0) #,0 means fill with 0 not nan
mask_dict['15P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<15,0) 
mask_dict['20P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<20,0) 
mask_dict['30P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<30,0) 
mask_dict['45P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<45,0)
mask_dict['60P'] = pacific_mask.where(np.abs(pacific_mask['lat'])<60,0)

#Asymmetric mask in a single basin, e.g. 10-60P is 10S-60N in the Pacific Ocean
mask_dict['10-60P'] = pacific_mask.where(pacific_mask['lat']>-10,0) & pacific_mask.where(pacific_mask['lat']<60,0)
mask_dict['15-60P'] = pacific_mask.where(pacific_mask['lat']>-15,0) & pacific_mask.where(pacific_mask['lat']<60,0)
mask_dict['20-60P'] = pacific_mask.where(pacific_mask['lat']>-20,0) & pacific_mask.where(pacific_mask['lat']<60,0)
mask_dict['10-30P'] = pacific_mask.where(pacific_mask['lat']>-10,0) & pacific_mask.where(pacific_mask['lat']<30,0)
mask_dict['60-10P'] = pacific_mask.where(pacific_mask['lat']>-60,0) & pacific_mask.where(pacific_mask['lat']<10,0)
mask_dict['60-15P'] = pacific_mask.where(pacific_mask['lat']>-60,0) & pacific_mask.where(pacific_mask['lat']<15,0)
mask_dict['60-20P'] = pacific_mask.where(pacific_mask['lat']>-60,0) & pacific_mask.where(pacific_mask['lat']<20,0)
mask_dict['30-10P'] = pacific_mask.where(pacific_mask['lat']>-30,0) & pacific_mask.where(pacific_mask['lat']<10,0)

#North, rather than equatorward, of the number
mask_dict['45NP'] = pacific_mask.where(pacific_mask['lat']>45,0)

#A is Atlantic Ocean, I is Indian Ocean
mask_dict['30A'] = atlantic_mask.where(np.abs(atlantic_mask['lat'])<30,0) 
mask_dict['30I'] = indian_mask.where(np.abs(indian_mask['lat'])<30,0)

#Adding oceans together is the union of the sets
mask_dict['30P30A'] = pacific_mask.where(np.abs(pacific_mask['lat'])<30,0) | atlantic_mask.where(np.abs(atlantic_mask['lat'])<30,0)
mask_dict['30P30I'] = pacific_mask.where(np.abs(pacific_mask['lat'])<30,0) | indian_mask.where(np.abs(indian_mask['lat'])<30,0)
mask_dict['30P30A30I'] = ocean_mask.where(np.abs(ocean_mask['lat'])<30,0)

mask_dict['30P45S'] = pacific_mask.where(np.abs(pacific_mask['lat'])<30,0) | ocean_mask.where(ocean_mask['lat']<-45,0)

#Weird nuanced stuff
#Pacific 10P but with an extra bit to capture the cold tongue better
mask_dict['10P30S80WP'] = pacific_mask.where((pacific_mask.lat<10) & ((pacific_mask.lat>-10) | ((pacific_mask.lat>-30) & (pacific_mask.lon>260))),0)

