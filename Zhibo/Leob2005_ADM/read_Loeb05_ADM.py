import pandas as pd
import glob
import numpy as np

class Loeb05_ADM(object):
    def __init__(self):
        '''
        this routine reads in the csv files that contains the 
        ADM model for bright desert surface based on the Loeb et al. (2005)

        The CSV files are generated from the tables from 
        https://ceres.larc.nasa.gov/documents/INVERSION/adm/tables/trmm/ocean-clr/table-admsw-clr-o-sz010.txt

        Loeb, N. G., S. Kato, K. Loukachine, and N. Manalo-Smith, 2005: 
        Angular Distribution Models for Top-of-Atmosphere Radiative
        Flux Estimation from the Clouds and the Earth’s Radiant Energy System Instrument
        on the Terra Satellite. Part I: Methodology. J. Atmos. Oceanic Technol., 
        22, 338–351, https://doi.org/10.1175/JTECH1712.1.

        '''

        # organize all the CSV files
        csv_files= glob.glob('*.csv')
        csv_files_sorted=[]
        for ele in sorted(csv_files):
            csv_files_sorted.append(ele)
        dataframes = [pd.read_csv(file) for file in csv_files_sorted]
        # number of solar zenith angles equal to the number of tables
        nsza=len(csv_files_sorted)
        # number of viewing zenith and relative azimuth angle
        nvza,nazi=dataframes[0].values[:,1:].shape

        ADM = np.zeros([nsza,nvza,nazi])
        for isza in range(nsza):
            ADM[isza,:,:] = np.array(dataframes[isza].values[:,1:],dtype=float)
        self.sza=np.arange(10,91,10)
        self.vza=np.arange(10,91,10)
        self.azi=np.array([10,30, 50, 70, 90, 110,130,150, 170, 180])
        self.ADM=ADM
        
    def interpolate_ADM(self,sza,vza,azi):
        '''
        interpolate the Loeb AMD model for a given sza, vza and relative azi combination
        input 1-D array sza,vza,azi must have the same length
        '''
        sza_index= np.searchsorted(self.sza,sza)
        vza_index= np.searchsorted(self.vza,vza)
        azi_index= np.searchsorted(self.azi,azi)
        n=len(sza)
        AMD_interp = np.zeros(n)
        for i in range(n):
            AMD_interp[i]=self.ADM[sza_index,vza_index,azi_index]
            
        return AMD_interp

    
    
    
    
