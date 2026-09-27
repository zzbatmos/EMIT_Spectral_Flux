"""One-command reproduction: offline by default; --raw resumes original S3 computation."""
import argparse
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw', action='store_true', help='Run/resume the pilot and all raw S3 cases first')
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--skip-pdf', action='store_true')
    args = p.parse_args()
    if args.workers < 1:
        p.error('--workers must be positive')
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MPLCONFIGDIR=str(ROOT / '.cache/matplotlib'))
    Path(env['MPLCONFIGDIR']).mkdir(parents=True, exist_ok=True)

    def run(script, *options):
        cmd = [sys.executable, str(ROOT / 'scripts' / script), *options]
        print('Running:', ' '.join(cmd), flush=True)
        subprocess.run(cmd, cwd=ROOT, env=env, check=True)

    if args.raw:
        run('replicate_raw_case.py', '20230401T094135', '--include-rfl')
        run('replicate_raw_batch.py', '--workers', str(args.workers))
    run('verify_reproduction.py')
    run('summarize_raw_reproduction.py', '--require-complete')
    run('reproduce_saved_flux_comparison.py')
    run('reproduce_saved_flux_comparison.py', '--input-dir', 'outputs/raw_reproduction/flux_results',
        '--output-dir', 'outputs/raw_reproduction/comparison',
        '--title', 'EMIT–CERES comparison · Recomputed from original April 2023 observations',
        '--scope', 'Raw S3 observations recomputed for 577 historical cases; see raw_validation_summary.json for validation and scope.')
    run('verify_reproduction.py', '--check-comparison')
    if not args.skip_pdf:
        run('build_reproduction_report.py')
    print('Reproduction complete; outputs/raw_reproduction/comparison/ and docs/EMIT_CERES_Reproduction_Guide.pdf', flush=True)


if __name__ == '__main__':
    main()
