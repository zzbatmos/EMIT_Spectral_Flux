import xarray as xr
import netCDF4,os,re,copy,glob
import numpy as np
import matplotlib.pyplot as plt
import datetime


class EMIT_Data(object):
    def __init__(self,ncf,variable_name,data_product,data_level):
        self.data_product=data_product
        self.data_level=data_level
        self.ncf=ncf
        f = netCDF4.Dataset(ncf,'r')
        
        if self.data_level.lower()=='l1b' or self.data_level.lower()=='l2a':
            self.data=f.variables[variable_name][:]
            location = f.groups['location']
            self.location={}
            for g in location.variables:
                self.location[g]=location.variables[g][:]
            sbp = f.groups['sensor_band_parameters']
            self.sensor_band_parameters={}
            for v in sbp.variables:
                self.sensor_band_parameters[v]=sbp.variables[v][:]
        elif self.data_level.lower()=='l2b':
            self.group_1_band_depth=f.variables['group_1_band_depth'][:]
            self.group_2_band_depth=f.variables['group_2_band_depth'][:]
            self.group_1_mineral_id=f.variables['group_1_mineral_id'][:]
            self.group_2_mineral_id=f.variables['group_2_mineral_id'][:]
            location = f.groups['location']
            self.location={}
            for g in location.variables:
                self.location[g]=location.variables[g][:]
            mineral_metadata = f.groups['mineral_metadata']
            self.mineral_metadata={}
            for v in mineral_metadata.variables:
                self.mineral_metadata[v]=mineral_metadata.variables[v][:]
        f.close()

        idx=ncf.find('001_')
        t=ncf[idx+4:idx+12]
        y=int(t[0:4])
        m=int(t[4:6])
        d=int(t[6:])
        self.date=datetime.date(y,m,d)
        
def read_single_EMIT_granule_data(unique_time_stamp,
                                  products2read,
                                  EMIT_data_path ):
    '''
    Inputs: 
    unique_time_stamp" '20231227T091713' the unique time stamp to track EMIT data
    products2read: list of products to read e.g., ['RAD','RFL','MIN']
    Outputs:
    RAD: Radiance data
    RFL: Surface reflectance data
    
    '''
    L1B_bucket_prefix=os.path.join(EMIT_data_path)
    RAD_file_prefix='EMIT_L1B_RAD_001_'
    OBS_file_prefix='EMIT_L1B_OBS_001_'
    
    L2A_bucket_prefix=os.path.join(EMIT_data_path)
    RFL_file_prefix='EMIT_L2A_RFL_001_'
    MASK_file_prefix='EMIT_L2A_MASK_001_'
    
    # MIN_bucket_prefix=os.path.join(EMIT_data_path,'L2B/')
    # MIN_file_prefix='EMIT_L2B_MIN_001_'
    EMIT_granule_data={}
    for d in products2read:
        if d=='RAD':
            bucket = os.path.join(L1B_bucket_prefix, RAD_file_prefix+unique_time_stamp)
            product_files =  glob.glob(bucket+'*.nc')
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
        elif d=='MASK':
            bucket = os.path.join(L2A_bucket_prefix, MASK_file_prefix+unique_time_stamp)
            product_files =  glob.glob(bucket+'*.nc')
            EMIT_granule_data[d]=xr.open_dataset(product_files[0])
        
    return EMIT_granule_data

