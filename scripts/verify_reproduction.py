"""Independently recheck every reconstructed case and the final comparison, offline."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import pickle
from pathlib import Path

import numpy as np
from replicate_raw_case import ROOT, manifest_name, validate

OUT = ROOT / 'outputs/raw_reproduction'
REFERENCE = ROOT / 'Qianqian/Flux_Comparison_Surface_Reflectance_Data'
REQUIRED = (
    'CERES_Lon CERES_Lat CERES_S0 CERES_Fup_based_on_ADM_filtered '
    'CERES_Fup_based_on_ADM_unfiltered CERES_Fup CERES_Fdn CERES_Ref '
    'CERES_Sza CERES_Vza CERES_Raz EMIT_Fup EMIT_Fup_fullspectrum '
    'EMIT_Fdn EMIT_Ref EMIT_Sza EMIT_Vza EMIT_Raz EMIT_Adm'
).split()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-comparison', action='store_true')
    args = parser.parse_args()
    refs = sorted(REFERENCE.glob('flux_comparison_results_raz_ceres_*.pkl'))
    check(len(refs) == 577, f'Expected historical 577-case scope, found {len(refs)}')
    inventory, differences = [], {}
    records = 0
    rfl_cases = []
    for ref in refs:
        ts = ref.stem.rsplit('_', 1)[-1]
        case = OUT / ts
        result_path = case / ref.name
        for name in ['provenance.json', 'validation.json', 'spectra_and_geometry.npz', 'collocation.npz', ref.name]:
            check((case / name).is_file(), f'{ts}: missing {name}')
        provenance = json.loads((case / 'provenance.json').read_text())
        with result_path.open('rb') as stream:
            result = pickle.load(stream)  # Trusted local research artifacts only.
        check(set(REQUIRED).issubset(result), f'{ts}: missing required flux/geometry fields')
        check(result['EMIT_time_stamp'] == ts, f'{ts}: timestamp mismatch')
        fields = validate(result, ts)['fields']  # Fresh comparison, not cached validation.json.
        included = REQUIRED.copy()
        # The original pilot predates the explicit flag; its RFL URL is recorded.
        if provenance.get('include_surface_reflectance', 'RFL' in provenance):
            included += ['EMIT_wvl', 'EMIT_surface_reflectance']
            rfl_cases.append(ts)
        for key in included:
            v = fields[key]
            check(v.get('allclose_rtol1e-5_atol1e-4') and v.get('nan_pattern_equal'), f'{ts}: {key} differs')
            delta = v.get('max_absolute_difference')
            if delta is not None:
                differences[key] = max(differences.get(key, 0), delta)
        n = len(result['CERES_Lon'])
        records += n
        check(len(provenance['CERES_indices']) == n, f'{ts}: provenance footprint count differs')
        with np.load(case / 'collocation.npz') as c, np.load(case / 'spectra_and_geometry.npz') as g:
            check(np.array_equal(c['CERES_indices'], provenance['CERES_indices']), f'{ts}: CERES indices differ')
            check(np.array_equal(g['EMIT_pixel_counts'], provenance['EMIT_pixel_counts']), f'{ts}: pixel counts differ')
            check(g['mean_radiance'].shape == (n, len(g['wavelength_nm'])), f'{ts}: spectrum shape differs')
        rad, obs = manifest_name(ts, 'RAD'), manifest_name(ts, 'OBS')
        check(provenance['RAD'].endswith('/' + rad) and provenance['OBS'].endswith('/' + obs), f'{ts}: manifest differs')
        inventory.append({'timestamp': ts, 'RAD': rad, 'OBS': obs,
                          'reference_sha256': sha(ref), 'result_sha256': sha(result_path),
                          'selected_CERES_url': provenance['selected_CERES_url']})
    check(records == 4844, f'Expected 4844 records, found {records}')
    check('20230401T094135' in rfl_cases, 'Pilot RFL branch has not been reproduced; run pilot --include-rfl')
    comparison_checked = False
    if args.check_comparison:
        actual = json.loads((OUT / 'comparison/summary.json').read_text())
        baseline = json.loads((ROOT / 'docs/raw_flux_comparison_summary.json').read_text())
        for key in ['files', 'total_footprint_records', 'excluded_files_over20', 'retained_files',
                    'records_after_file_filter', 'legacy_land_records', 'nan_reflectance_records',
                    'final_records', 'final_scenes', 'longitude_diagnostic']:
            check(actual[key] == baseline[key], f'Comparison selection changed: {key}')
        for group in ['direct', 'solar_angle_adjusted']:
            for key, value in baseline[group].items():
                check(np.isclose(actual[group][key], value, rtol=1e-10, atol=1e-10), f'Fit changed: {group}/{key}')
        def selected(path):
            with path.open() as stream:
                return {(r['source_file'], r['source_index']) for r in csv.DictReader(stream) if r['selected'] == 'True'}
        check(selected(OUT / 'comparison/footprint_selection.csv') ==
              selected(ROOT / 'outputs/saved_flux_comparison/footprint_selection.csv'),
              'Selected record identities differ from the saved-result reproduction')
        check(all(actual['matches_manuscript_to_printed_precision'].values()), 'Manuscript fit labels differ')
        comparison_checked = True
    tracked_inputs = [ROOT / 'EMIT_L1B.txt', ROOT / 'EMIT_L2A.txt'] + sorted((ROOT / 'Zhibo/Leob2005_ADM').glob('*.csv'))
    script_paths = sorted((ROOT / 'scripts').glob('*.py'))
    report = {'verified_cases': len(refs), 'verified_records': records,
              'fresh_field_comparison': True, 'comparison_checked': comparison_checked,
              'rtol': 1e-5, 'atol': 1e-4, 'maximum_absolute_differences': differences,
              'surface_reflectance_cases': rfl_cases,
              'input_sha256': {str(p.relative_to(ROOT)): sha(p) for p in tracked_inputs},
              'script_sha256': {str(p.relative_to(ROOT)): sha(p) for p in script_paths},
              'environment': {k: importlib.metadata.version(k) for k in
                              ['numpy', 'scipy', 'matplotlib', 'basemap', 'basemap-data', 'earthaccess', 'h5py', 'pyhdf', 's3fs', 'fsspec']}}
    (OUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'case_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print(f'PASS: {len(refs)} cases / {records} records; fresh field checks; comparison checked={comparison_checked}')


if __name__ == '__main__':
    main()
