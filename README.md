# EMIT spectral TOA flux

Derive spectrally resolved upward shortwave radiative flux at the top of the atmosphere from NASA EMIT hyperspectral radiance over the Sahara. Use PACE OCI to estimate missing UV energy and collocated CERES Terra SSF fluxes for validation.

Start with [the session memo](docs/SESSION_MEMO.md) and [the manuscript draft](references/EMIT%20Flux%20derivation.pdf). The draft and inherited code are research work in progress.

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
