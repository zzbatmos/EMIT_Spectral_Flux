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
