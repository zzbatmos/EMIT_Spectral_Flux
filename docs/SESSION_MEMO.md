# Session memo

Last updated: 2026-09-27 (UTC).

## Execution context

We are working on an AWS instance (explicitly confirmed by Zhibo). Prefer direct S3 access to NASA EMIT data instead of downloading complete granules. Verify the runtime region and direct S3 file type during access. Shared helper libraries are in `/home/ssm-user/Research/python_lib/`, including `EMIT_lib.py` and `AWS_Utils.py`. Zhibo and research scientist Qianqian developed the inherited analyses; this work continues their unfinished project.

## Objective and source

Derive spectrally resolved upward TOA shortwave flux from EMIT hyperspectral observations, initially over the Sahara, with broadband validation against CERES. Longer-term motivation: use spectral dust direct radiative effects to distinguish particle-size and absorption/mineralogy effects that broadband flux alone cannot separate.

Read all 20 PDF pages of `references/EMIT Flux derivation.pdf`, including visual inspection of the embedded spectral and validation plots. Title: “Derivation of spectrally resolved flux at the top of the atmosphere from EMIT hyperspectral observations: methodology and validation with CERES.” It is an unfinished draft intended for AMT, with placeholders and incomplete uncertainty sections. PDF page numbers below count the title page as page 1.

## Scientific method in the draft

- EMIT: 285 bands, approximately 381–2493 nm, nominal spectral resolution 7.4 nm and spatial resolution 60 m (PDF p. 6).
- General relation: F_lambda = pi * I_lambda / R_lambda, where R is the dimensionless angular anisotropy factor and geometry comprises solar zenith, viewing zenith, and relative azimuth (pp. 10–12).
- Proposed approximation: F_lambda_EMIT = pi * I_lambda_EMIT / R_CERES, using a wavelength-independent CERES desert broadband ADM (Loeb 2005) at the EMIT geometry (p. 12). Broadband flux is the wavelength integral plus estimated UV energy. Broadband agreement cannot by itself validate the spectral ADM approximation.
- OCI supplies an empirical relationship between missing UV energy around 315–380 nm and EMIT-observed UV-blue energy at 381–440 nm (pp. 7–10). CERES is the validation reference and source of the ADM; the method does not fit EMIT flux directly to CERES validation flux.
- Contributions below roughly 314/315 nm and above 2493 nm are neglected in the draft. The reported 90.1% EMIT coverage refers to incoming solar irradiance, not necessarily reflected TOA energy (pp. 6–8).
- Validation uses Terra CERES SSF, with spatial/temporal collocation and solar-zenith-angle adjustment (pp. 10, 14–16).
- Dust DRE convention: DRE_TOA = F_up_clear - F_up_dust (p. 3).

## Reported results, not reproduced here

PDF p. 15 shows EMIT versus CERES flux: y = 1.08x + 1.23, R = 0.93. PDF p. 16 shows the comparison with CERES adjusted to EMIT solar zenith angle: y = 1.00x + 12.49, R = 0.98. Flux axes are W m^-2. Sample selection, exact correction, uncertainties, and provenance require reproduction before these can be treated as verified project results.

The draft requests UV-regression and desert-ADM methodology, missing-energy and ADM uncertainty analysis, and a near-dust-free versus dusty case over the same grid box (pp. 12–17).

## Inherited code and data

`Qianqian/` contains collocation/read-data, mapping, one-case spectral irradiance, and flux-comparison scripts and notebooks. Local pickle results and figures already exist. `Zhibo/` contains EMIT, CERES, MODIS and cloud-access helpers, exploratory notebooks, and Loeb ADM tables. Preserve both contributors' work.

Observed issues to resolve before scientific execution:

