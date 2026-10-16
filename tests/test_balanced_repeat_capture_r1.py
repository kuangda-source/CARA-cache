"""Actual metadata body on a temp project; no SSH, tensors or model imports."""
import builtins
import gzip
import importlib.util
import io
import json
from pathlib import Path
import os
import subprocess
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_shared_production_r1 import sha, write
from wcomr.gpu_budget_pool_v2 import SCHEMA, BudgetPool

ROOT = Path(__file__).resolve().parents[1]


def script():
    path = ROOT / 'scripts/capture_wc_paper_N08_balanced_full40_r1.py'
    spec = importlib.util.spec_from_file_location('synthetic_N08_capture', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class OnceCaptureControls(unittest.TestCase):
    def test_before_original_ETA_never_calls_SSH(self):
        module = script()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); launch = root / 'launch.json'; output = root / 'capture.gz'
            write(launch, dict(dispatch=dict(next_check_not_before_unix=1000.)))
            args = ['SYNTHETIC', '--launch-ref', str(launch), '--output', str(output)]
            with patch.object(sys, 'argv', args), patch.object(module.time, 'time', return_value=999.), \
                    patch.object(module.subprocess, 'run') as network:
                with self.assertRaisesRegex(SystemExit, 'Before original'): module.main()
            network.assert_not_called(); self.assertFalse(output.exists())

    def test_admission_aliases_original_registration_and_no_numeric_or_scientific_import(self):
        self.check_body('admission')

    def test_terminal_reads_exact_SHA_bound_references_without_numeric_import(self):
        self.check_body('terminal')

    def test_cold_interpreter_without_site_packages_reads_only_stdlib_metadata(self):
        module = script()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); stage = root / '.sync/SYNTHETIC'; package = stage / 'src/wcomr'
            package.mkdir(parents=True)
            for name in ('__init__.py', 'gpu_budget_pool_v2.py'):
                (package / name).write_bytes((ROOT / 'src/wcomr' / name).read_bytes())
            registration = dict(source_revision='SYNTHETIC_NO_GPU', payload_sha256={
                'src/wcomr/' + n: sha(package / n) for n in ('__init__.py', 'gpu_budget_pool_v2.py')})
            write(stage / 'registration.json', registration)
            pool = dict(schema=SCHEMA, cap_gpu_hours=100., origin_used_gpu_hours=0., origin_gpu_jobs_launched=0, jobs={}, events=[])
            pool.update(BudgetPool.accounting(pool)); write(root / 'reports/gpu-budget-v2.json', pool)
            original = (root / 'reports/gpu-budget-v2.json').read_bytes()
            launch = dict(project=str(root), stage=str(stage), source_revision=registration['source_revision'],
                registration_sha256=sha(stage / 'registration.json'), run_id='SYNTHETIC_RUN', gpu_uuid='GPU-SYNTHETIC')
            code = module.remote_code(launch, 'admission').replace("'/home/gaokuangda/data/gkd/worldcache_omr'", repr(str(root)))
            # The child starts without any site packages. Telemetry alone is
            # a declared stand-in; BudgetPool and both source files are real.
            prefix = "import subprocess\nsubprocess.check_output=lambda cmd,**kw: 'GPU-SYNTHETIC, NVIDIA RTX A6000, 24' if '-i' in cmd else ''\n"
            env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
            child = subprocess.run([sys.executable, '-S', '-c', prefix + code],
                cwd=root, env=env, capture_output=True, timeout=10)
            self.assertEqual(child.returncode, 0, child.stderr.decode())
            captured = json.loads(gzip.decompress(child.stdout))
            self.assertEqual(captured['registration_sha256'], sha(stage / 'registration.json'))
            self.assertTrue(all(captured['payload_verified'].values()))
            self.assertEqual((root / 'reports/gpu-budget-v2.json').read_bytes(), original)

    def check_body(self, mode):
        module = script()
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = parent / 'physical'; root.mkdir()
            alias = parent / 'logical'; alias.symlink_to(root, target_is_directory=True)
            storage = parent / 'storage'; storage.mkdir(); (root / 'outputs').symlink_to(storage, target_is_directory=True)
            stage = root / '.sync/SYNTHETIC'; stage.mkdir(parents=True)
            source = stage / 'src/control.py'; source.parent.mkdir(); source.write_text('# SYNTHETIC\n')
            registration = dict(source_revision='SYNTHETIC_NOT_DEPLOYED', payload_sha256={'src/control.py': sha(source)})
            write(stage / 'registration.json', registration)
            launch = dict(project=str(alias), stage=str(stage), source_revision=registration['source_revision'],
                registration_sha256=sha(stage / 'registration.json'), run_id='SYNTHETIC_RUN', gpu_uuid='GPU-SYNTHETIC')
            if mode == 'terminal':
                # Only test the actual collector's reference reading, not a valid inference config.
                from wcomr.balanced_repeat_production_r1 import CONFIG
                target = stage / 'meta/shared.json.gz'; target.parent.mkdir(); target.write_bytes(gzip.compress(b'{"synthetic":true}'))
                config = dict(references={'shared_config': dict(ref='meta/shared.json.gz', sha256=sha(target))})
                write(stage / CONFIG, config); launch['config_sha256'] = sha(stage / CONFIG)
            code = module.remote_code(launch, mode); literal = "'/home/gaokuangda/data/gkd/worldcache_omr'"
            self.assertEqual(code.count(literal), 1); code = code.replace(literal, repr(str(alias)))
            output = io.BytesIO(); original_import = builtins.__import__
            def imports(name, *args, **kwargs):
                if name in ('torch', 'wcomr.balanced_repeat_production_r1', 'wcomr.frozen_shared_production_r1'):
                    raise AssertionError('Metadata collector imported a numeric production dependency')
                return original_import(name, *args, **kwargs)
            def telemetry(command, **kwargs): return 'GPU-SYNTHETIC, NVIDIA RTX A6000, 24' if '-i' in command else ''
            with patch('wcomr.gpu_budget_pool_v2.BudgetPool.read', return_value={'synthetic': True}), \
                    patch('subprocess.check_output', side_effect=telemetry), patch.object(sys, 'path', list(sys.path)), \
                    patch.object(sys, 'stdout', SimpleNamespace(buffer=output)), patch('builtins.__import__', side_effect=imports):
                exec(compile(code, 'SYNTHETIC_METADATA_ONLY_NO_NETWORK', 'exec'), {})
            captured = json.loads(gzip.decompress(output.getvalue()))
            self.assertEqual(captured['registration_sha256'], sha(stage / 'registration.json'))
            self.assertEqual(captured['output_root'], str((storage / 'SYNTHETIC_RUN').resolve()))
            self.assertNotIn('runner', captured); self.assertNotIn('final', captured)
            if mode == 'terminal': self.assertEqual(captured['shared_config'], {'synthetic': True})


if __name__ == '__main__': unittest.main()
