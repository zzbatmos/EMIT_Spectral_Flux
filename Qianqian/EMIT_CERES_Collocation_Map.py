#!/usr/bin/env python
# coding: utf-8

# This notebook includes codes to 
# * Read in EMIT observations and plot images
# * Collocate EMIT and CERES pixels

# In[1]:


import xarray as xr
import netCDF4,os,re,copy,glob,sys
import numpy as np
import matplotlib.pyplot as plt
import pickle
import cartopy
import sys,os,glob,datetime
import cartopy.crs as crs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import seaborn as sns

# Add the parent directory's subdirectory to sys.path
sys.path.append(os.path.join(os.path.dirname('./'), '../EMIT_project_Zhibo'))
from EMIT_lib import *


# In[2]:


EMIT_data_path_taki = '/umbc/rs/zzbatmos/common/Data/EMIT/'


# ### Function to read EMIT data products into a dictionary

# In[5]:


def read_single_EMIT_granule_data(unique_time_stamp,
                                  products2read,
                                  EMIT_data_path = '/umbc/rs/zzbatmos/common/Data/EMIT/'):
    '''
    Inputs: 
    unique_time_stamp" '20231227T091713' the unique time stamp to track EMIT data
    products2read: list of products to read e.g., ['RAD','RFL','MIN']
    Outputs:
    RAD: Radiance data
    RFL: Surface reflectance data
    
    '''
    L1B_bucket_prefix=os.path.join(EMIT_data_path,'L1B/')
    RAD_file_prefix='EMIT_L1B_RAD_001_'
    OBS_file_prefix='EMIT_L1B_OBS_001_'
    L2A_bucket_prefix=os.path.join(EMIT_data_path,'L2A/')
    RFL_file_prefix='EMIT_L2A_RFL_001_'
    # MIN_bucket_prefix=os.path.join(EMIT_data_path,'L2B/')
    # MIN_file_prefix='EMIT_L2B_MIN_001_'
    EMIT_granule_data={}
    for d in products2read:
        if d=='RAD':
            bucket = os.path.join(L1B_bucket_prefix, RAD_file_prefix+unique_time_stamp)
            product_files =  glob.glob(bucket+'*.nc')
            print('***',product_files,len(product_files),product_files[0])
            if len(product_files) ==1:
                EMIT_granule_data[d]=xr.open_dataset(product_files[0])
                EMIT_granule_data[d+'_location']=xr.open_dataset(product_files[0],
                                                   group="/location")
                EMIT_granule_data[d+'_sensor_band_parameters']=xr.open_dataset(product_files[0],
                                                                               group="/sensor_band_parameters")
        elif d =='OBS':
            bucket = os.path.join(L1B_bucket_prefix, OBS_file_prefix+unique_time_stamp)
            product_files =  glob.glob(bucket+'*.nc')
            if len(product_files) ==1:
                EMIT_granule_data[d]=xr.open_dataset(product_files[0])
                EMIT_granule_data[d+'_location']=xr.open_dataset(product_files[0],
                                                   group="/location")
                EMIT_granule_data[d+'_sensor_band_parameters']=xr.open_dataset(product_files[0],
                                                                               group="/sensor_band_parameters")
        elif d =='RFL':
            bucket = os.path.join(L2A_bucket_prefix, RFL_file_prefix+unique_time_stamp)
            product_files =  glob.glob(bucket+'*.nc')
            for p in product_files:
                if 'RFLUNCERT' in p: 
                    continue
                else:
                    EMIT_granule_data[d]=xr.open_dataset(p)
                    EMIT_granule_data[d+'_sensor_band_parameters'] = xr.open_dataset(product_files[0],
                                                                               group="/sensor_band_parameters")
    return EMIT_granule_data


# In[6]:


EGD=read_single_EMIT_granule_data('20230426T103717',['RAD','OBS','RFL'])


# In[7]:


# EGD['OBS_location'].lon.values
# EGD['RFL_sensor_band_parameters'].wavelengths.values


# In[8]:


# class kurudz_solar(object):
#     def __init__(self):
#         d=np.loadtxt('../EMIT_project_Zhibo/data/solar_flux/kurudz_1.0nm.dat',skiprows=12)
#         self.wavelength = d[:,0]
#         self.spectral_irradiance=d[:,1]/1000.0 # convert mW / (m2 nm) to W/m2/nm
#         self.solar_constant = np.trapz(self.spectral_irradiance,self.wavelength)
#         EMIT_wavelength = np.load('../EMIT_project_Zhibo/EMIT_wavelength.npz')['EMIT_wavelength']
#         spectral_cover = (self.wavelength>= EMIT_wavelength[0]) & (self.wavelength<= EMIT_wavelength[-1])
#         self.wavelength_EMIT = EMIT_wavelength
#         self.spectral_irradiance_EMIT = np.interp(self.wavelength_EMIT,
#                                                   self.wavelength,
#                                                   self.spectral_irradiance)
#         self.solar_constant_EMIT = np.trapz(self.spectral_irradiance_EMIT,self.wavelength_EMIT)
#     def plot_spectral_irradiance(self,overlay_EMIT=False):
#         fig,ax=plt.subplots(figsize=(12,3))
#         ax.plot(self.wavelength,self.spectral_irradiance,lw='0.5',label='full spectrum')
#         ax.set_xlabel('Wavelength [nm]')
#         ax.set_ylabel('Spectral irradiance [ W / (m2 nm)]')
#         #ax.set_title('Integrated solar constant {0:7.3f}'.format(self.solar_constant))
#         ax.set_xlim([0,2500])
#         if overlay_EMIT:
#             ax.plot(self.wavelength_EMIT , self.spectral_irradiance_EMIT, c='r', lw='0.75',label='EMIT spectrum')
#             ax.text(1000,2.0,'Solar Constant Full Specum {0:7.3f}'.format(self.solar_constant))
#             ax.text(1000,1.75,'Solar Constant EMIT Specum {0:7.3f}'.format(self.solar_constant_EMIT),c='r')
#             ax.legend(loc='upper right')
# KS=kurudz_solar()
# KS.plot_spectral_irradiance(overlay_EMIT=True)


# In[9]:


def great_circle(lon0, lat0, lon_array, lat_array):
    arc = np.arccos(np.sin(np.radians(lat0)) * np.sin(np.radians(lat_array))
                 + np.cos(np.radians(lat0)) * np.cos(np.radians(lat_array)) 
                 * np.cos(np.radians(lon0 - lon_array)))
    return 6371 * arc


# In[10]:


# import read_Loeb05_ADM 
# import importlib
# importlib.reload(read_Loeb05_ADM)
# ADM=read_Loeb05_ADM.Loeb05_ADM()


# ### Collocate all the EMIT file in April 2023 with CERES

# In[11]:


with open("../EMIT_project_Zhibo/EMIT_2023_04_L1B_file_list_taki.txt", "r") as read_in_file:
    L1B_filelist=read_in_file.readlines()
nfiles= int(len(L1B_filelist)/2)


# In[12]:


L1B_OBS_filelist = L1B_filelist[0:nfiles]
L1B_RAD_filelist = L1B_filelist[nfiles:]

nfile_to_collocate = len(L1B_RAD_filelist)
timestamp_of_EMIT_granule = []
date_of_EMIT_granule = []
for L1B_file in L1B_RAD_filelist:
    re_result=re.search('EMIT_L1B_RAD_001_',L1B_file)
    start_pos,end_pos=re_result.span()
    year =int(L1B_file[end_pos:end_pos+4])
    month = int(L1B_file[end_pos+4:end_pos+6])
    day = int(L1B_file[end_pos+6:end_pos+8])
    hour = int(L1B_file[end_pos+9:end_pos+11])
    minute = int(L1B_file[end_pos+11:end_pos+13])
    second = int(L1B_file[end_pos+13:end_pos+15])
    timestamp_of_EMIT_granule.append(L1B_file[end_pos:end_pos+15])
    date_of_EMIT_granule.append(datetime.datetime(year,month,day,hour,minute,second))


# In[18]:


