# EMIT–CERES spectral flux: reproduction guide

**A restart manual for Zhibo and Qianqian**  
Verified baseline: 27 September 2026 • April 2023 observations • AWS us-west-2

## 1. What this workflow reproduces

This guide describes how to rebuild the project's EMIT top-of-atmosphere (TOA) upward spectral flux estimates and their comparison with CERES. It joins the data requirements, executable scripts, scientific rules, validation evidence and troubleshooting in one place so the work can be resumed after an interruption.

The completed raw-data run reconstructed **577 EMIT cases and 4,844 CERES footprint records**. The original comparison selection retains **1,482 records across 339 EMIT scenes**. Both manuscript fits are reproduced. Each case reads original satellite observations, selects CERES footprints and calculates fluxes independently. Only after computation are the saved historical values used for validation. Historical pickle filenames define which 577 timestamps to process.

| Comparison | Slope | Intercept, W m⁻² | Pearson R | RMSE, W m⁻² |
| --- | ---: | ---: | ---: | ---: |
| Direct EMIT versus CERES | 1.08041303 | 1.23390975 | 0.93434055 | 37.1090 |
| CERES adjusted to EMIT solar zenith angle | 1.00138307 | 12.48820260 | 0.97761012 | 19.5391 |

The solar-angle-adjusted mean EMIT-minus-CERES difference is 12.954575 W m⁻², with population standard deviation 14.627226 W m⁻². Full-precision statistics are in `docs/raw_flux_comparison_summary.json`; validation differences are in `docs/raw_validation_summary.json`.

![Recomputed EMIT and CERES flux comparison](../outputs/raw_reproduction/comparison/comparison_pair.png)

*Figure 1. Recomputed flux comparisons using the historical 1,482-record selection. Left: direct CERES upward shortwave flux; color shows EMIT minus CERES solar zenith angle. Right: CERES flux adjusted using its reflectance and the EMIT incoming flux. Flux units are W m⁻². The historical 315 nm–2.5 µm label denotes measured EMIT wavelengths plus the empirical UV addition; CERES measures a broader shortwave interval.*

This is a reproduction of the historical TOA-flux baseline, not a demonstration that the scientific assumptions are correct. It covers the 577 saved-case timestamps, not every April granule or all 1,782 collocation cases reported in an older notebook. The full L2A surface-reflectance branch was reproduced only for the nine-footprint pilot. No MAIAC product is needed for these comparison plots.

## 2. Quick restart on this AWS instance

The project root is `/home/ssm-user/Research/Spectral_Flux/EMIT`. Start there and activate the local environment:

```bash
cd /home/ssm-user/Research/Spectral_Flux/EMIT
source scripts/activate.sh
```

**To verify existing reconstructed results and rebuild all figures and this PDF without NASA access:**

```bash
python scripts/run_reproduction.py
```

This runs fresh field comparisons, aggregates the raw validation, regenerates the saved-reference plots and raw-derived plots, checks the selected record identities and fit statistics, then builds the PDF. Any failed stage stops the command with a nonzero exit status. Allow about a minute or two for local verification and plotting; this depends on disk and CPU load.

**To run the complete raw-data workflow, or resume missing cases:**

```bash
python scripts/run_reproduction.py --raw --workers 6
```

This first recomputes the pilot with L2A reflectance, then runs/resumes the 577-case TOA batch before the same offline checks and reporting. Completed, successful cases with the required files are skipped by the batch. The pilot is deliberately recomputed when `--raw` is specified. Use `--workers 4` if memory pressure is high, and `--skip-pdf` when only the numerical products are needed.

The wrapper does not silently download data in its default mode. If local raw-derived outputs are missing, run the `--raw` mode. Source scripts and this guide are version controlled; raw observations, pickle results and generated arrays are excluded from git and must be retained separately.

## 3. Environment, credentials and storage

### Existing environment

The project `.venv` was built with system-site-packages from the host's Python 3.12 PACE_EMIT conda environment. Some project-local packages override that base, so the environment is tied to this host. `scripts/activate.sh` points Matplotlib and Jupyter caches at writable project directories. No shared conda packages were changed.