1. The draft uses a 381–440 nm UV-blue predictor, whereas `Qianqian/EMIT_CERES_Collocation_and_ReadData.py` names a 380–420 nm predictor and computes missing UV flux as `1.01 * EMIT_Fup_380_420 + 4.86` (around lines 326–330). Trace training data, exact mask, units, and fit provenance before adopting either formulation.
2. Draft boundaries alternate between 314 and 315 nm and between 380 and 381 nm; plots sometimes say 2.5 micrometers. Use actual wavelength coordinates and explicitly settle integration endpoints.
3. Spectral integration uses a `/100.0` conversion. Verify it against granule radiance units rather than copying it without unit analysis.
4. Code contains a CERES relative-azimuth transformation `180 - RAZ`, 20 km radial collocation, and a 100% clear-fraction threshold. Verify conventions, time tolerance, masks, coverage, and footprint weighting.
5. Hardcoded `/umbc/...` and `../EMIT_project_Zhibo/...` paths are not portable. Referenced solar-spectrum and collocation inputs are not provided at those expected paths.
6. Installed NumPy lacks `np.trapz`, which legacy scripts call. Plan explicit migration to `np.trapezoid` and scientific regression checks when modernizing the workflow.
7. Basemap and mpl-scatter-density are absent; these are optional legacy comparison-plot dependencies. Pandas reports an old optional numexpr version (2.10.1; it requests >=2.10.2). Core imports still succeed.

## Setup performed

- Initialized a local Git repository on `main`; no remote configured.
- Added README, project agent instructions, this memo, dependency manifests, activation script, and environment import check.
- Created `.venv` with system-site-packages from `/home/ssm-user/Codes/anaconda3/envs/PACE_EMIT/bin/python3` (Python 3.12.2). This reuses host packages and is not isolated from base-package updates. No shared packages were changed.
- Recorded installed distributions in `docs/environment-snapshot.txt`. The manifest is not a tested fresh-install lockfile.
- Routed Matplotlib and Jupyter caches to project-local `.cache` via activation.
- Excluded existing PEM keys, recovery-code files, data artifacts, and caches from Git. A filename-only credential-pattern scan flagged `Zhibo/AWS_Utils.py` and `Zhibo/AWS_NASA_data_test.ipynb`; both remain untouched and ignored pending review. A flag is not confirmation of a live credential. No credential contents were printed.
- Initial version-control baseline includes setup documentation, inherited non-flagged source/notebooks, the reference PDF, figures, and ADM tables. Ignored originals remain on disk. The automated baseline uses a local automation author if no user Git identity is configured.

## Next session

Start with a single reproducible EMIT/CERES case. Locate the required granules, solar spectrum, and collocation inputs; inspect metadata, unit conversions, geometry, and cloud masks. Extract pure computations from legacy scripts before execution, parameterize paths, and reconcile UV regression with the draft. Then reproduce the broadband comparison and quantify the wavelength-independent ADM and missing-energy assumptions. NASA access should use the installed earthaccess skill; authentication and network access were not exercised during setup.

## First direct-S3 EMIT RGB — 2026-09-27