# file location of EMIT and CERES data
CERES_data_path='CERES_SSF/'
CERES_SSF_prefix = 'CER_SSF_Terra-FM2' #'CER_SSF_Aqua-FM3'
collocation_file_path='EMIT_TERRA_CERES_collocation/'
#EMIT_data_path='/home/zzbatmos/zzbatmos_common/Data/EMIT/'
collocation_successful=np.array(np.zeros(nfile_to_collocate), dtype='bool') 
# number of cases
ncases=0 #len(case_files)
# start and end datetime of the collocation range (here It is April of 2023)
# start_date = datetime.datetime(2023,4,1,0,0)
# end_date = datetime.datetime(2023,4,30,12,59)
# print('collocation start time',start_date, 'endtime',end_date)

# time window of EMIT-CERES collocation
collocation_time_window_in_hour = 2
# spatial range of EMIT-CERES collocation
collocation_lat_lon_delta = 0.3

verbose = False

#go through all the EMIT files in the directory
print('Find EMIT CERES collocation info: EMIT filename (granule), CERES filename, CERES pixel index')
# sys.exit()
for ifile in range(0,nfile_to_collocate):
    if verbose: 
        print('processing',ifile)
        print('successfully collocated',ncases)
    if os.path.isfile('EMIT_CERES_collocation_taki/'+\
                      collocation_file_path+\
                      timestamp_of_EMIT_granule[ifile] + '.pkl'):
        print(ifile,'already collocated')
        ncases+=1
        collocation_successful[ifile]=True
        continue
        
    if verbose: print('collocating',L1B_OBS_filelist[ifile])
    EMIT_date=date_of_EMIT_granule[ifile]
    if verbose: print('reading in EMIT data')
    EMIT_data_dict=read_single_EMIT_granule_data(timestamp_of_EMIT_granule[ifile],['OBS'])
    if verbose: print('EMIT data reading finished')
    # read in all the CERES data in the time window
    
    CERES_file_list=[]
    CERES_granules={} # dictionary to store CERES data
    for t in range(-collocation_time_window_in_hour,collocation_time_window_in_hour+1):
        d=EMIT_date+datetime.timedelta(hours=t)
        CERES_time_stamp = '{0:4d}{1:02d}{2:02d}{3:02d}'.format(d.year,d.month,d.day,d.hour)
        #print(CERES_time_stamp,CERES_data_path+'*'+CERES_time_stamp+'*.hdf')
        flist=glob.glob(CERES_data_path+'*'+CERES_SSF_prefix+'*'+CERES_time_stamp+'*.hdf')
        #print(flist)
        if len(flist) >0:
            CERES_file_list.append(flist[0])            
            CERES_granules[flist[0]] = CERES_SSF(flist[0])  #?????

    if verbose: print('CERES SSF files',CERES_file_list) 
    #spatial collocation
    EMIT_granule_lon_mean = EMIT_data_dict['OBS_location'].lon.mean()
    EMIT_granule_lat_mean = EMIT_data_dict['OBS_location'].lat.mean()
    EMIT_granule_lat_range = np.array([EMIT_granule_lat_mean-collocation_lat_lon_delta,
                                       EMIT_granule_lat_mean+collocation_lat_lon_delta])
    EMIT_granule_lon_range = np.array([EMIT_granule_lon_mean-collocation_lat_lon_delta,
                                       EMIT_granule_lon_mean+collocation_lat_lon_delta])
    # print(EMIT_granule_lat_range)
    # print(EMIT_granule_lon_range)
    # EMIT latitude range is between [-90 and 90]
    # EMIT longtitude range is between [-180 and 180]
    
    # CERES co-latitude range is between [0 and 180]
    # CERES longtitude range is between [0 and 360]
    
    for CERES_file in CERES_file_list:
        CERES_lats = 90.0-CERES_granules[CERES_file].colats
        CERES_lons = copy.deepcopy(CERES_granules[CERES_file].lons)
        west_half = CERES_lons>180.0
        CERES_lons[west_half] = CERES_lons[west_half]-360.0
        CERES_in_EMIT_granule= (CERES_lats>(EMIT_granule_lat_range[0])) & \
                               (CERES_lats<(EMIT_granule_lat_range[1])) & \
                               (CERES_lons>(EMIT_granule_lon_range[0])) & \
                               (CERES_lons<(EMIT_granule_lon_range[1]))
        #print(CERES_in_EMIT_granule.sum())
        if CERES_in_EMIT_granule.sum() > 0:
            EMIT_CERES_collocation_cases={'L1B_OBS_filelist':[],
                              'L1B_RAD_filelist':[],
                              'CERES_file_name':[],
                              'CERES_pixel_index':[]}
            if verbose: print('EMIT file', L1B_OBS_filelist[ifile],
                              'successfully collocated with \n CERES file', CERES_file)
            collocation_successful[ifile] = True
            ncases+=1       
            if (ncases%10==0): 
                print('collocated cases',ncases)
        
            # collocation successful append EMIT data and CERES data to the dictory
            EMIT_CERES_collocation_cases['L1B_OBS_filelist'].append(L1B_OBS_filelist[ifile])
            EMIT_CERES_collocation_cases['L1B_RAD_filelist'].append(L1B_RAD_filelist[ifile])
            EMIT_CERES_collocation_cases['CERES_file_name'].append(CERES_file)
            EMIT_CERES_collocation_cases['CERES_pixel_index'].append(CERES_in_EMIT_granule)
            pkl_savefile = 'EMIT_CERES_collocation_taki/'+\
                           collocation_file_path+\
                           timestamp_of_EMIT_granule[ifile] + '.pkl'
            if verbose: print(pkl_savefile)
            with open(pkl_savefile, 'wb') as f:
                pickle.dump(EMIT_CERES_collocation_cases, f)
        else:
            if verbose: print('EMIT file', L1B_OBS_filelist[ifile],
                              'cannot be collocated with CERES')
            
                


