
import numpy as np
from pyhdf.SD import SD, SDC

class MOD021KM(object):
    
    def __init__(self,fn, Read_ems=False, Radiance=True):
        '''
        read in cloud properties from MOD021km file
        '''
        import pyhdf
        f = SD(fn,SDC.READ)
        self.lat = f.select('Latitude').get()
        self.lon = f.select('Longitude').get()        
        # wavelength of 36 MODIS bands
        # *** important to note that band 13 and 14 have low and high gain modes
        # *** so there are 38 wavelength in total

        self.bands_wl= np.array([0.645, 0.858, 0.469, 0.555, 1.240,
                                 1.640, 2.130, 0.412, 0.443, 0.488,
                                 0.531, 0.551, 0.667, 0.667, 0.678, 0.678, 0.748,
                                 0.869, 0.905, 0.936, 0.940, 3.75,
                                 3.959, 3.959, 4.05,  4.4655,4.5155,
                                 1.375, 6.715, 7.325, 8.55,  9.73,
                                 11.03, 12.02, 13.335, 13.635, 13.935,
                                 14.235])
        
        d = f.select('EV_250_Aggr1km_RefSB') # band 1-2
        #:band_names = "1,2";
        if Radiance:
            offset = np.array(d.attributes()['radiance_offsets'])
            scale  = np.array(d.attributes()['radiance_scales'])
        else:
            offset = np.array(d.attributes()['reflectance_offsets'])
            scale  = np.array(d.attributes()['reflectance_scales'])
        EV_250_Aggr1km_RefSB = np.array(d.get(),dtype=np.float64)
        b,x,a=EV_250_Aggr1km_RefSB.shape
        #print('dimension',b,x,a)
        # put all the observations in one large array in the order of band number
        # first dimension is band, second and third dimentions are cross and along track pixel number
        self.bands_obs = np.zeros([38,x,a])
        
        for i in  np.arange(offset.size):
            EV_250_Aggr1km_RefSB[i,:,:] =  (EV_250_Aggr1km_RefSB[i,:,:]-offset[i]) * scale[i]
        self.bands_obs[0:2,:,:] = EV_250_Aggr1km_RefSB


        d = f.select('EV_500_Aggr1km_RefSB') # band 3-7
        #:band_names = "3,4,5,6,7";
        if Radiance:
            offset = np.array(d.attributes()['radiance_offsets'])
            scale  = np.array(d.attributes()['radiance_scales'])
        else:
            offset = np.array(d.attributes()['reflectance_offsets'])
            scale  = np.array(d.attributes()['reflectance_scales'])
        EV_500_Aggr1km_RefSB = np.array(d.get(),dtype=np.float64)
        for i in  np.arange(offset.size):
            EV_500_Aggr1km_RefSB[i,:,:] =  (EV_500_Aggr1km_RefSB[i,:,:]-offset[i]) * scale[i]
        self.bands_obs[2:7,:,:] = EV_500_Aggr1km_RefSB
        
        d = f.select('EV_1KM_RefSB') # band 8-19
        #band_names = "8,9,10,11,12,13lo,13hi,14lo,14hi,15,16,17,18,19,26";
        if Radiance:
            #print('d.attributes()',d.attributes())
            offset = np.array(d.attributes()['radiance_offsets'])
            scale  = np.array(d.attributes()['radiance_scales'])
        else:
            offset = np.array(d.attributes()['reflectance_offsets'])
            scale  = np.array(d.attributes()['reflectance_scales'])
        EV_1KM_RefSB = np.array(d.get(),dtype=np.float64)
        for i in  np.arange(offset.size):
            EV_1KM_RefSB[i,:,:] =  (EV_1KM_RefSB[i,:,:]-offset[i]) * scale[i]
        #print('EV_1KM_RefSB.shape',EV_1KM_RefSB.shape)
        self.bands_obs[7:21,:,:] = EV_1KM_RefSB[:-1,:,:]
        self.bands_obs[27,:,:] = EV_1KM_RefSB[-1,:,:]

        if Read_ems:
            #band_names = "20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36"
            d = f.select('EV_1KM_Emissive') # band 8-19
            offset = np.array(d.attributes()['radiance_offsets'])
            scale  = np.array(d.attributes()['radiance_scales'])
            EV_1KM_Emissive = np.array(d.get(),dtype=np.float64)
            for i in  np.arange(offset.size):
                EV_1KM_Emissive[i,:,:] = (EV_1KM_Emissive[i,:,:] -offset[i]) * scale[i]
            self.bands_obs[21:27,:,:] = EV_1KM_Emissive[0:6,:,:]
            self.bands_obs[28:,:,:] = EV_1KM_Emissive[6:,:,:]
            
                    
class MOD03(object):
    def __init__(self,fn):
        '''
        read in cloud properties from MOD021km file
        '''
        import pyhdf
        f = SD(fn,SDC.READ)
        self.lat = f.select('Latitude').get()
        self.lon = f.select('Longitude').get()     
        self.sen_azi = f.select('SensorAzimuth').get()
        self.sen_zen = f.select('SensorZenith').get() 
        self.sol_azi = f.select('SolarAzimuth').get()
        self.sol_zen = f.select('SolarZenith').get() 
        