- Confirmed EC2 region **us-west-2** from the region-only instance metadata endpoint. Authenticated with earthaccess using the existing external `~/.netrc`, without printing credentials. Verified the underlying file object is `s3fs.core.S3File`.
- Successfully accessed `EMIT_L1B_RAD_001_20230426T090707_2311606_016`, acquired 2023-04-26 09:07:07–09:07:19 UTC over the Egyptian Sahara. Orthorectified extent: 28.123–29.244°E, 28.301–29.402°N.
- S3 object: `s3://lp-prod-protected/EMITL1BRAD.001/EMIT_L1B_RAD_001_20230426T090707_2311606_016/EMIT_L1B_RAD_001_20230426T090707_2311606_016.nc`.
- Collection 001 was selected for continuity with inherited work; CMR also lists 002. A narrow CMR temporal search returns overlapping acquisition intervals, not only start times. RAD granules include both RAD and OBS files; explicitly select the RAD filename.
- Read root-group radiance with xarray/h5netcdf plus `sensor_band_parameters` and `location`. Radiance units are `uW/cm^2/SR/nm`; RGB uses band indices 36, 23, 9 (zero-based), at 648.7303, 551.8667, 447.7428 nm.
- Generated a north-up RGB using the embedded GLT (one-based source sample/line indices, zero means missing), consistent with NASA EMIT-Data-Resources `emit_tools.py`. Original data: 1280 × 1242 pixels; orthorectified grid: 2031 × 2069. All selected raw RGB samples were finite/nonnegative; 2,103,024 output pixels have valid mapped RGB.
- Display uses independent 2nd–98th percentile stretches and gamma 2.2. Colors are contrast enhanced; this is at-sensor radiance visualization, not surface reflectance or flux. No cloud/quality screening was performed. Visually checked the plotted desert texture, mapped footprint, geographic axes, and image layout.
- Script: `scripts/plot_emit_rgb.py`. Run after `source scripts/activate.sh`. Outputs: `outputs/emit_rgb/EMIT_L1B_RAD_001_20230426T090707_2311606_016_RGB.png`, unannotated PNG, metadata JSON, and CMR JSON. A small provenance copy is tracked at `docs/first_emit_scene.json`.
- Read the shared `~/Research/python_lib/EMIT_lib.py` and inspected the AWS helper interface. Used earthaccess to manage current temporary S3 credentials and explicit grouped xarray access instead of the older credential helper. Shared libraries were left unchanged.
- No complete netCDF file was saved locally. V001 radiance storage is contiguous rather than chunked, so extracting three bands still incurred substantial S3 reads and took several minutes. Do not assume a small wavelength subset implies proportionately small I/O for this version.
- Scientific flux calculations and CERES collocation have not yet been rerun. Next: inspect OBS geometry and quality masks for this case, then reconcile radiance integration, UV correction, and ADM usage before deriving flux.

## Version and I/O clarification — 2026-09-27

NASA LP DAAC announced EMIT L1B Version 002 on 2026-09-21, with historical reprocessing expected to take about three months: https://forum.earthdata.nasa.gov/viewtopic.php?t=8243 . Catalog queries today returned no V002 match for our exact 2023 scene, nor for the broader Sahara box (10–30°E, 15–30°N) over April 26–27, 2023. This does not imply V002 is absent everywhere. We have not inspected a V002 radiance file's storage layout, so do not claim V002 is more efficiently chunked.

The measured V001 file has contiguous storage, dimensions (1280,1242,285), float32: about 1.81 GB of radiance. Three RGB bands are about 19 MB in memory but are interleaved throughout the file. Our first RGB script reads the three bands in separate passes, which can repeat S3 range reads; direct S3 access does not guarantee low transfer volume. Improved candidate: read spatial slabs containing all bands once, retain RGB channels or compute flux in memory, then discard the slab. For repeated scientific analysis, optionally cache/rechunk a scene locally after agreeing the desired data footprint. These alternatives have not yet been benchmarked. Product-version calibration changes and I/O optimization are separate questions.

## Qianqian restart audit — 2026-09-27

User identified `Qianqian/EMIT_CERES_Collocation_Map.py` as the latest working starting point. Read the full script, related comparison script, readers, notebook text outputs, and saved result dictionaries. Detailed audit: `docs/QIANQIAN_REPRODUCTION_AUDIT.md`.

577 saved flux dictionaries are available (4,844 footprint records; 2,324 before land/NaN masking after dropping cases with >20 records). Therefore replotting does not require raw satellite data. The historical notebook reports 1,782 collocation cases; completeness/provenance of the saved result subset remains unverified.

A full rerun needs April 2023 Terra-FM2 MODIS SSF Edition4A (historical notebook filenames show build 407405), EMIT V001 RAD/OBS and optionally RFL, and the original April manifest/collocation pickle files or a reconstruction. These exact CERES inputs and original matching records were not found in the inspected Research/Data trees. The 1,229 local CERES files in EMIT_dust_DRE are Aqua-FM3 for June–August, not the target data. ADM tables are present; candidate solar spectrum found in PACE_ACA_project. The solar spectrum is not a fundamental blocker because KS cancels algebraically from the incoming-flux calculation.

