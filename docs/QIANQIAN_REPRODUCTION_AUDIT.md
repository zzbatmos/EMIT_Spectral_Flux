# Qianqian workflow reproduction audit

Reviewed 2026-09-27. Static review of `Qianqian/EMIT_CERES_Collocation_Map.py`, its notebook outputs, `EMIT_CERES_FupTOA_Comparison.py`, the local readers and ADM tables, and the saved result dictionaries. The historical analysis was not executed or modified.

## Two distinct reproduction targets

1. **Replot saved comparisons:** 577 result dictionaries already exist in `Qianqian/Flux_Comparison_Surface_Reflectance_Data/`. They contain 4,844 footprint records. The comparison script drops files with more than 20 records, leaving 2,324 records before its land and NaN masks. Files span April 1–27, 2023. Their keys include both instruments' fluxes, incoming flux, geometry, EMIT ADM, and mean surface-reflectance spectra. No new raw satellite data are necessary for this target. Exact regression reproduction still requires the same selection/land mask. The map notebook reports 1,782 collocation cases; the saved 577 outputs should not automatically be assumed to be the complete/latest intended sample.
2. **Recompute from observations:** requires the April 2023 scene manifest, EMIT RAD/OBS (and RFL for the surface-reflectance outputs), Terra-FM2 SSF granules, and either original collocation files or their reconstruction.

## Data inventory

| Input | Role | Status |
|---|---|---|
| EMIT L1B V001 RAD and OBS, April 2023 | Radiance, wavelengths, geolocation, viewing/solar geometry | Direct S3 access demonstrated; exact original set remains to be reconstructed |
| EMIT L2A V001 RFL | Mean surface-reflectance spectra saved by the script | Needed to reproduce all fields; not required by the TOA radiance-to-flux calculation itself |
| CERES Terra-FM2 MODIS SSF Edition4A, April 2023 | Reference SW flux/radiance, incoming radiation, cloud fraction, time, and geometry | Required raw files not found in inspected Research/Data trees |
| `EMIT_2023_04_L1B_file_list_taki.txt` | Original selection and OBS/RAD pairing | Not found; script splits it into two equal lists and assumes matching order |
| `EMIT_CERES_collocation_taki/EMIT_TERRA_CERES_collocation/*.pkl` | Exact CERES filenames and footprint indices for each EMIT scene | Not found; outputs themselves do not retain these source filenames/indices |
| Loeb ADM CSV tables and reader | Bright-desert anisotropic factors | Present in `Zhibo/Leob2005_ADM/`; reader paths require repair |
| `kurudz_1.0nm.dat` | Original solar-spectrum helper | Candidate at `/home/ssm-user/Research/PACE_ACA_project/kurudz_1.0nm.dat`; identity with historical input unverified |
| `EMIT_wavelength.npz` | Solar-spectrum interpolation grid | Not found; equivalent coordinates can be taken from an EMIT granule |
| OCI UV-regression training observations | Provenance of missing-UV correction | Not needed to replay hardcoded coefficients; needed to independently validate or refit them |

Notebook output in `Zhibo/EMIT_CERES_collocation.ipynb` identifies files such as `CER_SSF_Terra-FM2-MODIS_Edition4A_407405.2023042509.hdf`. This is evidence for the historical edition/build, not proof of every source file used by Qianqian.

The available 1,229 HDF files under `/home/ssm-user/Research/EMIT_dust_DRE/CERES_SSF/` are **Aqua-FM3, June–August 2023**, and are not substitutes for the April Terra-FM2 baseline. Nearby NOAA20 SSF1deg files are also a different product. NASA identifies the required footprint product here: https://data.nasa.gov/dataset/ceres-single-scanner-footprint-ssf-toa-surface-fluxes-clouds-and-aerosols-terra-fm2-editio-6244a .

## What the code actually does

