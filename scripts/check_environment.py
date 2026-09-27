"""Check imports without accessing credentials, remote data, or legacy workflows."""
import importlib
import importlib.metadata
import sys

REQUIRED = {
    'numpy': 'numpy', 'scipy': 'scipy', 'pandas': 'pandas',
    'xarray': 'xarray', 'netCDF4': 'netCDF4', 'h5netcdf': 'h5netcdf',
    'h5py': 'h5py', 'earthaccess': 'earthaccess', 'requests': 'requests',
    'matplotlib': 'matplotlib', 'cartopy': 'cartopy', 'seaborn': 'seaborn',
    'pyhdf': 'pyhdf', 'jupyterlab': 'jupyterlab', 'ipykernel': 'ipykernel',
}
OPTIONAL = {'mpl_toolkits.basemap': 'basemap', 'mpl_scatter_density': 'mpl-scatter-density'}


def main():
    print(f'Python: {sys.executable} ({sys.version.split()[0]})')
    failures = []
    for module, distribution in {**REQUIRED, **OPTIONAL}.items():
        try:
            importlib.import_module(module)
            print(f'OK {distribution}=={importlib.metadata.version(distribution)}')
        except Exception as exc:
            optional = module in OPTIONAL
            print(f'{"OPTIONAL" if optional else "FAIL"} {distribution}: {exc}')
            if not optional:
                failures.append(module)
    import numpy as np
    print(f'Legacy np.trapz available: {hasattr(np, "trapz")}')
    print('Import check only; scientific workflows and Earthdata authentication are untested.')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