Clean-script blockers: undefined CERES_SSF, commented-out KS/ADM initialization, old paths, sys.exit at 100 map points, removed np.trapz, and this netCDF4 build's inability to read HDF4 (verified on a local SSF file; pyhdf works). Basemap needed for exact historical comparison land mask is missing. The map and flux/comparison stages use different spatial/sample selections. Collocation uses five hourly files rather than precise footprint time differences and overwrites earlier matching CERES files. Preserve historical behavior for reproduction before evaluating scientific changes. No scientific pipeline was run or modified during this audit.

## Saved flux comparisons reproduced — 2026-09-27

Successfully reproduced Qianqian's two manuscript comparisons from all 577 saved result files using `scripts/reproduce_saved_flux_comparison.py`. Report: `docs/SAVED_FLUX_REPRODUCTION.md`; full-precision tracked summary: `docs/saved_flux_reproduction_summary.json`. PNG/PDF figures, per-record selection CSV and SHA256 input manifest are in `outputs/saved_flux_comparison/`.

Preserved original rules: discard files with >20 footprints, default Basemap land mask on unmodified CERES longitudes, reject NaN reflectances; no extra region filter/deduplication. 4,844 records → 2,324 after file exclusion → 1,482 selected records across 339 EMIT timestamps. Direct fit: slope 1.080413027525219, intercept 1.233909747759924 W/m², R 0.9343405530002342. Adjusted fit: slope 1.0013830653258102, intercept 12.488203536074025 W/m², R 0.9776101158033365. Both match manuscript labels. Adjusted difference mean 12.954575148441972 and population std 14.627227186615482 W/m² exactly match the saved notebook outputs. Direct/adjusted RMSE: 37.1090/19.5391 W/m². Visually inspected the combined figure and verified reported reference statistics programmatically.

Found a real sample-selection issue: 0–360° CERES longitudes were passed unchanged to default Basemap (-180–180°). Wrapping changes 637 candidate land classifications and would increase the final sample to 2,022 records. This correction was NOT applied to the historical reproduction. Investigate separately before interpreting the sample as all available clear-sky land cases.

Installed Basemap 2.0.0 / basemap-data 2.0.0 in project .venv; local compatible NumPy 2.3.5, Matplotlib 3.10.9 and supporting packages shadow the shared installation. Shared conda environment untouched; required project imports pass. Main reproduction pins: `requirements-reproduction.txt`; local override inventory: `docs/reproduction-environment.txt`. Basemap is now available and np.trapz is present under this NumPy version, superseding earlier environment observations. Original scripts and pickle results remain untouched. No raw satellite data were accessed. Next work can examine corrected longitude selection, then reproduce a selected case from original observations.

## old_EMIT_dust_DRE inspection — 2026-09-27

User added `old_EMIT_dust_DRE`, a symlink to `/home/ssm-user/Research/EMIT_dust_DRE` (the same external tree noted in the earlier audit). Read-only inspection; external originals unchanged. Inventory saved in `docs/old_emit_inventory.json`.

`CERES_SSF/` contains 1,229 actual HDF4 SSF files: Aqua-FM3 MODIS Edition4A, June–August 2023, processing builds 407405 (910 files) and 409406 (319). Month counts: June 295, July 314, August 620. Opened one HDF from each build with pyhdf and confirmed all 11 required time/geolocation/radiance/flux/clear-fraction/geometry fields. These support a summer Aqua extension, not exact April Terra reproduction.

`EMIT_CERES_MAIAC_match_files/` contains 5,819 per-granule dictionaries and one daily list. All loaded successfully. Each per-granule dictionary stores EMIT S3 URLs (RAD/OBS/RFL/MASK), product labels, CERES file URLs, MAIAC MCD19A1 surface and MCD19A2 aerosol file URLs. They are candidate file associations, not final footprint collocations: no CERES pixel indices, spatial masks, spectra, or flux estimates. EMIT timestamps span June 1–August 31, 2023; 5,819 unique timestamps; no within-record timestamp mismatch among the four EMIT products.

