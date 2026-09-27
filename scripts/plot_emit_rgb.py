"""Stream a 2023 Sahara EMIT L1B scene from S3 and save a geolocated RGB.

Run from the project root after sourcing scripts/activate.sh.
The GLT convention follows NASA's EMIT-Data-Resources emit_tools.py:
https://github.com/nasa/EMIT-Data-Resources/blob/main/python/modules/emit_tools.py
"""
from contextlib import ExitStack
from pathlib import Path
import argparse
import json
import sys
import time

import earthaccess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import requests
import xarray as xr

HELPERS = Path.home() / '.codex/skills/earthaccess-nasa-data/scripts'
sys.path.insert(0, str(HELPERS))
from earthaccess_helpers import search_with_retry


def instance_region():
    """Read only the EC2 region, never instance credentials or identity documents."""
    try:
        s = requests.Session()
        s.trust_env = False
        token = s.put('http://169.254.169.254/latest/api/token',
                      headers={'X-aws-ec2-metadata-token-ttl-seconds': '60'}, timeout=3)
        token.raise_for_status()
        r = s.get('http://169.254.169.254/latest/meta-data/placement/region',
                  headers={'X-aws-ec2-metadata-token': token.text}, timeout=3)
        r.raise_for_status()
        return r.text
    except requests.RequestException:
        return 'unavailable (S3 backend checked separately)'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('outputs/emit_rgb'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    region = instance_region()
    print('AWS region:', region, flush=True)
    auth = earthaccess.login(strategy='netrc', persist=False)
    if not auth.authenticated:
        raise RuntimeError('Earthdata authentication failed')
    query = dict(short_name='EMITL1BRAD', version='001',
                 temporal=('2023-04-26T09:07:18', '2023-04-26T09:07:20'),
                 bounding_box=(10, 15, 30, 30), count=1)
    granules = search_with_retry(**query)
    if not granules:
        raise RuntimeError('Selected scene was not returned by CMR')
    granule = granules[0]
    scene = granule['umm']['GranuleUR']
    print('Scene:', scene, flush=True)
    # A RAD granule includes both RAD and OBS files. Select explicitly, not by order.
    files = None
    for attempt in range(3):
        try:
            files = earthaccess.open([granule])
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3 * 2**attempt)
    with ExitStack() as stack:
        for handle in files:
            stack.callback(handle.close)
        handle = next(f for f in files if Path(f.path).name.startswith('EMIT_L1B_RAD_'))
        raw_handle = getattr(handle, 'f', handle)
        backend = type(raw_handle).__module__ + '.' + type(raw_handle).__name__
        if 's3' not in backend.lower():
            raise RuntimeError(f'Direct S3 access required, got {backend}')
        print('Verified direct S3 backend:', backend, flush=True)
        root = stack.enter_context(xr.open_dataset(handle, engine='h5netcdf'))
        bands = stack.enter_context(xr.open_dataset(handle, engine='h5netcdf', group='sensor_band_parameters'))
        loc = stack.enter_context(xr.open_dataset(handle, engine='h5netcdf', group='location'))
        wavelengths = bands.wavelengths.values
        indices = [int(np.argmin(abs(wavelengths - target))) for target in (650, 550, 450)]
        chosen = wavelengths[indices].astype(float)
        print('RGB wavelengths (nm):', chosen, flush=True)
        print('Radiance storage chunks:', root.radiance.encoding.get('chunksizes'), flush=True)
        # Load only three spectral slices, not the full 285-band cube.
        rgb = np.stack([root.radiance.isel(bands=i).values for i in indices], axis=-1)
        rgb = np.where(rgb >= 0, rgb, np.nan)
        valid = np.isfinite(rgb).all(axis=-1)
        if not valid.any():
            raise RuntimeError('No valid RGB radiance samples')
        lo, hi = np.percentile(rgb[valid], [2, 98], axis=0)
        if np.any(hi <= lo):
            raise RuntimeError('Degenerate contrast range')
        display = np.clip((rgb-lo)/(hi-lo), 0, 1)**(1/2.2)
        display[~valid] = np.nan
        gx = np.nan_to_num(loc.glt_x.values, nan=0).astype(np.int32)
        gy = np.nan_to_num(loc.glt_y.values, nan=0).astype(np.int32)
        valid_glt = (gx > 0) & (gy > 0) & (gx <= rgb.shape[1]) & (gy <= rgb.shape[0])
        ortho = np.full((*gx.shape, 4), 0.0, dtype=np.float32)
        sampled = display[gy[valid_glt]-1, gx[valid_glt]-1]
        ortho[valid_glt, :3] = np.nan_to_num(sampled)
        ortho[valid_glt, 3] = np.isfinite(sampled).all(axis=-1)
        gt = np.asarray(root.attrs['geotransform'])
        if gt[2] != 0 or gt[4] != 0 or gt[1] <= 0 or gt[5] >= 0:
            raise ValueError('Expected north-up unrotated geotransform')
        extent = [gt[0], gt[0]+gx.shape[1]*gt[1], gt[3]+gx.shape[0]*gt[5], gt[3]]
        assert extent[0] >= -20 and extent[1] <= 40 and extent[2] >= 15 and extent[3] <= 35
        timestamp = root.attrs['time_coverage_start']
        fig, ax = plt.subplots(figsize=(10, 10), layout='constrained')
        ax.set_facecolor('#eef0f2')
        ax.imshow(ortho, extent=extent, origin='upper', interpolation='nearest')
        ax.set_aspect(1/np.cos(np.deg2rad((extent[2]+extent[3])/2)))
        ax.set_xlabel('Longitude (°E)')
        ax.set_ylabel('Latitude (°N)')
        ax.set_title('EMIT L1B · Sahara, Egypt\n' + timestamp.replace('+0000', ' UTC').replace('T',' ',1), fontsize=15)
        fig.text(0.5, 0.005, 'RGB: ' + ' / '.join(f'{w:.1f}' for w in chosen) + ' nm  |  Per-band 2–98% stretch, gamma 2.2\n'
                 'At-sensor radiance visualization; GLT orthorectified; no cloud screening', ha='center', fontsize=9)
        fig.get_layout_engine().set(rect=(0, 0.05, 1, 0.95))
        png = args.output_dir / f'{scene}_RGB.png'
        fig.savefig(png, dpi=180)
        plt.close(fig)
        plt.imsave(args.output_dir / f'{scene}_RGB_unannotated.png', ortho)
        metadata = {
            'granule': scene, 'collection': query['short_name'], 'version': query['version'],
            'query': query, 'time_start': timestamp, 'time_end': root.attrs['time_coverage_end'],
            's3_url': 's3://' + handle.path, 'aws_region': region, 'backend': backend,
            'radiance_units': root.radiance.attrs['units'], 'rgb_wavelengths_nm': chosen.tolist(),
            'rgb_band_indices_zero_based': indices, 'raw_shape': list(rgb.shape),
            'ortho_shape': list(ortho.shape), 'extent_west_east_south_north': list(extent),
            'geotransform': gt.tolist(), 'stretch_percentiles': [2, 98],
            'stretch_lower_radiance': lo.tolist(), 'stretch_upper_radiance': hi.tolist(),
            'gamma': 2.2, 'valid_raw_fraction': float(valid.mean()),
            'valid_ortho_pixels': int((ortho[:,:,3] > 0).sum()),
            'notes': 'Display RGB from L1B radiance, not surface reflectance or spectral flux; no cloud screening. Version 001 selected for continuity with inherited 2023 work; CMR also lists 002.',
            'glt_reference': 'https://github.com/nasa/EMIT-Data-Resources/blob/main/python/modules/emit_tools.py',
        }
        (args.output_dir/f'{scene}_metadata.json').write_text(json.dumps(metadata, indent=2))
        (args.output_dir/f'{scene}_cmr.json').write_text(json.dumps(dict(granule), indent=2))
        print(json.dumps(metadata, indent=2), flush=True)
        print('Saved:', png, flush=True)


if __name__ == '__main__':
    main()
