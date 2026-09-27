# EMIT spectral TOA flux

Derive spectrally resolved upward shortwave radiative flux at the top of the atmosphere from NASA EMIT hyperspectral radiance over the Sahara. Use PACE OCI to estimate missing UV energy and collocated CERES Terra SSF fluxes for validation.

Start with [the session memo](docs/SESSION_MEMO.md) and [the manuscript draft](references/EMIT%20Flux%20derivation.pdf). The draft and inherited code are research work in progress.

The [end-to-end reproduction guide](docs/REPRODUCTION_GUIDE.md) documents inputs, environment, scientific calculations, every script, restart commands, validation, output formats and troubleshooting. A [PDF edition with three figures](docs/EMIT_CERES_Reproduction_Guide.pdf) is generated from the same source.

```bash
source scripts/activate.sh
python scripts/run_reproduction.py                    # Offline checks, plots and PDF
python scripts/run_reproduction.py --raw --workers 6  # Also run/resume original S3 inputs
```

The default command requires the completed local raw-derived outputs. Both modes verify all 577 cases and the original 1,482-record comparison selection. The raw mode also recomputes the pilot with L2A reflectance. Workflow/PDF package versions are in `requirements-workflow.txt`; recovery tests run with `python -m unittest discover -s tests -v`.

## Working environment

A local `.venv` inherits installed packages from the existing Python 3.12 `PACE_EMIT` conda environment. This avoids modifying that shared environment. It is tied to this machine and is not a standalone reproducible environment.

```bash
source scripts/activate.sh
python scripts/check_environment.py
python -m jupyterlab
```

Activation routes plotting and Jupyter caches into the writable project `.cache` directory. For a fresh machine, create a virtual environment with `python3 -m venv .venv`, activate it, and install `requirements.txt`. Optional historical plotting dependencies are listed in `requirements-legacy-plots.txt`. The installed package inventory is in `docs/environment-snapshot.txt`; it records this host, not a portable lockfile.

## Existing work

- `Qianqian/`: collocation, radiance integration, spectral irradiance, CERES comparison scripts/notebooks, and local result artifacts.
- `Zhibo/`: EMIT/CERES/MODIS readers, AWS exploration, collocation notebooks, and Loeb 2005 ADM tables in `Leob2005_ADM/` (existing spelling retained).
- `references/`: background manuscript.
- `docs/`: persistent session context and environment inventory.
- `scripts/`: environment activation and import checks.

Historical scripts include unavailable absolute paths, notebook-style execution at import, and removed `np.trapz` calls. They are preserved as received; passing the environment check does not establish that the scientific workflows run. See the memo before reproducing results.

Keep credentials outside version control. Raw data, pickle results, caches, environments, and credential files are ignored. No remote repository or data downloads are configured by this setup.

## First Sahara RGB scene

```bash
source scripts/activate.sh
python scripts/plot_emit_rgb.py
```

Uses existing Earthdata credentials in `~/.netrc` and reads EMIT L1B radiance directly from S3. The script verifies the S3 backend, selects bands near 650/550/450 nm, applies the file's geolocation lookup table, and writes annotated/unannotated PNGs plus provenance JSON to `outputs/emit_rgb/`. RGB contrast is stretched independently by channel for display; it is not a flux or surface-reflectance product. Version 001 is used to match the inherited analysis. The installed earthaccess skill supplies catalog retry helpers.

## Reproduce Qianqian's saved flux comparisons

```bash
source scripts/activate.sh
python scripts/reproduce_saved_flux_comparison.py
```

The 577 supplied result files reproduce both manuscript regressions with 1,482 selected records. PNG/PDF plots, statistics, input hashes and a record-level selection table are written to `outputs/saved_flux_comparison/`. See [the reproduction report](docs/SAVED_FLUX_REPRODUCTION.md) for results and the historical longitude-mask issue. The required Basemap installation is available in `.venv`; main package versions are recorded in `requirements-reproduction.txt`.

## Recompute from original observations

On this AWS us-west-2 instance, with Earthdata credentials in `~/.netrc`:

```bash
source scripts/activate.sh
python scripts/replicate_raw_case.py 20230401T094135 --include-rfl
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/replicate_raw_batch.py --workers 6
python scripts/summarize_raw_reproduction.py --require-complete
python scripts/reproduce_saved_flux_comparison.py \
  --input-dir outputs/raw_reproduction/flux_results \
  --output-dir outputs/raw_reproduction/comparison \
  --title 'EMIT–CERES comparison · Recomputed from original April 2023 observations' \
  --scope 'Raw S3 observations recomputed for 577 historical cases; see raw_validation_summary.json for validation and scope.'
```

The supplied `EMIT_L1B.txt` and `EMIT_L2A.txt` manifests identify source filenames. The 577 saved result files define the case timestamps and provide validation references; fluxes and footprint selections are calculated independently from satellite observations. The batch resumes cases with completed provenance and validation files. It reads EMIT V001 from S3 into memory and caches only the selected CERES Terra-FM2 Edition4A build 407405 HDF4 files under `data/ceres_terra_april/` for pyhdf. Six workers fit this instance; reduce the worker count on smaller machines.

Each case retains source URLs, selected CERES indices, pixel counts, mean spectra, output fluxes, and comparison diagnostics in `outputs/raw_reproduction/`. The batch recomputes TOA fluxes; L2A surface-reflectance spectra are recomputed only for the pilot. Historical collocation, UV correction, ADM assumptions and plotting selection are preserved. See [the raw reproduction report](docs/RAW_REPRODUCTION.md).