The raw/PDF workflow's observed direct package versions are recorded in `requirements-workflow.txt`, which includes `requirements-reproduction.txt`. Key numerical versions are NumPy 2.3.5, SciPy 1.18.1, Matplotlib 3.10.9, Basemap 2.0.0 and basemap-data 2.0.0. Data access uses earthaccess 0.12.0, h5py 3.15.1 and pyhdf 0.11.6. The PDF builder uses PyMuPDF 1.28.2 and Markdown 3.4.1.

```bash
python scripts/check_environment.py
python -m pip show numpy scipy matplotlib basemap earthaccess h5py pyhdf
```

The environment check includes broader project imports; the workflow also imports its own dependencies when run. `docs/environment-snapshot.txt` describes the initial host, while `docs/reproduction-environment.txt` records later numerical/plotting overrides. The verification JSON records packages actually used during each check.

### Moving to another machine

Restore the project, manifests and historical reference pickles before running. A starting setup on a separate Linux machine with Python 3.12 is:

```bash
python3.12 -m venv .venv
source scripts/activate.sh
python -m pip install -r requirements-workflow.txt
```

These are observed direct-version pins, not a tested clean-install lockfile. Transitive dependencies and HDF4 system support can differ. If pyhdf has no suitable wheel, the platform needs an HDF4-capable build. Validate the resulting environment before interpreting differences. Do not recreate or replace this instance's working `.venv` merely to repeat a run.

### NASA authentication and region

This instance is in **AWS us-west-2**, the region used for the direct protected S3 reads in the completed run. The raw scripts use `earthaccess.login(strategy='netrc', persist=False)` with existing Earthdata Login credentials stored outside the project in `~/.netrc`. That file must have the `urs.earthdata.nasa.gov` machine entry and private permissions. Do not put a password or temporary token in a script, notebook, report or git.

The LP DAAC filesystem is obtained with provider `LPCLOUD`; ASDC/CERES uses `LARC_CLOUD`. Credentials for the two providers are separate. Batch authentication is serialized and retried to handle transient credential-endpoint failures. Long-running failures still produce per-case logs and can be resumed. Do not assume the direct S3 path will work from a different region or a laptop; an HTTPS access mode would need to be implemented and tested there.

### Storage and parallelism

A typical contiguous radiance cube is about 1.81 GB, with shape 1280 × 1242 × 285 and float32 samples. Each process also needs geometry arrays, temporary pixel selections and I/O buffers. Six processes worked on this instance's roughly 30 GB RAM; a cube's size alone is not the worker's full memory footprint. The wrapper sets `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` to avoid competing numerical thread pools.

The batch reads full radiance arrays into memory through checked 32 MiB S3 ranges with four I/O threads per process. It does not persist full EMIT cubes. This avoids repeated strided wavelength reads while retaining the historical averaging order. Existing noncontiguous layouts fall back to HDF5 access. CERES HDF4 requires local files for pyhdf: the completed run cached **138 hourly files, 10.61 GB** under `data/ceres_terra_april/`. This count describes the observed cache, not a hard-coded requirement. Protect enough disk space for that cache and the generated outputs.

## 4. Exact inputs and how they are used

| Input | Location | Purpose |
| --- | --- | --- |
| Historical reference results | `Qianqian/Flux_Comparison_Surface_Reflectance_Data/*.pkl` | 577 timestamps and post-computation validation references |
| L1B filename manifest | `EMIT_L1B.txt` | One exact V001 RAD and OBS filename per target timestamp |
| L2A filename manifest | `EMIT_L2A.txt` | Exact pilot V001 RFL filename |
| Desert ADM tables | `Zhibo/Leob2005_ADM/*.csv` | Nine solar-zenith tables; original directory spelling retained |
| Original manuscript | `references/EMIT Flux derivation.pdf` | Scientific motivation, assumptions and reported plots |
| Original implementation | `Qianqian/EMIT_CERES_Collocation_Map.py` | Historical matching and flux rules |
| Comparison implementation | `scripts/reproduce_saved_flux_comparison.py` | Preserved selection and regression/plot expressions |

