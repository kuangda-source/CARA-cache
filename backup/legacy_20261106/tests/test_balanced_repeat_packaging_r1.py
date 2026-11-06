"""Production-CPU metadata and real isolated source bytes; no SSH or GPU."""
import copy
from contextlib import redirect_stdout
import gzip
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wcomr.immutable_stage_payload_r1 import local_python_closure

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location('synthetic_N08_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def completed_common():
    capture = dict(launch=dict(source_revision='SYNTHETIC_COMPLETED_N07'), config_sha256='b' * 64)
    acceptance = dict(terminal_receipt_audit_accepted=True,
        scientific_available_cohorts_with_registered_missingness=True,
        original_runner_paths=180, scope_counts=dict(total_paths=180, scientific_paths=160),
        original_status_counts=dict(COMPLETE=178, TEXT_REJECTED=2, VIDEO_REJECTED=0, TECH_FAILED=0, NOT_REACHED=0),
        capture_sha256='a' * 64, source_revision=capture['launch']['source_revision'])
    return acceptance, capture


class ProductionCPUPackagingControls(unittest.TestCase):
    def test_original_common_completion_gate_retains_valid_rejections_not_test_scores(self):
        module = script('deploy_wc_paper_N08_production_cpu_r1')
        acceptance, capture = completed_common(); original = copy.deepcopy((acceptance, capture))
        module.accepted_common_identity(acceptance, capture, capture_sha256='a' * 64, shared_config_sha256='b' * 64)
        self.assertEqual((acceptance, capture), original)
        # Scores are deliberately absent: timing bindings were frozen earlier.
        for kind in ('audit', 'unfinished', 'source', 'capture', 'config', 'short', 'technical'):
            accepted, observed = copy.deepcopy(original)
            if kind == 'audit': accepted['terminal_receipt_audit_accepted'] = False
            elif kind == 'unfinished': accepted['original_status_counts']['NOT_REACHED'] = 1
            elif kind == 'source': observed['launch']['source_revision'] = 'SYNTHETIC_OTHER'
            elif kind == 'capture': accepted['capture_sha256'] = '0' * 64
            elif kind == 'config': observed['config_sha256'] = '0' * 64
            elif kind == 'short': accepted['scope_counts']['scientific_paths'] = 159
            else: accepted['original_status_counts']['TECH_FAILED'] = 1
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                module.accepted_common_identity(accepted, observed,
                    capture_sha256='a' * 64, shared_config_sha256='b' * 64)

    def test_missing_real_final_config_refuses_before_network(self):
        module = script('deploy_wc_paper_N08_production_cpu_r1')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = ['SYNTHETIC', '--base-CPU-capture', str(root / 'base.gz'), '--N07-capture', str(root / 'n07.gz'),
                    '--N07-acceptance', str(root / 'accepted.json'), '--stage', '.sync/wc-paper-n08-SYNTHETIC',
                    '--output', str(root / 'launch.json')]
            with patch.object(module, 'ROOT', root), patch.object(sys, 'argv', args), \
                    patch.object(module.subprocess, 'run') as network:
                with self.assertRaises(FileNotFoundError): module.main()
            network.assert_not_called(); self.assertFalse((root / 'launch.json').exists())

    def test_before_CPU_ETA_never_calls_SSH(self):
        module = script('capture_wc_paper_N08_production_cpu_r1')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); launch = root / 'launch.json'; output = root / 'capture.gz'
            launch.write_text(json.dumps(dict(launch=dict(first_collection_not_before_unix=1000.))))
            with patch.object(sys, 'argv', ['SYNTHETIC', '--launch-ref', str(launch), '--output', str(output)]), \
                    patch.object(module.time, 'time', return_value=999.), patch.object(module.subprocess, 'run') as network:
                with self.assertRaisesRegex(SystemExit, 'Before original N08 CPU ETA'): module.main()
            network.assert_not_called(); self.assertFalse(output.exists())

    def test_one_observation_bytes_survive_local_parse_failure_without_second_network(self):
        module = script('capture_wc_paper_N08_production_cpu_r1')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); launch = root / 'launch.json'; output = root / 'capture.gz'
            launch.write_text(json.dumps(dict(launch=dict(first_collection_not_before_unix=1.))))
            raw = gzip.compress(b'SYNTHETIC_BAD_JSON')
            with patch.object(sys, 'argv', ['SYNTHETIC', '--launch-ref', str(launch), '--output', str(output)]), \
                    patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=raw, stderr=b'')) as network:
                with self.assertRaises(json.JSONDecodeError): module.main()
            self.assertEqual(network.call_count, 1); self.assertEqual(output.read_bytes(), raw)

    def test_actual_metadata_body_under_cold_stdlib_interpreter(self):
        module = script('capture_wc_paper_N08_production_cpu_r1')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); stage = root / '.sync/SYNTHETIC'; package = stage / 'src/wcomr'
            package.mkdir(parents=True)
            for name in ('__init__.py', 'gpu_budget_pool_v2.py'):
                shutil.copyfile(ROOT / 'src/wcomr' / name, package / name)
            sha = lambda p: __import__('hashlib').sha256(p.read_bytes()).hexdigest()
            registration = dict(source_revision='SYNTHETIC_CPU_ONLY',
                payload_sha256={'src/wcomr/' + n: sha(package / n) for n in ('__init__.py', 'gpu_budget_pool_v2.py')})
            (stage / 'registration.json').write_text(json.dumps(registration))
            config = stage / 'configs/wc_paper_N08_balanced_full40_production_r1_20261016.json'
            config.parent.mkdir()
            reference = stage / 'SYNTHETIC_REFERENCE.json.gz'; reference.write_bytes(gzip.compress(b'{"synthetic":true}'))
            config.write_text(json.dumps(dict(references=dict(control=dict(ref=reference.name, sha256=sha(reference))))))
            (stage / 'N08-CPU-bundle-result.json').write_text(json.dumps(dict(status='SYNTHETIC_METADATA_ONLY_NOT_PASS', exit_code=0)))
            launch = dict(stage=str(stage), pid=99999999, source_revision=registration['source_revision'],
                registration_sha256=sha(stage / 'registration.json'))
            original = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
            child = subprocess.run([sys.executable, '-S', '-c', module.remote_code(launch)],
                cwd=root, env={**env, 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, timeout=10)
            self.assertEqual(child.returncode, 0, child.stderr.decode())
            observed = json.loads(gzip.decompress(child.stdout))
            self.assertEqual(observed['files']['control']['data'], dict(synthetic=True))
            self.assertEqual(observed['registration_sha256'], launch['registration_sha256'])
            self.assertTrue(all(observed['payload_verified'].values())); self.assertEqual(observed['GPU_submissions'], 0)
            self.assertEqual({str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}, original)

    def test_actual_bootstrap_installs_one_fresh_CPU_only_stage_and_never_overwrites_base(self):
        module = script('deploy_wc_paper_N08_production_cpu_r1')
        spec = importlib.util.spec_from_file_location('synthetic_archive_fixture',
            Path(__file__).with_name('test_immutable_stage_payload_r1.py'))
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        from wcomr.immutable_stage_payload_r1 import git_archive, plan
        with tempfile.TemporaryDirectory() as directory:
            root, base, old, _ = helper.fixture(Path(directory))
            target = root / '.sync/base'; target.parent.mkdir(); shutil.move(str(base), target); base = target
            names = ['src/wcomr/immutable_stage_payload_r1.py', 'src/wcomr/gpu_budget_pool_v2.py']
            for name in names:
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT / name, path)
            helper.write(root, 'scripts/run_wc_paper_N08_production_cpu_bundle_r1.py', b'# SYNTHETIC CHILD NEVER RUN\n')
            subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', '-c', 'user.name=Synthetic CPU Control', '-c', 'user.email=synthetic@invalid',
                'commit', '-qm', 'Synthetic bootstrap source only'], cwd=root, check=True, capture_output=True)
            revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
            value = plan(root, config_roots=['configs/final.json'], python_entrypoints=['scripts/entry.py'],
                extra_files=names + ['scripts/run_wc_paper_N08_production_cpu_bundle_r1.py'],
                base_registration_sha256=old['base_registration_sha256'], base_source_revision=old['base_source_revision'],
                numeric_sources={})
            archive = git_archive(root, value, revision)
            metadata = dict(base='.sync/base', stage='.sync/n08-SYNTHETIC', base_original_absolute=str(base),
                            source_revision=revision, plan=value)
            envelope = json.dumps(metadata).encode() + b'\n' + archive
            before = {str(p.relative_to(base)): p.read_bytes() for p in base.rglob('*') if p.is_file()}
            code = module.BOOTSTRAP.replace("'/home/gaokuangda/data/gkd/worldcache_omr'", repr(str(root)))
            identity = dict(pid=12345, state='R', start_ticks=123450,
                            command='SYNTHETIC run_wc_paper_N08_production_cpu_bundle_r1.py')
            with patch.object(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(envelope))), \
                    patch.object(sys, 'path', list(sys.path)), patch.object(subprocess, 'Popen', return_value=SimpleNamespace(pid=12345)) as child, \
                    patch('wcomr.gpu_budget_pool_v2.process_identity', return_value=identity), redirect_stdout(io.StringIO()):
                exec(compile(code, 'SYNTHETIC_CPU_BOOTSTRAP_NO_NETWORK', 'exec'), {})
            self.assertEqual(child.call_count, 1)
            self.assertEqual(child.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
            self.assertIn('run_wc_paper_N08_production_cpu_bundle_r1.py', child.call_args.args[0][1])
            stage = root / '.sync/n08-SYNTHETIC'
            registration = json.loads((stage / 'registration.json').read_text())
            self.assertEqual(registration['CPU_scope'], 'FROZEN_N08_PRODUCTION_CPU_PREPARATION_NO_GPU')
            launch = json.loads((stage / 'N08-CPU-launch.json').read_text())
            self.assertEqual(launch['expected_CPU_commands'], 9); self.assertEqual(launch['GPU_submissions'], 0)
            self.assertEqual(launch['first_collection_not_before_unix'] - launch['launched_unix'], 300.)
            self.assertFalse(launch['ledger_written']); self.assertFalse((root / 'reports/gpu-budget-v2.json').exists())
            self.assertEqual({str(p.relative_to(base)): p.read_bytes() for p in base.rglob('*') if p.is_file()}, before)

    def test_declared_fixture_pack_runs_all_eight_commands_in_isolated_local_stage(self):
        """Actual copied current source and original test files, no fake path imports."""
        module = script('deploy_wc_paper_N08_production_cpu_r1')
        from wcomr.balanced_repeat_cpu_acceptance_r1 import PATTERNS
        files = local_python_closure(ROOT, module.ENTRIES + module.TESTS)
        files['manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json'] = None
        self.assertIn('tests/test_frozen_shared_inputs_r1.py', files)
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            for name in files:
                path = stage / name; path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, path)
            env = dict(os.environ, PYTHONPATH=str(stage / 'src'), PYTHONDONTWRITEBYTECODE='1',
                CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='2')
            for pattern in PATTERNS:
                command = [sys.executable, '-m', 'unittest', 'discover', '-s', str(stage / 'tests'), '-p', pattern, '-v']
                child = subprocess.run(command, cwd=stage, env=env, capture_output=True, timeout=45)
                self.assertEqual(child.returncode, 0, pattern + '\n' + child.stderr.decode())


if __name__ == '__main__': unittest.main()
