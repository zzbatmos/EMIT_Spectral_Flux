# Reproduction of Qianqian's saved flux comparisons

Completed 2026-09-27 using all 577 supplied pickle files. The fitted lines and correlations reproduce both manuscript figures to their printed precision. The adjusted difference mean and population standard deviation match the saved notebook output to displayed machine precision. This verifies the saved-results-to-figure step; raw-data collocation, radiance integration, ADM and UV calibration were not independently rerun.

## Results

| Statistic | Direct comparison | Solar-angle-adjusted comparison |
|---|---:|---:|
| Footprint records | 1,482 | 1,482 |
| Slope | 1.0804130275 | 1.0013830653 |
| Intercept (W m^-2) | 1.2339097478 | 12.4882035361 |
| Pearson R | 0.9343405530 | 0.9776101158 |
| Mean EMIT minus CERES (W m^-2) | 27.2034989119 | 12.9545751484 |
| Difference standard deviation, ddof=0 (W m^-2) | 25.2398342123 | 14.6272271866 |
| RMSE (W m^-2) | 37.1090229474 | 19.5391093053 |

Manuscript labels are respectively `y = 1.08x + 1.23, R = 0.93` and `y = 1.00x + 12.49, R = 0.98`. Notebook residual outputs are exactly `12.954575148441972` and `14.627227186615482`, reproduced here.

The adjusted comparison uses `x = EMIT_Fdn * CERES_Ref` and `y = EMIT_Fdn * (EMIT_Fup_fullspectrum / EMIT_Fdn)`. The direct comparison uses saved CERES upward flux versus saved UV-corrected EMIT upward flux. The solar-angle adjustment improves agreement but leaves a positive mean difference of about 13 W m^-2.

## Preserved selection

- 577 files contain 4,844 footprint records.
- 51 files containing >20 records are excluded, exactly as in the original comparison code. The remaining 526 files contain 2,324 records.
- Default `Basemap()` and its `is_land(lon, lat)` classify 1,621 candidate records as land.
- The original joint mask rejects NaN CERES reflectance and NaN UV-corrected EMIT reflectance. There are 238 NaN-reflectance candidates in total, of which 139 are in the land subset.
- Final sample: 1,482 footprint records from 339 distinct EMIT timestamps. These are records, not necessarily independent or unique physical CERES footprints; no deduplication or additional Sahara bounding box was introduced.
- Data are sorted by source filename for deterministic output. Original scientific expressions and masks are preserved; unused imports and obsolete plotting API calls are omitted.

## Longitude issue discovered, not changed in the baseline

The saved CERES longitudes use 0–360°, while the default cylindrical Basemap covers -180–180°. The original code passes longitudes through unchanged. Of the 2,324 candidates, 653 have longitude >180°. Wrapping longitude to [-180,180) changes 637 land classifications and yields 2,022 final records instead of 1,482 (540 additional records). This is a separate selection correction to investigate next. The reproduced figures deliberately preserve the original selection, which is why the historical fits match.

## Reproduce and inspect

```bash
source scripts/activate.sh
python scripts/reproduce_saved_flux_comparison.py
```

Outputs under `outputs/saved_flux_comparison/`:

- `direct_comparison.png` and `.pdf`
- `solar_angle_adjusted_comparison.png` and `.pdf`
- `comparison_pair.png` and `.pdf`
- `summary.json`: counts, full-precision fits, diagnostics, and package versions
- `footprint_selection.csv`: every record, source file/index, saved quantities, and selection flags
- `input_manifest.json`: counts and SHA256 hashes for all 577 inputs

A tracked summary is saved at `docs/saved_flux_reproduction_summary.json`. The inherited scripts and pickle files were not edited.

Basemap 2.0.0 and basemap-data 2.0.0 were installed in `.venv`. The dependency resolver installed local NumPy 2.3.5, Matplotlib 3.10.9, pyproj 3.7.2, pyshp 2.3.1, and packaging 25.0, shadowing newer shared packages without modifying the shared conda environment. Core project import checks pass. `requirements-reproduction.txt` records the main reproduction versions; `docs/reproduction-environment.txt` records local venv overrides. The original environment snapshot remains a historical record of initial setup. Unrelated inherited GPy/TensorFlow/MKL dependency conflicts were reported by pip; those packages were not used in this task. The optional old numexpr warning persists. `np.trapz` is available again in this venv's NumPy 2.3.5, although migration to `np.trapezoid` remains appropriate for future code.