The manifests supplied by the user are filename lists, not downloaded observations. `manifest_name()` requires exactly one matching filename for the requested product and timestamp. Unrelated lines are ignored. RAD and OBS share an EMIT L1B radiance granule folder. For example, URLs have this structure (angle brackets are placeholders):

```text
s3://lp-prod-protected/EMITL1BRAD.001/
  <RAD filename without .nc>/<RAD or OBS filename>

s3://lp-prod-protected/EMITL2ARFL.001/
  <RFL filename without .nc>/<RFL filename>
```

CERES sources use this prefix and basename pattern, with no `.hdf` suffix on S3:

```text
s3://asdc-prod-protected/CERES/
  CER_SSF_Terra-FM2-MODIS_Edition4A/2023.04/
  CER_SSF_Terra-FM2-MODIS_Edition4A_407405.YYYYMMDDHH
```

The code builds the month from each candidate hour, so boundary hours would use the adjacent month. The April archive was checked to contain 720 hourly keys. Selected local cache files receive a `.hdf` suffix. Each case's `provenance.json` records all five candidate URLs and the selected URL; `case_inventory.json` records source filenames and reference/result hashes across the entire run.

The old `old_EMIT_dust_DRE/CERES_SSF/` collection contains summer Aqua-FM3 data, not the April Terra-FM2 inputs used here. Its matched pickle files are candidate product associations, not the final footprint selections or flux outputs. Neither that directory nor MAIAC is an input to this reproduction. See `docs/old_emit_inventory.json` for the earlier audit.

**Backup requirement:** git alone is insufficient. Preserve the two user-supplied manifests and the 577 trusted historical pickle files in addition to the tracked scripts/ADM tables. Preserve `outputs/raw_reproduction/` for fast offline recovery; CERES cache files can be fetched again if necessary. The workflow records manifest, ADM and reference hashes, but it does not store full raw-object checksums or S3 version IDs. Do not load arbitrary untrusted pickle files.

## 5. Scientific calculation, step by step

### 5.1 Read observations and candidate CERES hours

For each target timestamp, read EMIT OBS `location/lon`, `location/lat` and `obs`. The historical scene center is the mean longitude and latitude in those arrays. The geometry cube supplies sensor azimuth (index 1), viewing zenith (2), solar azimuth (3) and solar zenith (4), using zero-based indices.

Form five CERES hourly filenames using EMIT time plus −2, −1, 0, +1 and +2 hours. Read geolocation, clear coverage, upward SW flux, upward filtered/unfiltered radiance, incoming solar radiation, viewing geometry and observation time. HDF fill values are replaced with NaN. CERES latitude is 90° minus colatitude. For this scene-center search only, CERES longitudes above 180° are mapped to longitude minus 360°.

Select CERES centers strictly inside the scene-center box: longitude and latitude each within ±0.3°. Examine files in ascending hourly order and **retain the last file with any spatial matches**, reproducing the historical overwrite behavior. This is an hourly-file search, not a maximum exact time difference between the two footprint observations. Time is read but not used to impose an additional temporal filter.

### 5.2 Clear footprints and EMIT pixels

In the selected file, require the first clear/layer/overlap percentage component to be at least 100. For every remaining CERES center, select EMIT native pixels at great-circle distance ≤20 km, using Earth radius 6371 km. An empty EMIT selection is an error.

Average selected radiance pixels at each wavelength using the ordinary NumPy mean in the native float32 layout. Average the geometry angles over the same pixel selection. This preserves the old handling of NaNs; changing to `nanmean` would change the calculation. There is no new EMIT quality mask, no separate aerosol screening, no CERES point-spread weighting and no minimum footprint-coverage fraction in this baseline. The circular region can be clipped by the EMIT swath, and adjacent CERES regions may overlap.

![Reconstructed April 1 collocation map](../outputs/raw_reproduction/raw_collocation_map.png)