Normalize CERES URL basenames by adding `.hdf` when omitted. After normalization there are 814 distinct referenced CERES filenames, 812 present locally. Missing references are the 407405 and 409406 builds for hour 2023082323. 5,817 per-scene dictionaries have all referenced CERES files available, and all 5,819 have at least one available candidate. Thus most of this summer workflow has locally available CERES inputs; live EMIT/MAIAC links were not revalidated here.

The daily `EMIT_CERES_MAIAC_match_file_2023-06-01.pickle` is defective: 104 list entries reference the same dictionary object and one EMIT RAD URL. The notebook constructs a dictionary outside its granule loop and repeatedly appends it, explaining this aliasing. Prefer the 5,819 separate per-granule files; do not interpret the daily list as 104 distinct scenes.

Generator notebook `old_EMIT_dust_DRE/CERES-EMIT-MODIS-Collocation.ipynb` searches CERES over a full day in a ±0.5° box around a point from the EMIT footprint boundary. A later cell performs the actual spatial, daytime, 100%-clear, and 20 km pixel selection; that cell still has an unfinished radiance-processing placeholder. Revalidate footprint-level time matching before calling these science-ready collocations.

## April Terra-FM2 archive found on S3 — 2026-09-27

User supplied an ASDC S3 URL. Successfully authenticated using earthaccess with provider `LARC_CLOUD` and verified the exact object `s3://asdc-prod-protected/CERES/CER_SSF_Terra-FM2-MODIS_Edition4A/2023.04/CER_SSF_Terra-FM2-MODIS_Edition4A_407405.2023043023`: 74,694,931 bytes, readable through S3; first bytes `0e031301` are the HDF4 signature. No `.hdf` suffix is present on these S3 keys.

Listing the April prefix returns all 720 hourly objects from 2023040100 through 2023043023, all historical processing build 407405. Checked exact hourly coverage, not just the count. This resolves availability of the April Terra-FM2 raw archive needed for Qianqian's rerun. Inventory: `outputs/terra_fm2_april_s3_inventory.json`; tracked check summary: `docs/terra_fm2_s3_availability.json`. Only the supplied object's header was read; full contents of all files have not been validated. No full granules downloaded.

Next retrieval should select the hourly files needed by saved EMIT cases. ASDC uses separate temporary credentials from LP DAAC; let earthaccess scope them. Existing pyhdf expects a local filename, so a practical path is to cache selected CERES hourly HDF4 granules locally (adding `.hdf` locally if useful), while retaining direct S3 access for EMIT. April boundary cases may require adjacent-month hours under the historical five-hour search rule; those prefixes were not checked yet.

## Raw-observation replication started — 2026-09-27

User authorized reconstructing Qianqian's workflow and explicitly suggested 4–6 parallel jobs. New code: `scripts/replicate_raw_case.py`, `scripts/replicate_raw_batch.py`, `scripts/summarize_raw_reproduction.py`. Inputs use user-supplied `EMIT_L1B.txt` and `EMIT_L2A.txt`; all 577 saved-case timestamps have one RAD and one OBS manifest entry. Originals remain untouched.

Pilot `20230401T094135` (9 clear CERES footprints) successfully rebuilt from S3 EMIT RAD/OBS/RFL and five hourly ASDC CERES files. Correct hour selected independently: `CER_SSF_Terra-FM2-MODIS_Edition4A_407405.2023040108`. CERES arrays, ADM, measured-band upward flux, UV-corrected upward flux, wavelengths, and surface-reflectance spectra match the saved pilot exactly. Remaining geometry/incoming-flux differences are at floating-point precision and pass rtol=1e-5, atol=1e-4. All 4,844 saved ADM factors also match the recovered CSV tables and original bin lookup.

