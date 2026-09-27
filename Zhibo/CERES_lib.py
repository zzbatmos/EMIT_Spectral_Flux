# hdf = pyhdf.SD.SD('FLASH_SSF_Terra-FM1-MODIS_Version4A_403411.2024012411.hdf')
# hdf.datasets()
from pyhdf import SD
class CERES_SSF(object):
  def __init__(self,fn):

    hdf = SD.SD(fn)
    self.colats=hdf.select("Colatitude of CERES FOV at surface").get()
    self.lons=hdf.select("Longitude of CERES FOV at surface").get()
    self.time=hdf.select("Time of observation").get()
    self.SW_F0=hdf.select("TOA Incoming Solar Radiation").get()
    self.SW_TOA=hdf.select("CERES SW TOA flux - upwards").get()
    self.SZA=hdf.select("CERES solar zenith at surface").get()
    # self.cf_ocean = hdf.select("PSF-wtd_MOD04_cloud_fraction_ocean").get()
    # self.cf_land  = hdf.select("PSF-wtd_MOD04_cloud_fraction_land").get()
    # for k in hdf.datasets():
    #   print(k)
    # self.data = {}
    # for sds in SDS_list:
    #   print('reading',sds)
    #   s = hdf.select(sds)
    #   self.data[sds]=s.get()
    #   s.endaccess()
    hdf.end()