*Figure 2. Fifty-three clear CERES footprint centers and their overlapping EMIT pixel-selection regions across six April 1 scenes. The map covers 25–30°E and 15–20°N. Polygons use every fourth geolocation pixel for display; fluxes use all selected native pixels. These polygons depict the historical 20 km selection within the EMIT swath, not the CERES instrument's exact response footprint.*

### 5.3 Angle convention and ADM lookup

EMIT relative azimuth is `180 − (mean sensor azimuth − mean solar azimuth)`, in degrees. Follow the original lookup's folding: negative values become their absolute value; values above 180 become `360 − value`. The lookup uses `searchsorted` with its default left-sided insertion against these upper boundaries:

- Solar and viewing zenith: 10, 20, …, 90 degrees.
- Relative azimuth: 10, 30, 50, 70, 90, 110, 130, 150, 170, 180 degrees.

The nine sorted CSV files form a 9 × 9 × 10 array. The EMIT ADM uses EMIT geometry; diagnostic CERES radiance-derived fluxes use CERES geometry. The primary comparison uses the reported CERES SSF upward flux. All 4,844 historical EMIT ADM values were found consistent with the supplied tables and lookup. A future geometry outside table bounds needs an explicit scientific policy; do not silently clip it.

### 5.4 Radiance to spectral and integrated flux

The raw script checks the file's radiance unit string `uW/cm^2/SR/nm`. One µW cm⁻² equals 0.01 W m⁻², giving the factor 1/100. Let I(λ) be mean EMIT radiance in the file's units and R the dimensionless desert ADM:

```text
F(λ)       = π I(λ) / (100 R)           [W m⁻² nm⁻¹]
F_measured = π trapz(I, λ) / (100 R)     [W m⁻²]
F_short    = π trapz(I[λ≤420], λ[λ≤420]) / (100 R)
F_UV       = 1.01 F_short + 4.86         [W m⁻²]
F_augmented = F_measured + F_UV          [W m⁻²]
```

The implementation uses `np.trapezoid` on the actual granule wavelength coordinates, approximately 381–2493 nm. The broadband desert ADM is assumed wavelength independent. The old result key `EMIT_Fup_fullspectrum` means the UV-augmented EMIT interval, not a fully observed broadband spectrum. The UV regression coefficients are inherited, not refit in this workflow. The manuscript discusses a 381–440 nm predictor, whereas the implemented mask is λ≤420 nm; that discrepancy remains unresolved and is preserved explicitly.

![Pilot spectral flux](../outputs/raw_reproduction/pilot_spectral_flux.png)

*Figure 3. Upward spectral flux for nine CERES selections in EMIT scene 20230401T094135. Each spectrum uses its mean radiance and EMIT-geometry desert ADM. Only measured EMIT wavelengths are shown. The empirical integrated UV addition is not assigned an invented spectral shape.*

### 5.5 Incoming flux and solar-angle adjustment

For each selected hourly CERES subset, compute `S0 = nanmean(CERES incoming flux / cos(CERES solar zenith))`, with angles converted to radians. This is one scalar per scene's selected clear-footprint subset. Set `EMIT_Fdn = S0 × cos(EMIT solar zenith)` for each footprint. An external solar-spectrum file is unnecessary: the legacy solar constant factors cancel algebraically in this expression.

The main direct comparison is `x = CERES_Fup`, `y = EMIT_Fup_fullspectrum`. The adjusted comparison uses `CERES_Ref = CERES_Fup / CERES_Fdn` and:

```text
x_adjusted = EMIT_Fdn × CERES_Ref
EMIT_ref_for_plot = EMIT_Fup_fullspectrum / EMIT_Fdn
y_adjusted = EMIT_Fdn × EMIT_ref_for_plot
```

The plotted EMIT reflectance includes the UV addition. The saved field named `EMIT_Ref` instead uses measured-band flux; the plotting script intentionally recomputes the augmented reflectance and does not use that field. `EMIT_surface_reflectance` is an entirely separate L2A product and is not used in these comparison expressions.

### 5.6 Final sample selection

| Stage | Record count |
| --- | ---: |
| All 577 reconstructed files | 4,844 |
| Drop 51 files with more than 20 footprints | 2,324 |
| Historical default Basemap land mask | 1,621 |
| Also require non-NaN CERES and augmented EMIT reflectance | 1,482 |