def read_single_EMIT_granule_data_aws(EMIT_files,product_types,fs_s3):
    '''
    Inputs: 
    EMIT_files: the EMIT files to read in S3 bucket
    s3://lp-prod-protected/EMITL1BRAD.001/EMIT_L1B_RAD_001_20220827T105128_2223907_017/EMIT_L1B_RAD_001_20220827T105128_2223907_017.nc

    fs_s3: the aws credentials 
    lpdaac_creds = get_NASA_creds('lpdaac')
    fs_s3 = s3fs.S3FileSystem(anon=False, 
                          key=lpdaac_creds['accessKeyId'], 
                          secret=lpdaac_creds['secretAccessKey'], 
                          token=lpdaac_creds['sessionToken'])
    
    product_types: types of EMIT data such as "RAD", "RFL" and "MASK"

    *** the lenth of EMIT_files should be the same as the length of product_types
    '''
    # L1B_bucket_prefix=os.path.join(EMIT_data_path)
    # RAD_file_prefix='EMIT_L1B_RAD_001_'
    # OBS_file_prefix='EMIT_L1B_OBS_001_'
    
    # L2A_bucket_prefix=os.path.join(EMIT_data_path)
    # RFL_file_prefix='EMIT_L2A_RFL_001_'
    # MASK_file_prefix='EMIT_L2A_MASK_001_'
    
    # # MIN_bucket_prefix=os.path.join(EMIT_data_path,'L2B/')
    # # MIN_file_prefix='EMIT_L2B_MIN_001_'
    
    EMIT_granule_data={}
    nfile = len(EMIT_files)
    ntype = len(product_types)

    # check if the file numer euqal to the type numer
    if nfile!=ntype:
        print('number of EMIT_files must be equal to number of types')
        return
        
    for n in range(nfile):
        d = product_types[n]
        s3_file_obj = fs_s3.open(EMIT_files[n], mode='rb')
        if d=='RAD':
            
            EMIT_granule_data[d]=xr.open_dataset(s3_file_obj)
            EMIT_granule_data[d+'_location']=xr.open_dataset(s3_file_obj,
                                               group="/location")
            EMIT_granule_data[d+'_sensor_band_parameters']=xr.open_dataset(s3_file_obj,
                                                                           group="/sensor_band_parameters")
        elif d =='OBS':
            EMIT_granule_data[d]=xr.open_dataset(s3_file_obj)
            EMIT_granule_data[d+'_location']=xr.open_dataset(s3_file_obj,
                                               group="/location")
            EMIT_granule_data[d+'_sensor_band_parameters']=xr.open_dataset(s3_file_obj,
                                                                           group="/sensor_band_parameters")
        elif d =='RFL':            
            EMIT_granule_data[d]=xr.open_dataset(s3_file_obj)
        elif d=='MASK':
            EMIT_granule_data[d]=xr.open_dataset(s3_file_obj)
        
    return EMIT_granule_data
    
def compute_pixel_corners(lat, lon):
    """
    Given 2D arrays of pixel center coordinates (lat, lon) of shape (M, N),
    compute approximate pixel corner coordinates of shape (M+1, N+1).
    """
    M, N = lat.shape
    lat_corners = np.zeros((M+1, N+1))
    lon_corners = np.zeros((M+1, N+1))
    
    # Interior corners: average of the 4 surrounding pixel centers.
    lat_corners[1:M, 1:N] = (lat[:-1, :-1] + lat[:-1, 1:] +
                             lat[1:, :-1] + lat[1:, 1:]) / 4.0
    lon_corners[1:M, 1:N] = (lon[:-1, :-1] + lon[:-1, 1:] +
                             lon[1:, :-1] + lon[1:, 1:]) / 4.0

    # Edges: average adjacent centers along the edge.
    lat_corners[0, 1:N] = (lat[0, :-1] + lat[0, 1:]) / 2.0
    lon_corners[0, 1:N] = (lon[0, :-1] + lon[0, 1:]) / 2.0

    lat_corners[M, 1:N] = (lat[-1, :-1] + lat[-1, 1:]) / 2.0
    lon_corners[M, 1:N] = (lon[-1, :-1] + lon[-1, 1:]) / 2.0

    lat_corners[1:M, 0] = (lat[:-1, 0] + lat[1:, 0]) / 2.0
    lon_corners[1:M, 0] = (lon[:-1, 0] + lon[1:, 0]) / 2.0

    lat_corners[1:M, N] = (lat[:-1, -1] + lat[1:, -1]) / 2.0
    lon_corners[1:M, N] = (lon[:-1, -1] + lon[1:, -1]) / 2.0

    # Corners of the grid: simply take the value of the nearest center.
    lat_corners[0, 0] = lat[0, 0]
    lon_corners[0, 0] = lon[0, 0]

    lat_corners[0, N] = lat[0, -1]
    lon_corners[0, N] = lon[0, -1]

    lat_corners[M, 0] = lat[-1, 0]
    lon_corners[M, 0] = lon[-1, 0]

    lat_corners[M, N] = lat[-1, -1]
    lon_corners[M, N] = lon[-1, -1]

    return lat_corners, lon_corners