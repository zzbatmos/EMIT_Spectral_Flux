"""Offline checks for failure signaling and interrupted-case resume; no NASA calls."""
from concurrent.futures import Future
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import replicate_raw_batch as batch


class BatchRecoveryTests(unittest.TestCase):
    def run_batch(self, complete=False, missing_spectra=False, failure=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ts = '20230401T094135'
            name = f'flux_comparison_results_raz_ceres_{ts}.pkl'
            refs = root / 'Qianqian/Flux_Comparison_Surface_Reflectance_Data'
            refs.mkdir(parents=True)
            (refs / name).touch()
            case = root / 'outputs/raw_reproduction' / ts
            if complete:
                case.mkdir(parents=True)
                for filename in ['provenance.json', name, 'collocation.npz', 'spectra_and_geometry.npz']:
                    (case / filename).touch()
                (case / 'validation.json').write_text(json.dumps({'reference_exists': True,
                    'fields': {'EMIT_Fup': {'allclose_rtol1e-5_atol1e-4': True}}}))
                if missing_spectra:
                    (case / 'spectra_and_geometry.npz').unlink()
            with patch.object(batch, 'ROOT', root), patch.object(batch, 'manifest_name'), \
                 patch.object(batch, 'ProcessPoolExecutor') as pool, \
                 patch.object(sys, 'argv', ['replicate_raw_batch.py', '--workers', '2']), \
                 contextlib.redirect_stdout(io.StringIO()):
                future = Future()
                future.set_result({'timestamp': ts, 'status': 'error' if failure else 'done',
                                   'validation_failed_fields': []})
                executor = pool.return_value.__enter__.return_value
                executor.submit.return_value = future
                if failure:
                    with self.assertRaises(SystemExit):
                        batch.main()
                else:
                    batch.main()
                submitted = executor.submit.call_count
            checkpoint = json.loads((root / 'outputs/raw_reproduction/batch_status.json').read_text())
            self.assertFalse((root / 'outputs/raw_reproduction/batch_status.tmp').exists())
            return submitted, checkpoint['cases'][0]['status']

    def test_completed_case_needs_no_worker(self):
        self.assertEqual(self.run_batch(complete=True), (0, 'resumed'))

    def test_missing_artifact_is_requeued(self):
        self.assertEqual(self.run_batch(complete=True, missing_spectra=True), (1, 'done'))

    def test_worker_error_is_checkpointed_and_fails_command(self):
        self.assertEqual(self.run_batch(failure=True), (1, 'error'))


if __name__ == '__main__':
    unittest.main()