There are 526 files after the first exclusion and 339 scenes contributing to the final figure. Among all 2,324 candidates, 238 have a NaN reflectance; only 139 of these are in the land subset, so the masks overlap. No extra Sahara bounding box, deduplication or outlier removal is applied to the comparison.

CERES longitudes are saved in their original convention. The plotting land test passes them unchanged to default Basemap, whose domain is −180 to 180°. This known longitude issue is retained for reproduction. Wrapping longitudes changes 637 candidate land classifications and would produce 2,022 selected records. Do not interpret the baseline as all available clear-sky Sahara land cases. A corrected-selection experiment must be kept distinct from these results.

## 6. Scripts and individual execution stages

| Script in `scripts/` | Responsibility |
| --- | --- |
| `activate.sh` | Activate project Python and writable caches |
| `check_environment.py` | Check broader project imports |
| `replicate_raw_case.py` | Read a case from S3, collocate, derive flux, validate, save provenance |
| `replicate_raw_batch.py` | Parallel execution, checkpointing and resume |
| `verify_reproduction.py` | Fresh offline field, provenance and regression checks; input/result hashes |
| `summarize_raw_reproduction.py` | Aggregate validation, link flux files, draw collocation and spectral figures |
| `reproduce_saved_flux_comparison.py` | Apply historical selection and generate regression plots/statistics |
| `run_reproduction.py` | Orchestrate the complete verified workflow |
| `build_reproduction_report.py` | Render this Markdown guide, including figures, to PDF |

The new scripts use project-relative paths based on their own locations, and do not execute the inherited notebooks or scripts on import. They implement the recovered rules directly; the shared `~/Research/python_lib/EMIT_lib.py` and `AWS_Utils.py` are not runtime dependencies. The first Sahara RGB script, `plot_emit_rgb.py`, is a separate display diagnostic, not required for flux reproduction.

To execute each stage manually, from the activated project root:

```bash
# 1. Raw pilot, including surface reflectance; NASA access required.
python scripts/replicate_raw_case.py 20230401T094135 --include-rfl

# 2. All historical TOA cases; NASA access for pending cases.
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python scripts/replicate_raw_batch.py --workers 6

# 3. Fresh offline validation; fail if any required case is missing.
python scripts/verify_reproduction.py
python scripts/summarize_raw_reproduction.py --require-complete

# 4. Rebuild saved-reference plots for record-identity comparison.
python scripts/reproduce_saved_flux_comparison.py

# 5. Plot only the independently reconstructed flux files.
python scripts/reproduce_saved_flux_comparison.py \
  --input-dir outputs/raw_reproduction/flux_results \
  --output-dir outputs/raw_reproduction/comparison \
  --title 'EMIT–CERES comparison · Recomputed from original April 2023 observations' \
  --scope 'Raw S3 observations recomputed for 577 historical cases; see raw_validation_summary.json for validation and scope.'

# 6. Check selection/fits and render the report.
python scripts/verify_reproduction.py --check-comparison
python scripts/build_reproduction_report.py
```

`--limit N` on the batch is useful for a small smoke run of the first N timestamps. It changes that invocation's checkpoint target count, not the scientific calculation. Run the full command afterward; the final verifier always requires the 577-case baseline. Run only one batch controller at a time because they share the checkpoint file and case output paths.

For an unattended raw run in a shell on this instance:

```bash
mkdir -p outputs/raw_reproduction
nohup python -u scripts/run_reproduction.py --raw --workers 6 \
  > outputs/raw_reproduction/workflow.log 2>&1 &
tail -f outputs/raw_reproduction/workflow.log
```

After an interruption, repeat the same command. Cases that are incomplete or whose cached validation reports failure are queued again. The batch's completion test requires provenance, validation, calculated pickle, collocation and spectra files. It does not detect every possible manual alteration; the mandatory fresh offline verifier checks the content against the references. A failed fresh check stops reporting: inspect the named field and logs, then explicitly rerun that case with `replicate_raw_case.py TIMESTAMP` (add `--include-rfl` for the pilot).