- Map script lines 162–186: reads the April file list and pairs the first half (OBS) with the second half (RAD).
- Lines 192–294: searches hourly Terra-FM2 files at hour offsets -2 through +2 around each EMIT timestamp; tests CERES centers against an EMIT mean-coordinate box of ±0.3°. It does **not** enforce an exact per-footprint ±2-hour tolerance. Multiple matching CERES files overwrite the same timestamp-named pickle; only the last written match survives.
- Lines 307–428: selects 100%-clear CERES footprints; maps EMIT pixels within 20 km. Map-only selection includes 10–30°N, -10–40°E and more than one clear footprint per case; plotting extent is 25–30°E, 15–20°N. It exits the process at 100 collected centers, before reaching plotting or flux code in a clean script run. Unsorted file order can affect this map subset.
- Lines 472–620: independently loops over collocation files, applies the clear-fraction and 20 km rules, averages radiance and geometry, looks up a broadband desert ADM, and computes `F_EMIT = pi * integral(I_lambda d_lambda) / (100 * ADM)`. The factor 1/100 is consistent with the units observed in our tested EMIT granule (`uW/cm^2/sr/nm` to `W/m^2/sr/nm`). Verify metadata for every input product.
- UV addition: `F_315_380 = 1.01 * F_EMIT_lambda<=420 + 4.86`. The actual mask has no explicit lower limit; the native first wavelength supplies it. This differs from the draft's 381–440 nm predictor. Preserve the coefficients for historical replay, then separately investigate their provenance.
- The flux loop does **not** apply the map section's Sahara bounds or >1-clear-footprint criterion. Saved latitude values span approximately 8.89–36.59°N and longitudes remain in the CERES 0–360° convention. The land mask must handle that convention consistently.
- The separate comparison script excludes cases with >20 footprints, constructs a Basemap land mask, rejects NaN reflectances, and plots both raw and solar-angle-adjusted comparisons. Its adjusted CERES x-coordinate is `EMIT_Fdn * CERES_Fup / CERES_Fdn`; y is UV-corrected EMIT upward flux. The map script saves results but does not generate these scatterplots.

## Code/environment repairs before a clean rerun

- Replace legacy `/umbc/...` and `../EMIT_project_Zhibo/...` paths with explicit configuration and S3 readers; reconcile collocation write/read directories and create output directories.
- Import `CERES_SSF` from the available `Zhibo/CERES_lib.py`; it is not defined by the current EMIT helper import.
- Restore ADM initialization (currently commented out). Both provided ADM readers use working-directory-dependent table paths. Despite the name `interpolate_ADM`, the method performs angle-bin lookup with `searchsorted`, not continuous interpolation; preserve that behavior for baseline reproduction.
- Restore or eliminate the undefined `KS` dependency. In this script `KS.solar_constant` cancels exactly: `EMIT_Fdn = CERES_S0 * cos(EMIT_SZA)`. Thus the external solar spectrum and NPZ are not necessary for the flux comparison after this algebraically equivalent simplification, though the original solar diagnostic plot needs them.
- Remove the map section's process exit and separate map/flux/comparison stages. Add safe handling for missing files, empty selections, NaNs/fill values, and azimuth normalization, without silently changing baseline sample selection.
- Replace removed `np.trapz` with `np.trapezoid` and compare numerical results.
- Use an HDF4-capable CERES reader. A local CERES SSF file opens with `pyhdf`, but this environment's xarray `engine='netcdf4'` fails with NetCDF error -128 (HDF4 support not enabled). The current CERES helper exposes only some fields; extend its variable selection for all required flux, cloud, and geometry fields.
- The comparison script needs Basemap (absent) for the original land mask; replacing its coastline/mask may alter samples. `mpl_scatter_density` is imported but not used in these plots, so that import can be removed. Its `Colorbar.set_clim` call also needs updating to the mappable API. Figure output paths need repair.
- Read EMIT spatial blocks once and reuse spectra for overlapping footprints; avoid repeated full-cube `.values` access per CERES footprint.

## Recommended order

First reproduce plots and counts from the 577 saved dictionaries, keeping originals untouched. Then select one of their actual EMIT timestamps, recover the corresponding Terra-FM2 hourly SSF files, rebuild its collocation, and compare intermediate quantities against that saved result. Only after this case agrees should we expand to April. Recovering the original scene manifest and collocation pickles from the historical UMBC workspace would make exact sample and source-file reproduction substantially more reliable.
