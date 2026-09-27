"""Audit completed raw cases, link recomputed results, and plot a collocation map."""
from pathlib import Path
import argparse
import json
import pickle
import collections

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
from scipy.spatial import ConvexHull

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/raw_reproduction'


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--require-complete',action='store_true');args=parser.parse_args()
 expected=sorted(p.stem.rsplit('_',1)[-1] for p in (ROOT/'Qianqian/Flux_Comparison_Surface_Reflectance_Data').glob('*.pkl'))
 completed=[];issues=[];maxdiff={};records=0;nan_mismatches=[]
 links=OUT/'flux_results';links.mkdir(exist_ok=True)
 for ts in expected:
  case=OUT/ts
  if not (case/'provenance.json').exists() or not (case/'validation.json').exists():continue
  validation=json.loads((case/'validation.json').read_text())
  with (case/f'flux_comparison_results_raz_ceres_{ts}.pkl').open('rb') as f: result=pickle.load(f)
  completed.append(ts);records+=len(result['CERES_Lon'])
  for k,v in validation['fields'].items():
   if not v.get('allclose_rtol1e-5_atol1e-4',False):issues.append({'timestamp':ts,'field':k,**v})
   delta=v.get('max_absolute_difference')
   if delta is not None:maxdiff[k]=max(maxdiff.get(k,0),delta)
   if not v.get('nan_pattern_equal',True):nan_mismatches.append({'timestamp':ts,'field':k})
  link=links/f'flux_comparison_results_raz_ceres_{ts}.pkl'
  if not link.exists():link.symlink_to(Path('..')/ts/link.name)
 summary={'expected_cases':len(expected),'completed_cases':len(completed),'recomputed_footprint_records':records,
  'missing_cases':sorted(set(expected)-set(completed)), 'discrepancies_beyond_rtol1e-5_atol1e-4':issues,
  'nan_pattern_mismatches':nan_mismatches,'maximum_absolute_differences_by_field':maxdiff,
  'method':'Rebuilt hourly CERES matching, spatial masks and EMIT radiance-to-flux calculations from S3. Historical derived fluxes are read only for validation after computation.',
  'surface_reflectance_scope':'Recomputed for pilot 20230401T094135 only; batch reproduces TOA flux fields.',
  'historical_input_scope':'The 577 saved-case timestamps, not every April EMIT scene. All source filenames come from supplied EMIT_L1B.txt and EMIT_L2A.txt.'}
 (OUT/'raw_validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
 if args.require_complete and len(completed)!=len(expected):raise RuntimeError('Batch incomplete')
 if args.require_complete and (issues or nan_mismatches):raise RuntimeError('Raw validation failed; inspect raw_validation_summary.json')
 # Recreate the geographic swath illustrated in the draft, with computed masks.
 timestamps=['20230401T094111','20230401T094123','20230401T094135','20230401T094147','20230401T094159','20230401T094211']
 fig,ax=plt.subplots(figsize=(7,9),layout='constrained');mapped=0
 for ts in timestamps:
  case=OUT/ts;npz=case/'spectra_and_geometry.npz'
  if not npz.exists():continue
  with (case/f'flux_comparison_results_raz_ceres_{ts}.pkl').open('rb') as f:r=pickle.load(f)
  g=np.load(npz);lon=g['lon'];lat=g['lat']
  for lon0,lat0 in zip(r['CERES_Lon'],r['CERES_Lat']):
   a=np.sin(np.radians(np.float64(lat0)))*np.sin(np.radians(lat))+np.cos(np.radians(np.float64(lat0)))*np.cos(np.radians(lat))*np.cos(np.radians(lon0-lon))
   mask=6371*np.arccos(np.clip(a,-1,1))<=20
   points=np.column_stack((lon[mask],lat[mask]))
   if len(points)<3:continue
   hull=ConvexHull(points)
   ax.add_patch(Polygon(points[hull.vertices],fc='tomato',ec='darkred',alpha=.35,lw=.5,label='EMIT pixels within 20 km' if mapped==0 else None))
   ax.scatter(lon0,lat0,s=11,c='royalblue',label='CERES center' if mapped==0 else None,zorder=4)
   mapped+=1
 ax.set(xlim=(25,30),ylim=(15,20),xlabel='Longitude (°E)',ylabel='Latitude (°N)',title=f'EMIT–CERES collocation rebuilt from raw data\n1 April 2023 · {mapped} clear CERES footprints')
 ax.set_aspect(1/np.cos(np.radians(17.5)));ax.grid(alpha=.25);ax.legend(loc='lower left',fontsize=9)
 fig.savefig(OUT/'raw_collocation_map.png',dpi=200);fig.savefig(OUT/'raw_collocation_map.pdf');plt.close(fig)
 # Pilot spectral flux retains the original wavelength-independent ADM assumption.
 case=OUT/'20230401T094135'
 with (case/'flux_comparison_results_raz_ceres_20230401T094135.pkl').open('rb') as f:r=pickle.load(f)
 g=np.load(case/'spectra_and_geometry.npz');f=np.pi*g['mean_radiance']/100/np.array(r['EMIT_Adm'])[:,None]
 fig,ax=plt.subplots(figsize=(10,4.6),layout='constrained')
 for i,spectrum in enumerate(f):ax.plot(g['wavelength_nm'],spectrum,lw=.8,label=f'Footprint {i+1}')
 ax.set(xlabel='Wavelength [nm]',ylabel='Upward spectral flux [W m$^{-2}$ nm$^{-1}$]',title='EMIT-derived spectral flux · 1 April 2023, 09:41:35 UTC\nNine CERES footprints; historical broadband desert ADM')
 ax.legend(ncol=3,fontsize=8);ax.grid(alpha=.2)
 fig.savefig(OUT/'pilot_spectral_flux.png',dpi=200);plt.close(fig)


if __name__=='__main__':main()
