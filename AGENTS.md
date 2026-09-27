# Project working context

Read `docs/SESSION_MEMO.md` at the start of a session. Update it with substantive decisions, verified results, unresolved issues, and the next useful step before ending scientific work.

Use `source scripts/activate.sh` for the local environment. Preserve inherited research files unless the task calls for changing them. Do not execute legacy scripts merely to import functions: many run data access and analysis at module scope.

Keep spectral radiance, spectral flux, and integrated flux distinct, with explicit units and wavelength coordinates. Record ADM provenance, scene selection, angle conventions, cloud screening, spatial/temporal collocation, and UV regression provenance. Treat manuscript plots as reported results until reproduced. Do not silently resolve discrepancies between manuscript and code.

Do not commit credentials, recovery codes, raw satellite data, caches, or generated pickle results. Review notebook outputs before staging. Use the installed `earthaccess-nasa-data` skill when accessing NASA Earthdata; keep credentials in external credential storage. Keep commits local unless publication is requested.
