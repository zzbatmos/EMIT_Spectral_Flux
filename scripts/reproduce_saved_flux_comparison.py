"""Reproduce Qianqian's two comparisons from the supplied trusted pickle results.

Preserves the original >20-footprint file exclusion, Basemap() land test on
unmodified longitudes, and NaN-reflectance mask. No new geographical filtering.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
from pathlib import Path
import pickle

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
from scipy.stats import linregress

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('CERES_Lon', 'CERES_Lat', 'CERES_Sza', 'EMIT_Sza', 'CERES_Ref',
          'CERES_Fup', 'CERES_Fdn', 'EMIT_Fup_fullspectrum', 'EMIT_Fdn')


def fit(x, y):
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Historical mask leaves nonfinite fluxes; do not silently change selection')
    r = linregress(x, y)
    d = y-x
    return dict(n=len(x), slope=float(r.slope), intercept_W_m2=float(r.intercept),
                pearson_r=float(r.rvalue), r_squared=float(r.rvalue**2),
                pvalue=float(r.pvalue), slope_stderr=float(r.stderr),
                mean_emit_minus_ceres_W_m2=float(d.mean()),
                difference_std_ddof0_W_m2=float(d.std()), rmse_W_m2=float(np.sqrt(np.mean(d*d))))


def panel(ax, x, y, stats, adjusted=False, colors=None):
    opts = dict(marker='.', s=14, linewidths=0)
    if colors is None:
        sc = ax.scatter(x, y, color='royalblue', **opts)
    else:
        sc = ax.scatter(x, y, c=colors, cmap='bwr', vmin=-20, vmax=20, **opts)
    xx = np.array([0., 550.])
    ax.plot(xx, xx, color='black', lw=1, label='1:1')
    ax.plot(xx, stats['slope']*xx+stats['intercept_W_m2'], color='red', lw=1.4, label='Linear fit')
    ax.text(.04, .95, f"y = {stats['slope']:.2f}x + {stats['intercept_W_m2']:.2f}\n"
            f"R = {stats['pearson_r']:.2f}; N = {stats['n']:,}",
            transform=ax.transAxes, va='top', color='red', fontsize=11)
    ax.set(xlim=(0,550), ylim=(0,550),
           xlabel=('CERES flux at EMIT solar zenith angle' if adjusted else 'CERES upward SW flux') + ' [W m$^{-2}$]',
           ylabel='EMIT upward flux, 315 nm–2.5 μm [W m$^{-2}$]',
           title='Solar-angle-adjusted comparison' if adjusted else 'Direct comparison')
    ax.set_aspect('equal', adjustable='box')
    return sc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=ROOT/'Qianqian/Flux_Comparison_Surface_Reflectance_Data')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'outputs/saved_flux_comparison')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows, manifest = [], []
    files = sorted(args.input_dir.glob('flux_comparison_results_raz_ceres_*.pkl'))
    if not files:
        raise FileNotFoundError(args.input_dir)
    for path in files:
        payload = path.read_bytes()
        data = pickle.loads(payload)  # Supplied project artifacts; never use untrusted pickles.
        n = len(data['CERES_Lon'])
        if any(len(data[k]) != n for k in FIELDS):
            raise ValueError(f'Inconsistent field lengths: {path}')
        manifest.append(dict(file=path.name, sha256=hashlib.sha256(payload).hexdigest(),
                             footprints=n, file_selected=0<n<=20))
        for i in range(n):
            row = dict(source_file=path.name, source_index=i, emit_timestamp=data['EMIT_time_stamp'],
                       file_selected=0<n<=20)
            row.update({k:float(data[k][i]) for k in FIELDS})
            rows.append(row)
    candidates = [r for r in rows if r['file_selected']]
    a = {k:np.array([r[k] for r in candidates]) for k in FIELDS}
    m = Basemap()  # Preserve original cylindrical projection, crude resolution and domain.
    land = np.array([m.is_land(lon,lat) for lon,lat in zip(a['CERES_Lon'],a['CERES_Lat'])])
    with np.errstate(divide='ignore', invalid='ignore'):
        emit_ref = a['EMIT_Fup_fullspectrum']/a['EMIT_Fdn']
    nonnan = ~np.isnan(a['CERES_Ref']) & ~np.isnan(emit_ref)
    selected = land & nonnan
    if selected.sum()<2:
        raise ValueError('Insufficient selected points')
    x = a['CERES_Fup'][selected]
    y = a['EMIT_Fup_fullspectrum'][selected]
    xa = (a['EMIT_Fdn']*a['CERES_Ref'])[selected]
    ya = (a['EMIT_Fdn']*emit_ref)[selected]  # Preserve original expression.
    colors = (a['EMIT_Sza']-a['CERES_Sza'])[selected]
    direct, adjusted = fit(x,y), fit(xa,ya)
    # Diagnostic only: demonstrate whether longitude wrapping changes selection.
    wrapped = (a['CERES_Lon']+180)%360-180
    wrapped_land = np.array([m.is_land(lon,lat) for lon,lat in zip(wrapped,a['CERES_Lat'])])
    for row, is_land, ok, keep in zip(candidates,land,nonnan,selected):
        row.update(legacy_land=bool(is_land), nonnan_reflectances=bool(ok), selected=bool(keep))
    for row in rows:
        row.setdefault('legacy_land',''); row.setdefault('nonnan_reflectances',''); row.setdefault('selected',False)
    summary = {
        'input_directory':str(args.input_dir), 'files':len(files), 'total_footprint_records':len(rows),
        'excluded_files_over20':sum(f['footprints']>20 for f in manifest),
        'excluded_empty_files':sum(f['footprints']==0 for f in manifest),
        'retained_files':sum(f['file_selected'] for f in manifest),
        'records_after_file_filter':len(candidates), 'legacy_land_records':int(land.sum()),
        'nan_reflectance_records':int((~nonnan).sum()), 'final_records':int(selected.sum()),
        'final_scenes':len({r['emit_timestamp'] for r in candidates if r['selected']}),
        'direct':direct, 'solar_angle_adjusted':adjusted,
        'longitude_diagnostic':{'candidate_longitudes_over180':int((a['CERES_Lon']>180).sum()),
                                'land_classifications_changed_by_wrapping':int((land!=wrapped_land).sum()),
                                'selected_if_wrapped':int((wrapped_land & nonnan).sum()),
                                'baseline_uses_wrapping':False},
        'manuscript_rounded_targets':{'direct':[1.08,1.23,0.93],'adjusted':[1.00,12.49,0.98]},
        'notebook_saved_adjusted_difference':{'mean_W_m2':12.954575148441972,'std_W_m2':14.627227186615482},
        'environment':{k:importlib.metadata.version(k) for k in ['numpy','scipy','matplotlib','basemap','basemap-data']},
        'selection':'Original file-size exclusion, Basemap() on unchanged CERES longitudes, non-NaN reflectances. No extra Sahara bounding box, deduplication, or outlier filter.',
        'scope':'Replotting saved derived fluxes; no independent validation of raw-data collocation, ADM, or UV correction.'}
    for key,stats in [('direct',direct),('adjusted',adjusted)]:
        summary.setdefault('matches_manuscript_to_printed_precision',{})[key] = [round(stats['slope'],2),round(stats['intercept_W_m2'],2),round(stats['pearson_r'],2)] == summary['manuscript_rounded_targets'][key]
    (args.output_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (args.output_dir/'input_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (args.output_dir/'footprint_selection.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    for name,xx,yy,stats,adj in [('direct_comparison',x,y,direct,False),('solar_angle_adjusted_comparison',xa,ya,adjusted,True)]:
        fig,ax=plt.subplots(figsize=(6.7,5.5),layout='constrained')
        sc=panel(ax,xx,yy,stats,adj,None if adj else colors)
        if not adj: fig.colorbar(sc,ax=ax,label='Solar zenith angle: EMIT − CERES [°]',shrink=.8)
        for ext in ['png','pdf']: fig.savefig(args.output_dir/f'{name}.{ext}',dpi=220)
        plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(13,5.6),layout='constrained')
    sc=panel(axs[0],x,y,direct,False,colors); panel(axs[1],xa,ya,adjusted,True)
    fig.colorbar(sc,ax=axs[0],label='EMIT − CERES solar zenith angle [°]',shrink=.8)
    fig.suptitle('EMIT–CERES comparison · Reproduced from Qianqian’s saved April 2023 results',fontsize=14)
    for ext in ['png','pdf']: fig.savefig(args.output_dir/f'comparison_pair.{ext}',dpi=220)
    plt.close(fig)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