# ### ???

# In[19]:


collocation_file_path='../EMIT_project_Zhibo/EMIT_CERES_collocation_taki/EMIT_TERRA_CERES_collocation/'
Collocate_file_list=glob.glob(collocation_file_path+'*.pkl') 
Ncases = len(Collocate_file_list)
print(Ncases)

#define sahara region for analysis
sahara_lat_range = [10,30]
sahara_lon_range = [-10,40]

CERES_cloud_fraction_threshold = 100.0 # the threshold for selecting clear-sky CERES SSF FOV
EMIT_CERES_distance_threshold = 20.0 # there radius to collocate EMIT pixels and CERES FOV. 
                                     # Compute the distance from EMIT pixels to a CERES FOV. 
                                     # smaller than this thredhold then EMIT pixels are in CERES FOV

collocation_georesults={}
collocation_georesults['EMIT_time_stamp']=[]
collocation_georesults['CERES_Lon']=[]
collocation_georesults['CERES_Lat']=[]
collocation_georesults['EMIT_Lon_arr']=[]
collocation_georesults['EMIT_Lat_arr']=[]
    
for icase in range(0,Ncases):
    pos = re.search('.pkl',Collocate_file_list[icase])
    EMIT_time_stamp=(Collocate_file_list[icase][pos.span()[0]-15:pos.span()[0]])
    print('icase',icase,EMIT_time_stamp)
    
    with open(Collocate_file_list[icase], 'rb') as pkl_file:
        collocation_data=pickle.load(pkl_file)
    CERES_data=xr.open_dataset('../EMIT_project_Zhibo/'+collocation_data['CERES_file_name'][0],engine='netcdf4')
    CERES_clear_fraction = CERES_data['Clear/layer/overlap percent coverages'].values[collocation_data['CERES_pixel_index'][0]][:,0]
    CERES_clear_sky_pixels = CERES_clear_fraction>=CERES_cloud_fraction_threshold
    
    if CERES_clear_sky_pixels.sum() ==0: 
        continue
    EMIT_data_dict = read_single_EMIT_granule_data(EMIT_time_stamp,['OBS','RAD','RFL'])
    NCERES_clear = CERES_clear_sky_pixels.sum()
    
    for j in range(NCERES_clear):
        lon0=CERES_data['Longitude of CERES FOV at surface'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels][j]
        lat0=90.0-CERES_data['Colatitude of CERES FOV at surface'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels][j]
        
        if NCERES_clear>1 and sahara_lon_range[0] <= lon0 <= sahara_lon_range[1] and sahara_lat_range[0] <= lat0 <= sahara_lat_range[1]:
            collocation_georesults['EMIT_time_stamp'].append(EMIT_time_stamp)
            collocation_georesults['CERES_Lon'].append(lon0)
            collocation_georesults['CERES_Lat'].append(lat0)

            EMIT_lon_array=EMIT_data_dict['OBS_location'].lon.values
            EMIT_lat_array=EMIT_data_dict['OBS_location'].lat.values
            EMIT_CERES_distance=great_circle(lon0,lat0,EMIT_lon_array,EMIT_lat_array)
            EMIT_pixels_in_CERES_FOV = (EMIT_CERES_distance<=EMIT_CERES_distance_threshold)
            EMIT_lon_arr_in_CERES_FOV = EMIT_lon_array[EMIT_pixels_in_CERES_FOV]
            EMIT_lat_arr_in_CERES_FOV = EMIT_lat_array[EMIT_pixels_in_CERES_FOV]
            collocation_georesults['EMIT_Lon_arr'].append(EMIT_lon_arr_in_CERES_FOV)
            collocation_georesults['EMIT_Lat_arr'].append(EMIT_lat_arr_in_CERES_FOV)
            
        if len(collocation_georesults['CERES_Lon'])>=100: 
            sys.exit()

    