## 7. Output dictionary and file layout

Each timestamp under `outputs/raw_reproduction/` contains:

| File | Content |
| --- | --- |
| `flux_comparison_results_raz_ceres_TIMESTAMP.pkl` | Calculated flux, geometry and supporting arrays |
| `provenance.json` | RAD/OBS/RFL URLs, candidate and chosen CERES URLs/indices, rules, units, pixel counts, elapsed time |
| `validation.json` | Per-field shape, NaN-pattern, maximum difference and tolerance comparisons; reference hash |
| `collocation.npz` | CERES selected indices and scene-box spatial mask |
| `spectra_and_geometry.npz` | Wavelengths, mean radiance, pixel counts and every-fourth-pixel geolocation |
| `run.log` | Batch worker messages/errors; single-case runs write to the terminal |

Important dictionary fields and dimensions:

| Field(s) | Meaning / units |
| --- | --- |
| `CERES_Lon`, `CERES_Lat` | Selected footprint centers, degrees; original CERES longitude convention |
| `CERES_Fup`, `CERES_Fdn` | Reported upward shortwave and incoming TOA flux, W m⁻² |
| `CERES_S0` | One-element list containing the scene's inferred solar irradiance, W m⁻² |
| `CERES_Ref` | Reported upward / incoming flux, dimensionless |
| `EMIT_Fup` | Integrated measured-band upward flux, W m⁻² |
| `EMIT_Fup_fullspectrum` | Measured-band flux plus empirical UV contribution, W m⁻² |
| `EMIT_Fdn`, `EMIT_Ref` | Incoming flux and measured-band upward / incoming ratio |
| `EMIT_Adm` | Desert anisotropy factor at EMIT geometry, dimensionless |
| `*_Sza`, `*_Vza`, `*_Raz` | Solar zenith, viewing zenith, relative azimuth, degrees |
| `CERES_Fup_based_on_ADM_*` | Diagnostic filtered/unfiltered radiance-to-flux estimates, W m⁻² |
| `EMIT_wvl`, `EMIT_surface_reflectance` | Pilot-only per-footprint L2A wavelengths (nm) and positive-value mean reflectance |
| `EMIT_surface_reflectance_flatten` | Historical empty placeholder; not a computed science product |

Except `CERES_S0`, the scalar science fields have one value per footprint. `EMIT_time_stamp` is a string. The nonpilot RFL fields remain empty and are explicitly omitted from raw field validation. `mean_radiance` in the NPZ is footprint × wavelength, in original radiance units; its wavelengths are stored even when L2A is omitted.

Top-level outputs include `batch_status.json`, aggregate `raw_validation_summary.json`, fresh `verification.json`, and `case_inventory.json`. The `flux_results/` directory contains relative links to calculated case pickles for the plotting script. The `comparison/` directory contains PNG/PDF plots, `summary.json`, per-file hashes in `input_manifest.json`, and a row-level `footprint_selection.csv`. The two diagnostic figures are at the raw output root. The final guide PDF is `docs/EMIT_CERES_Reproduction_Guide.pdf`.

## 8. Acceptance criteria and numerical compatibility

All 577 cases and 4,844 records must be present. Fresh verification requires every TOA flux and geometry field listed in the verifier, with the original array shape and NaN pattern. Numeric tolerance is `rtol=1e-5`, `atol=1e-4`, using NumPy's relative-plus-absolute criterion. Pilot wavelengths and reflectance are checked separately. The same 1,482 source-file/record-index identities must survive selection, and the new regression statistics must match the established raw-run summary to `rtol=1e-10`, `atol=1e-10`.

Observed largest absolute differences against the historical references:

| Quantity | Maximum difference |
| --- | ---: |
| EMIT measured-band or UV-augmented upward flux | 1.14 × 10⁻¹³ W m⁻² |
| EMIT incoming flux | 2.70 × 10⁻⁴ W m⁻² |
| EMIT relative azimuth | 1.07 × 10⁻⁴ degrees |
| CERES reported fluxes, coordinates and geometry | 0 |
| Pilot L2A wavelengths and reflectance spectra | 0 |

