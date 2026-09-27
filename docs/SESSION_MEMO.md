# Session memo

Last updated: 2026-09-27 (UTC).

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