# In[ ]:


print(len(collocation_georesults['EMIT_time_stamp']))


# In[ ]:


import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from scipy.spatial import ConvexHull
from matplotlib.patches import Polygon


# In[ ]:


primary_lons=collocation_georesults['CERES_Lon']
primary_lats=collocation_georesults['CERES_Lat']
nearby_lons = collocation_georesults['EMIT_Lon_arr']
nearby_lats = collocation_georesults['EMIT_Lat_arr']

# Create a map of the Sahara region
fig, ax = plt.subplots(figsize=(15, 6), dpi=100, subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([25, 30, 15, 20])  # Adjust the extent to focus on the Sahara
# ax.set_extent([0, 40, 0, 30])  # Adjust the extent to focus on the Sahara
# Add features to the map
ax.coastlines()
# Add country borders
ax.add_feature(cfeature.BORDERS, linestyle='-', edgecolor='gray')
ax.gridlines(draw_labels=True, linestyle='--', color='gray')

# Plot the nearby points with a transparent shaded polygon (using ConvexHull)
label_added = False  # Use a flag to add the label only once
for lon, lat, lon_nearby, lat_nearby in zip(primary_lons, primary_lats, nearby_lons, nearby_lats):
    # Combine lon_nearby and lat_nearby into points for ConvexHull
    points = np.vstack((lon_nearby, lat_nearby)).T
    hull = ConvexHull(points)
    
    # Extract the vertices of the convex hull
    hull_points = points[hull.vertices]
    
    
    # Add the label only on the first polygon
    if not label_added:
        polygon = Polygon(hull_points, closed=True, edgecolor='k', facecolor='r', alpha=0.5, zorder=3, label='EMIT pixels')
        label_added = True  # Set flag to True after adding the label
    else:
        polygon = Polygon(hull_points, closed=True, edgecolor='k', facecolor='r', alpha=0.5, zorder=3)
    
    ax.add_patch(polygon)
    
# Scatter plot the primary points
ax.scatter(primary_lons, primary_lats, color='b', s=8, zorder=5,label='CERES pixels')
    
ax.legend(fontsize=12,frameon=0)

plt.title("EMIT and CERES Collocation")
fig.savefig('../figures/EMIT_CERES_Collocation_Map.png',dpi=300,bbox_inches='tight', pad_inches=0.15)


# In[ ]:





# ### Collocate EMIT and CERES in April 2023

# In[9]:


# The filename (granule) of EMIT OBS and RAD L1B data; The time collocated CERES filename (granule); The index of CERES pixels located in the EMIT granule.
collocation_file_path='../EMIT_project_Zhibo/EMIT_CERES_collocation_taki/EMIT_TERRA_CERES_collocation/'
Collocate_file_list=glob.glob(collocation_file_path+'*.pkl') 
Ncases = len(Collocate_file_list)

CERES_cloud_fraction_threshold = 100.0 # the threshold for selecting clear-sky CERES SSF FOV
EMIT_CERES_distance_threshold = 20.0 # there radius to collocate EMIT pixels and CERES FOV. 
                                     # Compute the distance from EMIT pixels to a CERES FOV. 
                                     # smaller than this thredhold then EMIT pixels are in CERES FOV
        
EMIT_reflectance = []
CERES_reflectance = []


verbose=False

save_flux_comparison_result=True
save_emit_reflectance_result = True
raz_definition = 'ceres'


# In[10]:


print(Collocate_file_list[0])


# In[17]:


for icase in range(0,Ncases):
            
    with open(Collocate_file_list[icase], 'rb') as pkl_file:
        collocation_data=pickle.load(pkl_file)  # CERES pixels located in the EMIT granule, 
                                                # Each file contains info of EMIT L1B OBS and RAD filename, CERES filename and CERES pixel index
                                                # Note, for EMIT filename, what we need is the time stamp
                
        # print(collocation_data)
        # sys.exit()
        
    pos = re.search('.pkl',Collocate_file_list[icase])
    EMIT_time_stamp=(Collocate_file_list[icase][pos.span()[0]-15:pos.span()[0]])
    print('processing case',icase,'out of',Ncases, EMIT_time_stamp)
    flux_comparison_results={}
    flux_comparison_results['EMIT_time_stamp']=EMIT_time_stamp
    
    CERES_data=xr.open_dataset('../EMIT_project_Zhibo/'+collocation_data['CERES_file_name'][0],engine='netcdf4')
    CERES_clear_fraction = CERES_data['Clear/layer/overlap percent coverages'].values[collocation_data['CERES_pixel_index'][0]][:,0]
    CERES_clear_sky_pixels = CERES_clear_fraction>=CERES_cloud_fraction_threshold
    
    #CERES pixels in EMIT granule and clear-sky pixels (two masks)
    CERES_flux = CERES_data['CERES SW TOA flux - upwards'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels]
    CERES_radiance = CERES_data['CERES SW filtered radiance - upwards'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels]
    CERES_radiance_unfiltered = CERES_data['CERES SW radiance - upwards'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels]


    CERES_SZA=CERES_data['CERES solar zenith at surface'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels]
    CERES_VZA=CERES_data['CERES viewing zenith at surface'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels]
    CERES_RAZ=CERES_data['CERES relative azimuth at surface'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels]
    CERES_F0=CERES_data['TOA Incoming Solar Radiation'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels]
    
    CERES_S0=np.nanmean(CERES_F0/np.cos(np.radians(CERES_SZA))) #CERES solar constant (note, it contains seasonal variation)
    KS_CERES_S0_ratio = CERES_S0/KS.solar_constant
    

    flux_comparison_results['CERES_Lon']=[]
    flux_comparison_results['CERES_Lat']=[]
    flux_comparison_results['CERES_S0']=[CERES_S0]
    flux_comparison_results['CERES_Fup_based_on_ADM_filtered']=[]
    flux_comparison_results['CERES_Fup_based_on_ADM_unfiltered']=[]
    flux_comparison_results['CERES_Fup']=[]
    flux_comparison_results['CERES_Fdn']=[]
    flux_comparison_results['CERES_Ref']=[]
    flux_comparison_results['CERES_Sza']=[]
    flux_comparison_results['CERES_Vza']=[]
    flux_comparison_results['CERES_Raz']=[]
    


    flux_comparison_results['EMIT_Fup']=[] # EMIT spectrum 380nm-2500nm
    flux_comparison_results['EMIT_Fup_fullspectrum']=[] #This 'full' spectrum means 315nm-2500nm
    flux_comparison_results['EMIT_Fdn']=[]
    flux_comparison_results['EMIT_Ref']=[]
    flux_comparison_results['EMIT_Sza']=[]
    flux_comparison_results['EMIT_Vza']=[]
    flux_comparison_results['EMIT_Raz']=[]
    flux_comparison_results['EMIT_Adm']=[]
    
    flux_comparison_results['EMIT_wvl']=[]
    flux_comparison_results['EMIT_surface_reflectance_flatten']=[]
    flux_comparison_results['EMIT_surface_reflectance']=[]

    if CERES_clear_sky_pixels.sum() ==0: 
        continue
    EMIT_data_dict = read_single_EMIT_granule_data(EMIT_time_stamp,['OBS','RAD','RFL'])
    NCERES_clear = CERES_clear_sky_pixels.sum()
    
    for j in range(NCERES_clear):
        lon0=CERES_data['Longitude of CERES FOV at surface'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels][j]
        lat0=90.0-CERES_data['Colatitude of CERES FOV at surface'].values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels][j]
        flux_comparison_results['CERES_Lon'].append(lon0)
        flux_comparison_results['CERES_Lat'].append(lat0)
        EMIT_lon_array=EMIT_data_dict['OBS_location'].lon.values
        EMIT_lat_array=EMIT_data_dict['OBS_location'].lat.values
        EMIT_CERES_distance=great_circle(lon0,lat0,EMIT_lon_array,EMIT_lat_array)
        EMIT_pixels_in_CERES_FOV = (EMIT_CERES_distance<=EMIT_CERES_distance_threshold)

        EMIT_pixels_in_CERES_FOV_avg_radiance = EMIT_data_dict['RAD'].radiance.values[EMIT_pixels_in_CERES_FOV].mean(axis=0)        
        EMIT_pixels_in_CERES_SZA = EMIT_data_dict['OBS'].obs.values[:,:,4][EMIT_pixels_in_CERES_FOV].mean() # EMIT solar zenith angle (small variation so only needs mean)
        EMIT_pixels_in_CERES_VZA = EMIT_data_dict['OBS'].obs.values[:,:,2][EMIT_pixels_in_CERES_FOV].mean() # EMIT viewing zenith angle (small variation so only needs mean)
        
        EMIT_pixels_in_CERES_RAZ = EMIT_data_dict['OBS'].obs.values[:,:,1][EMIT_pixels_in_CERES_FOV].mean()-\
                                   EMIT_data_dict['OBS'].obs.values[:,:,3][EMIT_pixels_in_CERES_FOV].mean()
        
        # print(EMIT_data_dict['RFL_sensor_band_parameters'].wavelengths.values)
        # print( EMIT_data_dict['RFL'].reflectance.values.shape, EMIT_pixels_in_CERES_FOV.shape)
        EMIT_wvls = EMIT_data_dict['RFL_sensor_band_parameters'].wavelengths.values
        A = EMIT_data_dict['RFL'].reflectance.values[EMIT_pixels_in_CERES_FOV]
        EMIT_rfls = np.nanmean( np.where(A>0.0,A,np.nan), axis=0) #only keep surface reflectance larger than 0
