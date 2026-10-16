"""Exercise the dispatch fence with fake child handles, no SSH or GPU process."""
from contextlib import redirect_stdout
import importlib.util
import io
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_shared_production_r1 import CONFIG, PRODUCTION_CPU_STATUS, fingerprint, sha, write


def load(path):
    spec = importlib.util.spec_from_file_location('synthetic_dispatch_' + path.stem, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def fixture(root, *, limit=10., delay=120):
    contract = load(Path(__file__).with_name('test_frozen_shared_production_r1.py'))
    config, bound = contract.fixture()
    config.update(billed_limit_GPUh=limit, first_collection_delay_seconds=delay)
    relative = '.sync/SYNTHETIC_N07_NOT_A_PRODUCTION_STAGE'; stage = root / relative; stage.mkdir(parents=True)
    write(stage / CONFIG, config)
    scripts = [f'scripts/{name}' for name in ('run_wc_paper_N07_frozen_shared180_r1.py',
        'supervise_wc_paper_N07_frozen_shared180_r1.py', 'watch_wc_paper_N07_post_cpu_r1.py')]
    for name in scripts:
        path = stage / name; path.parent.mkdir(exist_ok=True); path.write_text('# SYNTHETIC NOT EXECUTABLE\n')
    registration = dict(source_revision='SYNTHETIC_NOT_DISPATCHED',
        payload_sha256={name: sha(stage / name) for name in [CONFIG] + scripts})
    write(stage / 'registration.json', registration)
    proof = dict(status=PRODUCTION_CPU_STATUS, exit_code=0, source_revision=registration['source_revision'],
        registration_sha256=sha(stage / 'registration.json'), config_sha256=sha(stage / CONFIG),
        actual_sample_argument_variants=160, matrix=bound['execution_plan'],
        runner_source_sha256=sha(stage / scripts[0]))
    write(stage / 'production-CPU-result.json', proof)
    fixture_module = load(Path(__file__).with_name('test_frozen_shared_acceptance_r1.py'))
    write(stage / 'CPU-bundle-result.json', fixture_module.synthetic_CPU_bundle(registration['source_revision']))
    write(stage / 'CPU-launch.json', dict(source_revision=registration['source_revision'],
        identity=dict(pid=9999, start_ticks=99990)))
    authority = dict(source_revision=registration['source_revision'], config_sha256=sha(stage / CONFIG),
        production_CPU_sha256=sha(stage / 'production-CPU-result.json'), bound_input_fingerprint=fingerprint(bound),
        scope_counts=config['scope_counts'], whole_card_run=config['run_id'], gpu_uuid='GPU-SYNTHETIC-NO-DEVICE',
        forecast_complete_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'],
        cumulative_cap_GPUh=config['cumulative_cap_GPUh'], budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
        direct_user_authorization=True, user_reply_quote='SYNTHETIC quote only: `$(not-executed)`\n',
        launch_id='SYNTHETIC-NO-GPU-LAUNCH', kind='STANDING_STRICT_UNDER12')
    return config, bound, stage, relative, registration, authority


def execute_code(code, root, config, bound, registration, popen):
    # Only the fixed remote root literal changes, into this test's temporary
    # directory. Real launch/CPU/scope validation remains; child creation and
    # physical asset validation are explicitly mocked.
    literal = "'/home/gaokuangda/data/gkd/worldcache_omr'"
    if code.count(literal) != 1: raise AssertionError('Synthetic root replacement must be exact')
    code = code.replace(literal, repr(str(root)))
    def process(pid):
        if pid == 9999: return dict(pid=pid, start_ticks=None, state=None, command=None)
        command = 'supervise_wc_paper_N07_frozen_shared180_r1.py' if pid == 1001 else 'watch_wc_paper_N07_post_cpu_r1.py'
        return dict(pid=pid, start_ticks=pid * 10, state='R', command=command)
    with patch('wcomr.frozen_shared_production_r1.validate',
               return_value=(config, registration, None, None, None, None, bound, None)), \
         patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process), \
         patch('subprocess.Popen', side_effect=popen) as mocked, \
         patch.object(sys, 'path', list(sys.path)), redirect_stdout(io.StringIO()):
        exec(compile(code, 'SYNTHETIC_REMOTE_NO_NETWORK', 'exec'), {})
    return mocked


class DispatchControls(unittest.TestCase):
    def test_one_original_dispatch_and_post_fence_refuse_lost_reply_retry(self):
        script = load(Path(__file__).resolve().parents[1] / 'scripts/launch_wc_paper_N07_frozen_shared180_r1.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); config, bound, stage, relative, registration, authority = fixture(root)
            code = script.remote_code(relative, authority); calls = []
            def popen(command, **kwargs):
                calls.append(command)
                return SimpleNamespace(pid=1000 + len(calls))
            execute_code(code, root, config, bound, registration, popen)
            receipt = json.loads((stage / 'GPU-launch.json').read_text())
            self.assertEqual(len(calls), 2)
            self.assertEqual(receipt['supervisor_pid'], 1001)
            self.assertEqual(receipt['post_watcher_pid'], 1002)
            self.assertEqual(receipt['scope_counts']['total_paths'], 180)
            self.assertAlmostEqual(receipt['next_check_not_before_unix'] - receipt['started_unix'], 120.)
            with self.assertRaises(FileExistsError): execute_code(code, root, config, bound, registration, popen)
            self.assertEqual(len(calls), 2)

    def test_invalid_CPU_scope_authority_or_ETA_fail_before_fence_and_process(self):
        script = load(Path(__file__).resolve().parents[1] / 'scripts/launch_wc_paper_N07_frozen_shared180_r1.py')
        for kind in ('CPU', 'scope', 'at12', 'ETA'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config, bound, stage, relative, registration, authority = fixture(root,
                    limit=12. if kind == 'at12' else 10., delay=None if kind == 'ETA' else 120)
                if kind == 'CPU': authority['production_CPU_sha256'] = '0' * 64
                if kind == 'scope': authority['scope_counts'] = {**config['scope_counts'], 'total_paths': 179}
                code = script.remote_code(relative, authority)
                def forbidden(*args, **kwargs): raise AssertionError('SYNTHETIC PROCESS MUST NOT START')
                with self.assertRaises((ValueError, AssertionError)):
                    execute_code(code, root, config, bound, registration, forbidden)
                self.assertFalse((stage / 'GPU-launch-request.json').exists())

    def test_before_ETA_terminal_capture_never_calls_SSH(self):
        script = load(Path(__file__).resolve().parents[1] / 'scripts/capture_wc_paper_N07_frozen_shared180_r1.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); launch = root / 'launch.json'; output = root / 'capture.json.gz'
            launch.write_text(json.dumps(dict(dispatch=dict(next_check_not_before_unix=1000.))))
            arguments = ['SYNTHETIC', '--launch-ref', str(launch), '--output', str(output)]
            with patch.object(sys, 'argv', arguments), patch.object(script.time, 'time', return_value=999.), \
                 patch.object(script.subprocess, 'run') as network:
                with self.assertRaisesRegex(SystemExit, 'Before original'): script.main()
                network.assert_not_called()
            self.assertFalse(output.exists())

    def test_transport_timeout_preserves_original_identity_without_retry(self):
        script = load(Path(__file__).resolve().parents[1] / 'scripts/launch_wc_paper_N07_frozen_shared180_r1.py')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); _, _, _, relative, _, authority = fixture(root)
            path = root / 'SYNTHETIC_AUTHORITY.json'; path.write_text(json.dumps(authority))
            output = root / 'SYNTHETIC_LOST_TRANSPORT.json'
            arguments = ['SYNTHETIC', '--stage', relative, '--authorization', str(path), '--output', str(output)]
            with patch.object(sys, 'argv', arguments), redirect_stdout(io.StringIO()), \
                 patch.object(script.subprocess, 'run', side_effect=subprocess.TimeoutExpired('SYNTHETIC_NO_NETWORK', 180)) as network:
                with self.assertRaises(subprocess.TimeoutExpired): script.main()
                self.assertEqual(network.call_count, 1)
            value = json.loads(output.read_text())
            self.assertFalse(value['GPU_retry_authorized'])
            self.assertFalse(value['original_task_terminal'])
            self.assertEqual(value['launch_id'], authority['launch_id'])

    def test_admission_capture_resolves_project_and_output_aliases_without_science_reads(self):
        script = load(Path(__file__).resolve().parents[1] / 'scripts/capture_wc_paper_N07_frozen_shared180_r1.py')
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); physical = parent / 'physical'; physical.mkdir()
            alias = parent / 'logical'; alias.symlink_to(physical, target_is_directory=True)
            storage = parent / 'storage'; storage.mkdir()
            (physical / 'outputs').symlink_to(storage, target_is_directory=True)
            stage = physical / '.sync/SYNTHETIC_CAPTURE'; stage.mkdir(parents=True)
            source = stage / 'src/control.py'; source.parent.mkdir(parents=True); source.write_text('# synthetic\n')
            registration = dict(source_revision='SYNTHETIC_NO_TASK', payload_sha256={'src/control.py': sha(source)})
            write(stage / 'registration.json', registration)
            launch = dict(project=str(alias), stage=str(stage), run_id='SYNTHETIC_RUN', gpu_uuid='GPU-SYNTHETIC',
                source_revision=registration['source_revision'], registration_sha256=sha(stage / 'registration.json'))
            code = script.remote_code(launch, 'admission')
            literal = "'/home/gaokuangda/data/gkd/worldcache_omr'"
            self.assertEqual(code.count(literal), 1); code = code.replace(literal, repr(str(alias)))
            output = io.BytesIO()
            def telemetry(command, **kwargs):
                return 'GPU-SYNTHETIC, NVIDIA RTX A6000, 24' if '-i' in command else ''
            with patch('wcomr.gpu_budget_pool_v2.BudgetPool.read', return_value={'synthetic': True}), \
                 patch('subprocess.check_output', side_effect=telemetry), \
                 patch.object(sys, 'path', list(sys.path)), patch.object(sys, 'stdout', SimpleNamespace(buffer=output)):
                exec(compile(code, 'SYNTHETIC_ALIAS_CAPTURE_NO_NETWORK', 'exec'), {})
            captured = json.loads(gzip.decompress(output.getvalue()))
            self.assertEqual(captured['output_root'], str((storage / 'SYNTHETIC_RUN').resolve()))
            self.assertNotIn('runner', captured); self.assertNotIn('final', captured)
            self.assertTrue(all(captured['payload_verified'].values()))


if __name__ == '__main__': unittest.main()