Important numerical compatibility: NumPy 1 promoted Python-float/float32 scalar operations to float64, whereas NumPy 2 often retains float32. Explicit float64 CERES scalar latitude and relative-azimuth/integration arithmetic are required to reproduce the original distance mask and flux. Without that, the pilot differed by up to 0.036 W/m² and 0.51° relative azimuth; restoring historical precision resolved it. Preserve this in future refactoring.

For uncompressed contiguous EMIT arrays, use HDF5 metadata to locate the dataset byte offset, then read checked 32 MiB S3 ranges into a native-typed NumPy array with four I/O threads per process. Preserve original float32 spatial mean order. Pilot radiance loaded within about 12 s including preceding setup; the full pilot with surface reflectance took ~26 s. This is much faster than separate strided band reads.

A 577-case, resumable batch is now running with SIX processes (increased from four at the user's request), with one native radiance cube per worker. CERES HDF4 files are cached under ignored `data/ceres_terra_april/`, with process locks; EMIT cubes are not saved to disk. Main batch omits L2A surface-reflectance computation because it does not enter the TOA comparison; pilot verifies that branch separately. Historical results are read only after raw calculations for validation, never to supply computed fluxes or collocation indices.

Batch output/checkpoints: `outputs/raw_reproduction/<timestamp>/{provenance.json,validation.json,run.log,collocation.npz,spectra_and_geometry.npz,flux_comparison_results_raz_ceres_<timestamp>.pkl}`. Progress: `outputs/raw_reproduction/batch_status.json`. Resume using `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/replicate_raw_batch.py --workers 6`. Authentication is serialized and retried after an initial transient JSON error from the credential endpoint. A case is complete only when provenance and validation exist.

The first six illustrated April 1 swath scenes produce a raw-derived map of 53 clear CERES footprints; `raw_collocation_map.png` uses sampled (every fourth pixel) geolocation hulls for display, with the same 20 km selection rule. Pilot spectral-flux figure: `pilot_spectral_flux.png`. Both visually inspected. These are diagnostic reconstructions; the final all-case comparison awaits batch completion and validation.

## Raw-observation replication completed — 2026-09-27

The six-process batch finished all 577 cases successfully (4,844 footprint records). No missing cases, shape/NaN-pattern mismatches or field differences beyond rtol=1e-5, atol=1e-4. Maximum measured-band and UV-augmented EMIT upward-flux differences: 1.1368683772161603e-13 W/m²; incoming-flux difference: 0.0002699042233871296 W/m². CERES reported fluxes, coordinates and geometry match exactly. Pilot wavelengths and surface-reflectance spectra match exactly. This supersedes the preceding running status.

Regenerated the comparison from raw-derived result files, and verified the exact same 1,482 selected record identities across 339 scenes. Direct slope/intercept/R: 1.080413027525219 / 1.233909747759924 / 0.9343405530002342. Solar-angle-adjusted: 1.0013830676064388 / 12.488202598052396 / 0.9776101182212882. RMSEs 37.1090229474348 and 19.539108609632056 W/m². Both manuscript-rounded fits reproduced. Combined figure visually inspected; all new scripts compile.

Report: docs/RAW_REPRODUCTION.md. Tracked full-precision summaries: docs/raw_validation_summary.json and docs/raw_flux_comparison_summary.json. Figures and selection/hash tables: outputs/raw_reproduction/comparison/. Diagnostic collocation map and pilot spectral flux: outputs/raw_reproduction/. README documents the complete resumable workflow. User-supplied manifests and old_EMIT_dust_DRE symlink remain untouched.

This establishes a reproducible historical TOA-flux baseline, not a validation of the scientific assumptions. Scope remains the 577 saved timestamps; L2A surface-reflectance branch was independently reproduced only for the pilot. Next scientific work should assess the longitude-mask correction, footprint time differences/coverage, wavelength-independent ADM and empirical UV correction separately, retaining this baseline.