#         print(EMIT_rfls)
#         print(EMIT_wvls)
        
#         sys.exit()

        if raz_definition =='ceres':
            EMIT_pixels_in_CERES_RAZ = 180.0-EMIT_pixels_in_CERES_RAZ
            # the definition of relative azimuth angle in CERES product
            # is the direction of viewing w.r.t. SUNLIGHT
            # while the relative azimuth angle of EMIT is defined as the viewing direction w.r.t. sun.  
        
        # print([EMIT_pixels_in_CERES_SZA],[EMIT_pixels_in_CERES_VZA],[EMIT_pixels_in_CERES_RAZ])
        # print( [CERES_SZA.values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels][j]],
        #        [CERES_VZA.values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels][j]],
        #        [CERES_RAZ.values[collocation_data['CERES_pixel_index'][0]][CERES_clear_sky_pixels][j]])
        
        
        ADM_for_EMIT = ADM.interpolate_ADM([EMIT_pixels_in_CERES_SZA],[EMIT_pixels_in_CERES_VZA],[EMIT_pixels_in_CERES_RAZ])
        ADM_for_CERES = ADM.interpolate_ADM( [CERES_SZA[j]],
                                             [CERES_VZA[j]],
                                             [CERES_RAZ[j]])
        #print(j,ADM_for_EMIT,ADM_for_CERES)
        flux_comparison_results['CERES_Sza'].append(CERES_SZA[j])
        flux_comparison_results['CERES_Vza'].append(CERES_VZA[j])
        flux_comparison_results['CERES_Raz'].append(CERES_RAZ[j])
        flux_comparison_results['CERES_Fup'].append(CERES_flux[j])
        flux_comparison_results['CERES_Fup_based_on_ADM_filtered'].append(CERES_radiance[j]/ADM_for_CERES[0]*np.pi)
        flux_comparison_results['CERES_Fup_based_on_ADM_unfiltered'].append(CERES_radiance_unfiltered[j]/ADM_for_CERES[0]*np.pi)

        flux_comparison_results['CERES_Fdn'].append(CERES_F0[j])
        flux_comparison_results['CERES_Ref'].append(CERES_flux[j]/CERES_F0[j])
        # print('CERES Fup', flux_comparison_results['CERES_Fup'][-1],
        #                    flux_comparison_results['CERES_Fup_based_on_ADM_filtered'][-1],
        #                    flux_comparison_results['CERES_Fup_based_on_ADM_unfiltered'][-1])
        EMIT_Fup = np.trapz(EMIT_pixels_in_CERES_FOV_avg_radiance,EMIT_data_dict['RAD_sensor_band_parameters'].wavelengths)*np.pi/100.0/ADM_for_EMIT[0]
        wvl_mask = (EMIT_data_dict['RAD_sensor_band_parameters'].wavelengths <=420)
        EMIT_Fup_380_420 = np.trapz(EMIT_pixels_in_CERES_FOV_avg_radiance[wvl_mask],EMIT_data_dict['RAD_sensor_band_parameters'].wavelengths[wvl_mask])*np.pi/100.0/ADM_for_EMIT[0]
        EMIT_Fup_315_380 = 1.01*EMIT_Fup_380_420 + 4.86
        EMIT_Fup_fullspectrum = EMIT_Fup + EMIT_Fup_315_380 #315nm to 2500nm
        EMIT_Fdn = KS.solar_constant*KS_CERES_S0_ratio*np.cos(np.radians(EMIT_pixels_in_CERES_SZA)) # EMIT_Fdn is for full spectrum using CERES solar constant.
        # print('EMIT_Fup',EMIT_Fup)
        # print('EMIT_Fup_380_420',EMIT_Fup_380_420)
        # print('EMIT_Fup_315_380',EMIT_Fup_315_380)
        # print('EMIT_Fup_fullspectrum',EMIT_Fup_fullspectrum)
        flux_comparison_results['EMIT_Fup'].append(EMIT_Fup)
        flux_comparison_results['EMIT_Fup_fullspectrum'].append(EMIT_Fup_fullspectrum)
        flux_comparison_results['EMIT_Fdn'].append(EMIT_Fdn)
        flux_comparison_results['EMIT_Ref'].append(EMIT_Fup/EMIT_Fdn)  #Reflectance_prime
        flux_comparison_results['EMIT_Sza'].append(EMIT_pixels_in_CERES_SZA)
        flux_comparison_results['EMIT_Vza'].append(EMIT_pixels_in_CERES_VZA)
        flux_comparison_results['EMIT_Raz'].append(EMIT_pixels_in_CERES_RAZ)
        flux_comparison_results['EMIT_Adm'].append(ADM_for_EMIT[0])
        
        
        flux_comparison_results['EMIT_wvl'].append(EMIT_wvls)
        flux_comparison_results['EMIT_surface_reflectance'].append(EMIT_rfls)
    if save_flux_comparison_result:  
        save_file_name='Flux_Comparison_Surface_Reflectance_Data/flux_comparison_results_raz_ceres_'+EMIT_time_stamp+'.pkl'
        with open(save_file_name,'wb') as dump_file:
            pickle.dump(flux_comparison_results,dump_file)


# In[ ]:




