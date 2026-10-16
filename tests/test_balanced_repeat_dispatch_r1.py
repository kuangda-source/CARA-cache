"""Full40 one-dispatch fence with fake children; no network or GPU process."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_shared_production_r1 import sha, write

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location('synthetic_' + path.stem, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def fixture(root, *, limit=3., delay=120):
    module = load(Path(__file__).with_name('test_balanced_repeat_supervision_r1.py'))
    config, bound, stage, registration, authority, pool = module.fixture(root, limit=limit)
    config['first_collection_delay_seconds'] = delay
    from wcomr.balanced_repeat_production_r1 import CONFIG, CPU_RESULT
    write(stage / CONFIG, config); registration['payload_sha256'][CONFIG] = sha(stage / CONFIG)
    write(stage / 'registration.json', registration)
    proof = json.loads((stage / CPU_RESULT).read_text()); proof.update(config_sha256=sha(stage / CONFIG), registration_sha256=sha(stage / 'registration.json'))
    write(stage / CPU_RESULT, proof)
    authority.update(config_sha256=sha(stage / CONFIG), production_CPU_sha256=sha(stage / CPU_RESULT))
    (stage / 'N08-launch-authorization.json').unlink()
    return config, bound, stage, registration, authority


def execute(code, root, config, bound, registration, popen, *, cpu_live=False):
    literal = "'/home/gaokuangda/data/gkd/worldcache_omr'"; assert code.count(literal) == 1
    code = code.replace(literal, repr(str(root)))
    def process(pid):
        if pid == 9999: return dict(pid=pid, state='R' if cpu_live else None, start_ticks=99990 if cpu_live else None, command='SYNTHETIC_CPU')
        return dict(pid=pid, state='R', start_ticks=pid * 10,
            command='supervise_wc_paper_N08_balanced_full40_r1.py' if pid == 1001 else 'watch_wc_paper_N08_post_cpu_r1.py')
    with patch('wcomr.balanced_repeat_production_r1.validate', return_value=(config, registration, None, None, None, None, bound, None)), \
            patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process), \
            patch('subprocess.Popen', side_effect=popen) as spawned, patch.object(sys, 'path', list(sys.path)), redirect_stdout(io.StringIO()):
        exec(compile(code, 'SYNTHETIC_N08_REMOTE_NO_NETWORK', 'exec'), {})
    return spawned


class DispatchControls(unittest.TestCase):
    def test_single_sup_and_CPU_post_dispatch_and_original_fence_survives_retry(self):
        script = load(ROOT / 'scripts/launch_wc_paper_N08_balanced_full40_r1.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); config, bound, stage, registration, authority = fixture(root)
            # A copied accepted base may contain N07 receipts. Never clobber them.
            (stage / 'GPU-launch-request.json').write_text('SYNTHETIC_OLD_BASE_RECEIPT')
            old = sha(stage / 'GPU-launch-request.json'); calls = []
            def popen(command, **kwargs): calls.append(command); return SimpleNamespace(pid=1000 + len(calls))
            code = script.remote_code(str(stage.relative_to(root)), authority)
            execute(code, root, config, bound, registration, popen)
            result = json.loads((stage / 'N08-GPU-launch.json').read_text())
            self.assertEqual(len(calls), 2); self.assertEqual(result['scope_counts']['total_paths'], 40)
            self.assertEqual(result['supervisor_pid'], 1001); self.assertEqual(result['post_watcher_pid'], 1002)
            self.assertAlmostEqual(result['next_check_not_before_unix'] - result['started_unix'], 120.)
            self.assertEqual(sha(stage / 'GPU-launch-request.json'), old)
            with self.assertRaises(FileExistsError): execute(code, root, config, bound, registration, popen)
            self.assertEqual(len(calls), 2)

    def test_CPU_authority_ETA_or_live_original_CPU_fail_before_any_dispatch_fence(self):
        script = load(ROOT / 'scripts/launch_wc_paper_N08_balanced_full40_r1.py')
        for kind in ('CPU_identity', 'native_guard', 'scope', 'at12', 'ETA', 'CPU_live'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory); config, bound, stage, registration, authority = fixture(root,
                    limit=12. if kind == 'at12' else 3., delay=None if kind == 'ETA' else 120)
                if kind == 'CPU_identity': authority['production_CPU_sha256'] = '0' * 64
                elif kind == 'native_guard':
                    from wcomr.balanced_repeat_production_r1 import CPU_RESULT
                    proof = json.loads((stage / CPU_RESULT).read_text()); proof['guardrail_checks'][0]['unguarded_execution_refused'] = False
                    write(stage / CPU_RESULT, proof); authority['production_CPU_sha256'] = sha(stage / CPU_RESULT)
                elif kind == 'scope': authority['scope_counts'] = {**config['scope_counts'], 'total_paths': 39}
                elif kind == 'at12': authority['kind'] = 'STANDING_STRICT_UNDER12'
                def forbidden(*args, **kwargs): raise AssertionError('SYNTHETIC NO CHILD ALLOWED')
                code = script.remote_code(str(stage.relative_to(root)), authority)
                with self.subTest(kind=kind), self.assertRaises((ValueError, AssertionError)):
                    execute(code, root, config, bound, registration, forbidden, cpu_live=kind == 'CPU_live')
                self.assertFalse((stage / 'N08-GPU-launch-request.json').exists())

    def test_transport_timeout_keeps_original_identity_and_never_retries(self):
        script = load(ROOT / 'scripts/launch_wc_paper_N08_balanced_full40_r1.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _, _, stage, _, authority = fixture(root)
            path = root / 'SYNTHETIC_AUTHORITY.json'; write(path, authority); output = root / 'unknown.json'
            args = ['SYNTHETIC', '--stage', str(stage.relative_to(root)), '--authorization', str(path), '--output', str(output)]
            with patch.object(sys, 'argv', args), redirect_stdout(io.StringIO()), \
                    patch.object(script.subprocess, 'run', side_effect=subprocess.TimeoutExpired('SYNTHETIC', 180)) as network:
                with self.assertRaises(subprocess.TimeoutExpired): script.main()
            self.assertEqual(network.call_count, 1)
            result = json.loads(output.read_text()); self.assertFalse(result['GPU_retry_authorized'])
            self.assertFalse(result['original_task_terminal']); self.assertEqual(result['launch_id'], authority['launch_id'])

    def test_unparseable_success_transport_is_unknown_not_success_or_GPU_relaunch(self):
        script = load(ROOT / 'scripts/launch_wc_paper_N08_balanced_full40_r1.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _, _, stage, _, authority = fixture(root)
            path = root / 'SYNTHETIC_AUTHORITY.json'; write(path, authority); output = root / 'unknown.json'
            args = ['SYNTHETIC', '--stage', str(stage.relative_to(root)), '--authorization', str(path), '--output', str(output)]
            with patch.object(sys, 'argv', args), redirect_stdout(io.StringIO()), \
                    patch.object(script.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=b'SYNTHETIC_NOT_JSON', stderr=b'')):
                with self.assertRaises(SystemExit) as error: script.main()
            self.assertEqual(error.exception.code, 1)
            result = json.loads(output.read_text()); self.assertFalse(result['GPU_retry_authorized'])
            self.assertIn('UNKNOWN', result['status']); self.assertNotIn('dispatch', result)


if __name__ == '__main__': unittest.main()
