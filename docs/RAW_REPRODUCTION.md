# Reproduction from original EMIT and CERES observations

This run reconstructs the TOA flux calculations for the 577 April 2023 timestamps represented in Qianqian's saved results. It independently selects CERES footprints and computes EMIT fluxes from the satellite observations. The historical pickle contents are read afterward for numerical validation; their timestamps define the scope of this run. This does not recover every case in the historical notebook's broader collocation search.

## Completed results — 2026-09-27

All 577 cases completed successfully: 4,844 reconstructed footprint records, with no shape, NaN-pattern or tolerance failures in the compared fields. Maximum absolute differences were 1.14 × 10⁻¹³ W m⁻² for measured-band and UV-augmented upward flux, 2.70 × 10⁻⁴ W m⁻² for incoming flux, and 1.07 × 10⁻⁴ degrees for relative azimuth. CERES coordinates, reported fluxes and geometry agree exactly. Pilot wavelength and surface-reflectance spectra agree exactly.

The final comparison contains the same 1,482 record identities across 339 EMIT scenes as the historical reproduction. Both manuscript regressions are recovered:

| Comparison | Slope | Intercept (W m⁻²) | Pearson R | RMSE (W m⁻²) |
| --- | ---: | ---: | ---: | ---: |
| Direct | 1.08041303 | 1.23390975 | 0.93434055 | 37.1090 |
| Solar-angle adjusted | 1.00138307 | 12.48820260 | 0.97761012 | 19.5391 |

The adjusted mean EMIT-minus-CERES difference is 12.954575 W m⁻², with population standard deviation 14.627226 W m⁻². Full-precision results: [raw validation](raw_validation_summary.json) and [comparison statistics](raw_flux_comparison_summary.json). The combined figure was visually inspected; source record identities and manuscript-rounded fit coefficients were checked programmatically.

## Inputs and execution

- EMIT L1B RAD and OBS Version 001, identified by the supplied `EMIT_L1B.txt`, read directly from LP DAAC S3 on this AWS us-west-2 instance.
- CERES Terra-FM2 MODIS SSF Edition4A, build 407405, from ASDC S3. Selected hourly HDF4 files are cached under `data/ceres_terra_april/` for pyhdf.
- Original desert ADM CSV tables in `Zhibo/Leob2005_ADM/`; all 4,844 saved ADM factors also independently agree with their bin lookup.
- EMIT L2A surface reflectance, identified by `EMIT_L2A.txt`, recomputed for the nine-footprint pilot `20230401T094135` only. Surface-reflectance spectra do not enter the TOA comparison and were not recomputed for the remaining cases.

Six worker processes run concurrently. Contiguous radiance arrays are read through checked 32 MiB S3 byte ranges, with four I/O threads per process, into their native float32 layout. The original spatial averaging order is retained. Full EMIT cubes are discarded after each case; mean spectra and sampled geolocation are retained. Authentication retries and serialization handle transient credential-service failures. Per-file locks protect the CERES cache. Completed cases are resumable.

See the [README](../README.md#recompute-from-original-observations) for commands. The three new scripts are `replicate_raw_case.py`, `replicate_raw_batch.py`, and `summarize_raw_reproduction.py`. Original research scripts, data and saved results are unchanged.

## Preserved scientific and numerical rules

The search examines five CERES hourly files at offsets −2 through +2 hours around each EMIT timestamp. CERES centers must lie within ±0.3° of the EMIT scene mean location; the last matching hourly file wins, as in the historical script. Footprints must have 100% clear coverage. EMIT pixels within 20 km of each selected CERES center supply average radiance and viewing geometry. This reproduces the historical selection; it does not impose a new footprint-level time separation criterion.

Spectral flux is `π × mean radiance / (100 × ADM)` in W m⁻² nm⁻¹, converting from the EMIT radiance units µW cm⁻² sr⁻¹ nm⁻¹. The desert broadband ADM is treated as wavelength independent. Trapezoidal integration over the measured EMIT wavelengths gives measured-band flux. The original UV addition is `1.01 × integrated flux at wavelengths ≤420 nm + 4.86 W m⁻²`. The output key `EMIT_Fup_fullspectrum` retains its historical name; this is the UV-augmented EMIT spectral interval, not a measurement of the entire CERES shortwave spectrum.

NumPy 2 changed scalar promotion compared with the historical NumPy environment. Explicit float64 scalar latitude, relative-azimuth and integration arithmetic restore the original pixel selection and flux calculation. Remaining differences are assessed with `rtol=1e-5`, `atol=1e-4`, plus shape and NaN-pattern checks. Numerical agreement demonstrates reproduction, not independent validation of the ADM or UV assumptions.

The comparison excludes files containing more than 20 footprints, applies the original default Basemap land mask to unchanged CERES longitudes, and removes NaN reflectances. The known 0–360° versus −180–180° longitude issue is deliberately preserved. Correcting it changes the comparison population and should be a separate analysis.

## Artifacts

Under `outputs/raw_reproduction/`, each timestamp has source URLs, selected CERES indices, EMIT pixel counts, calculated flux dictionaries, mean radiance spectra, sampled geolocation, and per-field validation differences. `raw_validation_summary.json` aggregates the validation. `comparison/` contains the two regression plots, their combined PNG/PDF, full-precision statistics, input hashes, and record-level selection CSV.

`raw_collocation_map.png` and `.pdf` show 53 clear CERES footprints across six April 1 EMIT scenes. Display polygons use every fourth geolocation pixel; fluxes use full-resolution selections. `pilot_spectral_flux.png` shows the nine pilot spectra over measured EMIT wavelengths, without inventing a spectral shape for the empirical UV addition.
