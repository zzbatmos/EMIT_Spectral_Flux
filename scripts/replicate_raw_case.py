"""Rebuild a historical EMIT/CERES case from original satellite observations.

Uses the supplied EMIT manifests, direct LP DAAC S3, locally cached ASDC HDF4,
and original spatial/time/ADM/UV rules. Saved results are used only afterward
for validation. Run from the project root after sourcing scripts/activate.sh.
"""
from pathlib import Path
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor
import argparse
import datetime as dt
import hashlib
import fcntl
import json
import pickle
import time

import earthaccess
import h5py
import numpy as np
from pyhdf.SD import SD, SDC

ROOT=Path(__file__).resolve().parents[1]
CERES_FIELDS={
 'lon':'Longitude of CERES FOV at surface', 'colat':'Colatitude of CERES FOV at surface',
 'clear':'Clear/layer/overlap percent coverages', 'flux':'CERES SW TOA flux - upwards',
 'radiance':'CERES SW radiance - upwards', 'filtered':'CERES SW filtered radiance - upwards',
 'sza':'CERES solar zenith at surface', 'vza':'CERES viewing zenith at surface',
 'raz':'CERES relative azimuth at surface', 'incoming':'TOA Incoming Solar Radiation',
 'time':'Time of observation'}


def log(*args):
 print(dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S'),*args,flush=True)


def retry(fn, tries=3):
 for attempt in range(tries):
  try:return fn()
  except Exception:
   if attempt==tries-1:raise
   time.sleep(2**attempt)


def read_ceres(fs, date):
 name=f'CER_SSF_Terra-FM2-MODIS_Edition4A_407405.{date:%Y%m%d%H}'
 url=f's3://asdc-prod-protected/CERES/CER_SSF_Terra-FM2-MODIS_Edition4A/{date:%Y.%m}/{name}'
 path=ROOT/'data/ceres_terra_april'/f'{name}.hdf'
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.with_suffix('.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if not path.exists():
   tmp=path.with_suffix('.part'); retry(lambda:fs.get_file(url,str(tmp)));tmp.replace(path)
 h=SD(str(path),SDC.READ)
 try:
  data={}
  for key,field in CERES_FIELDS.items():
   s=h.select(field);a=s.get();attrs=s.attributes();s.endaccess()
   if '_FillValue' in attrs:
    a=np.where(a==attrs['_FillValue'],np.nan,a)
   data[key]=a
 finally:h.end()
 return url,data


def manifest_name(timestamp,product):
 file=ROOT/('EMIT_L2A.txt' if product=='RFL' else 'EMIT_L1B.txt')
 level='L2A' if product=='RFL' else 'L1B'
 names=[n.strip() for n in file.read_text().splitlines() if n.startswith(f'EMIT_{level}_{product}_001_{timestamp}_') and n.endswith('.nc')]
 if len(names)!=1: raise ValueError(f'{timestamp} {product}: {len(names)} manifest matches')
 return names[0]


def emit_url(timestamp,product):
 name=manifest_name(timestamp,product)
 if product=='RFL':
  coll='EMITL2ARFL.001'; folder=name[:-3]
 else:
  coll='EMITL1BRAD.001';folder=manifest_name(timestamp,'RAD')[:-3]
 return f's3://lp-prod-protected/{coll}/{folder}/{name}'


def open_h5(stack,fs,url):
 handle=stack.enter_context(fs.open(url,'rb',block_size=8*1024**2))
 return stack.enter_context(h5py.File(handle,'r'))


def values(d):
 a=d[:]
 if '_FillValue' in d.attrs:
  a=np.where(a==d.attrs['_FillValue'],np.nan,a)
 return a


def read_cube(fs,url,d):
 """Read a contiguous uncompressed dataset in parallel byte ranges, once.

This preserves native float32 values and NumPy mean order without fetching
three interleaved bands separately. Noncontiguous layouts use normal HDF5 I/O.
"""
 offset=d.id.get_offset()
 if offset is None or d.chunks is not None or d.compression is not None:
  return values(d)
 nbytes=d.size*d.dtype.itemsize; out=np.empty(d.shape,dtype=d.dtype)
 raw=memoryview(out).cast('B'); block=32*1024**2
 def readpart(start):
  end=min(start+block,nbytes)
  data=retry(lambda:fs.cat_file(url,start=int(offset)+start,end=int(offset)+end))
  if len(data)!=end-start:raise IOError('Incomplete S3 range')
  raw[start:end]=data
 with ThreadPoolExecutor(max_workers=4) as pool:
  list(pool.map(readpart,range(0,nbytes,block)))
 if '_FillValue' in d.attrs:out[out==d.attrs['_FillValue']]=np.nan
 return out


def adm_tables():
 paths=sorted((ROOT/'Zhibo/Leob2005_ADM').glob('*.csv'))
 tables=np.stack([np.loadtxt(p,delimiter=',',skiprows=1,usecols=range(1,11)) for p in paths])
 if tables.shape!=(9,9,10):raise ValueError(tables.shape)
 return tables


def adm(tables,sza,vza,azi):
 # Original Zhibo/read_Loeb05_ADM.py angle folding and bin lookup.
 az=abs(azi) if azi<0 else (360-azi if azi>180 else azi)
 i=np.searchsorted(np.arange(10,91,10),sza)
 j=np.searchsorted(np.arange(10,91,10),vza)
 k=np.searchsorted([10,30,50,70,90,110,130,150,170,180],az)
 return tables[i,j,k]


def distance(lon0,lat0,lon,lat):
 return 6371*np.arccos(np.sin(np.radians(lat0))*np.sin(np.radians(lat))+
  np.cos(np.radians(lat0))*np.cos(np.radians(lat))*np.cos(np.radians(lon0-lon)))


def validate(result, timestamp):
 p=ROOT/'Qianqian/Flux_Comparison_Surface_Reflectance_Data'/f'flux_comparison_results_raz_ceres_{timestamp}.pkl'
 if not p.exists():return {'reference_exists':False}
 with p.open('rb') as f: ref=pickle.load(f)
 report={'reference_exists':True,'reference_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fields':{}}
 for k,v in result.items():
  if k not in ref or k=='EMIT_time_stamp':continue
  a=np.asarray(v);b=np.asarray(ref[k])
  if a.shape!=b.shape:report['fields'][k]={'shape':list(a.shape),'reference_shape':list(b.shape),'shape_match':False};continue
  mask=np.isfinite(a)&np.isfinite(b)
  report['fields'][k]={'shape_match':True,'nan_pattern_equal':bool(np.array_equal(np.isnan(a),np.isnan(b))),
   'max_absolute_difference':float(np.max(np.abs(a[mask]-b[mask]))) if mask.any() else None,
   'allclose_rtol1e-5_atol1e-4':bool(np.allclose(a,b,rtol=1e-5,atol=1e-4,equal_nan=True))}
 return report


def run_case(timestamp,lpfs,asdcfs,include_rfl=False):
 outdir=ROOT/'outputs/raw_reproduction'/timestamp;outdir.mkdir(parents=True,exist_ok=True)
 start=time.monotonic(); tables=adm_tables(); obsurl=emit_url(timestamp,'OBS');radurl=emit_url(timestamp,'RAD')
 provenance={'timestamp':timestamp,'OBS':obsurl,'RAD':radurl,'rules':'Five hourly CERES files; last spatial match wins; +/-0.3 deg scene-center box; clear fraction >=100%; 20 km radius; original azimuth and ADM bin rules; UV=1.01*F(lambda<=420)+4.86.'}
 with ExitStack() as stack:
  obs=open_h5(stack,lpfs,obsurl)
  lon=values(obs['location/lon']);lat=values(obs['location/lat']);geo=values(obs['obs'])
  log(timestamp,'OBS loaded',geo.shape,'scene center',float(lon.mean()),float(lat.mean()))
  t=dt.datetime.strptime(timestamp,'%Y%m%dT%H%M%S')
  dates=[t+dt.timedelta(hours=i) for i in range(-2,3)]
  with ThreadPoolExecutor(max_workers=5) as pool: cs=list(pool.map(lambda date:read_ceres(asdcfs,date),dates))
  matches=[]
  for url,c in cs:
   clat=90.0-c['colat'];clon=np.where(c['lon']>180,c['lon']-360,c['lon'])
   mask=(clat>lat.mean()-.3)&(clat<lat.mean()+.3)&(clon>lon.mean()-.3)&(clon<lon.mean()+.3)
   if mask.any():matches.append((url,c,mask))
  provenance['candidate_CERES_urls']=[url for url,_ in cs]
  provenance['spatial_matches']=[{'url':url,'footprints':int(mask.sum())} for url,_,mask in matches]
  if not matches:raise RuntimeError('No CERES spatial matches')
  url,c,mask=matches[-1]
  selected=mask&(c['clear'][:,0]>=100)
  indices=np.flatnonzero(selected)
  provenance['selected_CERES_url']=url;provenance['CERES_indices']=indices.tolist()
  log(timestamp,'Selected CERES',url.rsplit('/',1)[-1],len(indices),'clear footprints')
  np.savez_compressed(outdir/'collocation.npz',CERES_indices=indices,spatial_mask=mask)
  keys=['CERES_Lon','CERES_Lat','CERES_S0','CERES_Fup_based_on_ADM_filtered','CERES_Fup_based_on_ADM_unfiltered','CERES_Fup','CERES_Fdn','CERES_Ref','CERES_Sza','CERES_Vza','CERES_Raz','EMIT_Fup','EMIT_Fup_fullspectrum','EMIT_Fdn','EMIT_Ref','EMIT_Sza','EMIT_Vza','EMIT_Raz','EMIT_Adm','EMIT_wvl','EMIT_surface_reflectance_flatten','EMIT_surface_reflectance']
  result={k:[] for k in keys};result['EMIT_time_stamp']=timestamp
  s0=np.nanmean(c['incoming'][selected]/np.cos(np.radians(c['sza'][selected])))
  result['CERES_S0']=[s0]
  rad=open_h5(stack,lpfs,radurl);wl=values(rad['sensor_band_parameters/wavelengths'])
  units=rad['radiance'].attrs['units'];units=units.decode() if isinstance(units,bytes) else str(units)
  if units!='uW/cm^2/SR/nm':raise ValueError(f'Unrecognized radiance units {units}')
  provenance['radiance_units']=units;provenance['radiance_shape']=list(rad['radiance'].shape)
  log(timestamp,'Reading radiance once',rad['radiance'].shape)
  radiance=read_cube(lpfs,radurl,rad['radiance'])
  log(timestamp,'Radiance loaded after',round(time.monotonic()-start,1),'seconds')
  spectra=[]; counts=[];masks=[]
  for idx in indices:
   lon0=c['lon'][idx];lat0=np.float64(90.0)-np.float64(c['colat'][idx])
   pix=distance(lon0,lat0,lon,lat)<=20.;n=int(pix.sum());counts.append(n);masks.append(pix)
   if n==0:raise ValueError('Empty EMIT footprint')
   spec=radiance[pix].mean(axis=0);spectra.append(spec)
   sza=geo[:,:,4][pix].mean();vza=geo[:,:,2][pix].mean();raz=np.float64(180.)-np.float64(geo[:,:,1][pix].mean()-geo[:,:,3][pix].mean())
   r=adm(tables,sza,vza,raz);rc=adm(tables,c['sza'][idx],c['vza'][idx],c['raz'][idx])
   f=np.float64(np.trapezoid(spec,wl))*np.pi/100./r
   short=wl<=420;uv=1.01*np.float64(np.trapezoid(spec[short],wl[short]))*np.pi/100./r+4.86
   fdn=s0*np.cos(np.radians(sza))
   vals={'CERES_Lon':lon0,'CERES_Lat':lat0,'CERES_Fup_based_on_ADM_filtered':c['filtered'][idx]/rc*np.pi,
    'CERES_Fup_based_on_ADM_unfiltered':c['radiance'][idx]/rc*np.pi,'CERES_Fup':c['flux'][idx],
    'CERES_Fdn':c['incoming'][idx],'CERES_Ref':c['flux'][idx]/c['incoming'][idx],
    'CERES_Sza':c['sza'][idx],'CERES_Vza':c['vza'][idx],'CERES_Raz':c['raz'][idx],
    'EMIT_Fup':f,'EMIT_Fup_fullspectrum':f+uv,'EMIT_Fdn':fdn,'EMIT_Ref':f/fdn,
    'EMIT_Sza':sza,'EMIT_Vza':vza,'EMIT_Raz':raz,'EMIT_Adm':r}
   for k,v in vals.items():result[k].append(v)
  del radiance
  if include_rfl:
   rflurl=emit_url(timestamp,'RFL');rfl=open_h5(stack,lpfs,rflurl);provenance['RFL']=rflurl
   rwl=values(rfl['sensor_band_parameters/wavelengths']);cube=read_cube(lpfs,rflurl,rfl['reflectance'])
   for pix in masks:
    a=cube[pix];result['EMIT_surface_reflectance'].append(np.nanmean(np.where(a>0,a,np.nan),axis=0));result['EMIT_wvl'].append(rwl)
   del cube
  # Keep compact spatial subset for rebuilding the footprint map, not raw cubes.
  np.savez_compressed(outdir/'spectra_and_geometry.npz',wavelength_nm=wl,mean_radiance=np.array(spectra),
   lon=lon[::4,::4],lat=lat[::4,::4],EMIT_pixel_counts=counts)
  provenance['EMIT_pixel_counts']=counts;provenance['elapsed_seconds']=time.monotonic()-start
  provenance['include_surface_reflectance']=include_rfl
 with (outdir/f'flux_comparison_results_raz_ceres_{timestamp}.pkl').open('wb') as f:pickle.dump(result,f)
 report=validate(result,timestamp)
 if not include_rfl:
  report['omitted_fields']=['EMIT_wvl','EMIT_surface_reflectance']
  for key in report['omitted_fields']: report.get('fields',{}).pop(key,None)
 (outdir/'validation.json').write_text(json.dumps(report,indent=2))
 (outdir/'provenance.json').write_text(json.dumps(provenance,indent=2))
 log(timestamp,'DONE',round(provenance['elapsed_seconds'],1),'seconds')
 print(json.dumps(report,indent=2),flush=True)
 return result,report


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('timestamp',nargs='?',default='20230401T094135');p.add_argument('--include-rfl',action='store_true');args=p.parse_args()
 if not earthaccess.login(strategy='netrc',persist=False).authenticated:raise RuntimeError('Authentication failed')
 lpfs=earthaccess.get_s3_filesystem(provider='LPCLOUD');asdcfs=earthaccess.get_s3_filesystem(provider='LARC_CLOUD')
 run_case(args.timestamp,lpfs,asdcfs,args.include_rfl)


if __name__=='__main__':main()