NumPy 2 scalar-promotion rules differ from the historical NumPy environment. The raw calculation explicitly restores float64 scalar arithmetic for CERES latitude, relative azimuth and integration scaling, while preserving float32 spatial averaging. Changing accumulation order or precision can alter a distance-boundary pixel or an angle-bin choice. Keep these details when optimizing; do not assume numerically plausible fluxes establish reproduction.

Operational improvements introduced with this guide are confined to orchestration and checks: atomic checkpoint replacement, positive worker/limit validation, explicit batch failure exit status, more complete resume checks, fresh all-case validation, hash inventory, and a one-command report build. The radiance averaging, pixel masks, ADM lookup, UV regression and plot selection were not changed. The full offline pipeline is the regression check for these changes; no repeat transfer of hundreds of EMIT cubes is needed to verify orchestration-only changes.

The offline pipeline passed on all 577 cases after these improvements. A completed-batch resume correctly reported zero pending cases without authenticating to NASA. Three isolated recovery tests cover skipping a complete case, requeuing an incomplete case, and returning an error while retaining the checkpoint after a worker failure. Run them with `python -m unittest discover -s tests -v`.

## 9. Troubleshooting and future scientific changes

| Symptom | Check / recovery |
| --- | --- |
| Missing reference files or manifest match count is not one | Restore the trusted 577 references and correct supplied manifest; inspect product/timestamp rather than substituting another version |
| Earthdata login or protected S3 access fails | Check the external Earthdata account setup, provider and AWS region; never print credentials into logs |
| Credential endpoint returns JSON decoding error | Retry; batch initialization serializes credential requests and retries five times |
| Worker fails / job is interrupted | Inspect timestamp `run.log` and `batch_status.json`; rerun to resume incomplete/failed cases |
| Process killed or memory exhausted | Reduce `--workers`; each worker needs more than the 1.81 GB cube size |
| CERES cannot be opened by netCDF4 | Use the implemented pyhdf HDF4 path and local cached file |
| A cached CERES file is corrupt | Move that named file aside while no job is using it, then rerun to fetch it again |
| Changed field values or pixel counts | Compare NumPy versions, scalar precision, source product version and mask/ADM rules; do not loosen tolerance silently |
| Different final point count | Check >20-file exclusion, Basemap data version, unchanged longitude convention and NaN reflectance rules |
| PDF build reports missing plots | Run `python scripts/run_reproduction.py`; the PDF needs generated images and a successful comparison verification |
| PDF text and image placement need revision | Edit the Markdown guide or builder CSS, rebuild, and visually inspect the pages |

Future work should evaluate exact footprint time separation, actual spatial coverage/weighting, longitude wrapping, spectral dependence of the desert ADM, and the UV regression's training data and wavelength mismatch. These would intentionally change scientific results and are not applied to this baseline. The reproduced comparison does not isolate aerosol effects, establish the spectral ADM's accuracy or finish the dust-DRE analysis.

## 10. Provenance and project memory

Read `docs/SESSION_MEMO.md` at each restart. Its dated entries form a chronological record; later verified results supersede early missing-data notes. The compact report is `docs/RAW_REPRODUCTION.md`. The earlier code audit and saved-result reproduction are in `docs/QIANQIAN_REPRODUCTION_AUDIT.md` and `docs/SAVED_FLUX_REPRODUCTION.md`.

The scientific source is the local manuscript `references/EMIT Flux derivation.pdf`, especially its EMIT/UV methodology and comparison figures, together with Qianqian's collocation and comparison code and `Zhibo/read_Loeb05_ADM.py`. This guide reports the behavior verified from those local sources and the reproduced outputs. It does not claim to rederive the original ADM tables or retrain the OCI-based UV regression.

The raw baseline was saved in local git commit `87df034`. Subsequent guide and orchestration improvements are recorded in the local history; no remote publishing is required. Preserve original research inputs, keep credential material outside git, and record new scientific choices and results in the session memo. The PDF is generated from this Markdown source, so both versions can be updated together.
