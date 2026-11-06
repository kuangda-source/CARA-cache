"""Temporary real pool/UUID locks with explicitly mocked children and telemetry."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from wcomr.balanced_repeat_production_r1 import CONFIG, CPU_RESULT, RUN
from wcomr.frozen_shared_production_r1 import fingerprint, sha, write
from wcomr.gpu_budget_pool_v2 import BudgetPool, DeviceLease
from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location('synthetic_' + path.stem, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def fixture(root, *, limit=3.):
    helper = load(Path(__file__).with_name('test_balanced_repeat_cpu_acceptance_r1.py'))
    value = helper.fixture(); files = value['files']; config = files['config']['data']
    bound = helper.FIXTURE.fixture()[4]; stage = root / '.sync/SYNTHETIC_N08'; stage.mkdir(parents=True)
    (root / 'outputs').mkdir(); (root / 'runtime').mkdir()
    config.update(forecast_complete_GPUh=2. if limit < 12 else 13., billed_limit_GPUh=limit)
    write(stage / CONFIG, config)
    runner = 'scripts/run_wc_paper_N08_balanced_full40_r1.py'
    (stage / runner).parent.mkdir(); (stage / runner).write_text('# SYNTHETIC NEVER EXECUTED\n')
    registration = value['registration']; registration['payload_sha256'] = {CONFIG: sha(stage / CONFIG), runner: sha(stage / runner)}
    # The real admission proof still checks all99 source identities; these
    # explicit tiny placeholder files stand in for source bytes, not kernels.
    numeric = {}
    for i in range(99):
        name = 'src/SYNTHETIC_NUMERIC_' + str(i) + '.py'; path = stage / name
        path.parent.mkdir(exist_ok=True); path.write_text('# SYNTHETIC NUMERIC PLACEHOLDER\n'); numeric[name] = sha(path)
    registration['payload_sha256'].update(numeric); write(stage / 'registration.json', registration)
    proof = files['proof']['data']; proof.update(registration_sha256=sha(stage / 'registration.json'),
        config_sha256=sha(stage / CONFIG), runner_source_sha256=sha(stage / runner))
    proof['unchanged_numeric_CPU_reuse']['source_sha256'] = numeric
    write(stage / CPU_RESULT, proof); write(stage / 'N08-CPU-bundle-result.json', helper.bundle(registration['source_revision']))
    write(stage / 'N08-CPU-launch.json', dict(source_revision=registration['source_revision'], identity=dict(pid=9999, start_ticks=99990)))
    authority = dict(source_revision=registration['source_revision'], config_sha256=sha(stage / CONFIG),
        production_CPU_sha256=sha(stage / CPU_RESULT), bound_timing_fingerprint=fingerprint(bound), bound_input_fingerprint=fingerprint(bound),
        scope_counts=config['scope_counts'], whole_card_run=RUN, gpu_uuid='GPU-SYNTHETIC-N08',
        forecast_complete_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=limit,
        cumulative_cap_GPUh=config['cumulative_cap_GPUh'], budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
        direct_user_authorization=True, user_reply_quote='SYNTHETIC_TEST_ONLY_NOT_HUMAN_APPROVAL', launch_id='SYNTHETIC_N08',
        kind='STANDING_STRICT_UNDER12' if limit < 12 else 'SPECIFIC_WHOLE_CARD_APPROVAL')
    write(stage / 'N08-launch-authorization.json', authority)
    pool = ApprovedCardBudgetPool(root)
    legacy = dict(job_id='SYNTHETIC_LEGACY', kind='LEGACY_W3', status='RESERVED_OR_RUNNING', billed_limit_GPUh=12,
        source_revision='SYNTHETIC_OLD', launch_id='SYNTHETIC_OLD', gpu_uuid='GPU-SYNTHETIC-OLD',
        supervisor_pid=1, supervisor_start_ticks=10, stage='SYNTHETIC_OLD')
    pool.initialize(cap=config['cumulative_cap_GPUh'], origin_used=config['budget_origin_used_GPUh'], origin_jobs=1,
        authorization=dict(direct_user_authorization=True, cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
                           autonomy_exclusive_upper_GPUh=12, user_reply_quote='SYNTHETIC_TEST_ONLY'), legacy_job=legacy)
    pool.settle(legacy['job_id'], .05, 'a' * 64)
    return config, bound, stage, registration, authority, pool


def run_supervisor(root, values, *, fail_mkdir=False):
    config, bound, stage, registration, authority, pool = values
    module = load(ROOT / 'scripts/supervise_wc_paper_N08_balanced_full40_r1.py')
    args = ['SYNTHETIC', '--project', str(root), '--stage', str(stage), '--authorization',
        str(stage / 'N08-launch-authorization.json'), '--source-revision', registration['source_revision'],
        '--gpu-uuid', authority['gpu_uuid']]
    child = SimpleNamespace(pid=54321, poll=lambda: 0, wait=lambda **kw: 0)
    def process(pid): return dict(pid=pid, start_ticks=None if pid == 9999 else pid * 10,
                                  state=None if pid == 9999 else 'R', command='SYNTHETIC')
    gpu = dict(uuid=authority['gpu_uuid'], name='NVIDIA RTX A6000', memory_used_mib=0, compute_cap='8.6', pids=[])
    original_mkdir = Path.mkdir
    def mkdir(path, *a, **kw):
        if fail_mkdir and path == root / 'outputs' / RUN: raise OSError('SYNTHETIC_OUTPUT_MKDIR_FAILURE')
        return original_mkdir(path, *a, **kw)
    with patch.object(sys, 'argv', args), patch.object(sys, 'path', list(sys.path)), \
            patch('wcomr.balanced_repeat_production_r1.validate', return_value=(config, registration, None, None, None, None, bound, None)), \
            patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process), \
            patch.object(module, 'observe', return_value=gpu), patch.object(module.signal, 'signal'), \
            patch.object(module.subprocess, 'Popen', return_value=child) as spawned, patch.object(Path, 'mkdir', mkdir):
        module.main()
    return spawned


class SupervisionControls(unittest.TestCase):
    def test_original_under12_whole_reserve_settle_once_and_UUID_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); values = fixture(root); before = values[-1].read()
            spawned = run_supervisor(root, values)
            self.assertEqual(spawned.call_count, 1)
            self.assertIn('run_wc_paper_N08_balanced_full40_r1.py', spawned.call_args.args[0][2])
            bill_path = root / 'outputs' / RUN / 'billing.json'; bill = json.loads(bill_path.read_text())
            after = values[-1].read(); job = after['jobs'][RUN]
            self.assertEqual(job['status'], 'SETTLED'); self.assertEqual(after['reserved_gpu_hours'], 0)
            self.assertAlmostEqual(after['used_gpu_hours'] - before['used_gpu_hours'], bill['actual_GPUh'])
            self.assertEqual(job['scope_counts']['total_paths'], 40)
            self.assertEqual(job['bound_input_fingerprint'], job['bound_timing_fingerprint'])
            self.assertEqual(values[-1].settle(RUN, bill['actual_GPUh'], sha(bill_path)), after)
            with DeviceLease(root, values[4]['gpu_uuid']): pass

    def test_specific_large_card_uses_generic_alias_and_actual_original_pool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); values = fixture(root, limit=14.)
            run_supervisor(root, values)
            job = values[-1].read()['jobs'][RUN]
            self.assertEqual(job['kind'], 'V2_SPECIFIC_WHOLE_CARD_APPROVAL')
            self.assertEqual(job['billed_limit_GPUh'], 14.)
            self.assertEqual(job['authorization_sha256'], sha(values[2] / 'N08-launch-authorization.json'))

    def test_output_mkdir_failure_still_settles_original_bill_and_releases_UUID(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); values = fixture(root)
            with self.assertRaisesRegex(OSError, 'SYNTHETIC_OUTPUT'): run_supervisor(root, values, fail_mkdir=True)
            bill = json.loads((values[2] / 'N08-billing-fallback.json').read_text())
            self.assertFalse(bill['original_output_root_available'])
            self.assertEqual(values[-1].read()['jobs'][RUN]['status'], 'SETTLED')
            self.assertTrue((values[2] / 'N08-supervisor-fallback.json').exists())
            with DeviceLease(root, values[4]['gpu_uuid']): pass

    def test_other_registered_job_refuses_clean_start_without_stopping_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); values = fixture(root); pool = values[-1]
            job = dict(job_id='SYNTHETIC_OTHER_ACTIVE', forecast_GPUh=.5, billed_limit_GPUh=1., gpu_uuid='GPU-SYNTHETIC-OTHER',
                       source_revision='SYNTHETIC', config_sha256='a' * 64, launch_id='SYNTHETIC_OTHER')
            pool.reserve(job, dict(uuid=job['gpu_uuid'], name='NVIDIA RTX A6000', compute_cap='8.6', memory_used_mib=0, pids=[]))
            with self.assertRaisesRegex(ValueError, 'Another registered GPU'): run_supervisor(root, values)
            after = pool.read(); self.assertNotIn(RUN, after['jobs'])
            self.assertEqual(after['jobs'][job['job_id']]['status'], 'RESERVED_OR_RUNNING')

    def test_child_exit_race_does_not_abort_the_final_settlement_path(self):
        module = load(ROOT / 'scripts/supervise_wc_paper_N08_balanced_full40_r1.py')
        child = SimpleNamespace(pid=54321, poll=lambda: None, wait=Mock(return_value=0))
        with patch.object(module.os, 'killpg', side_effect=ProcessLookupError) as kill:
            module.stop(child)
        self.assertEqual(kill.call_count, 1); child.wait.assert_called_once()


if __name__ == '__main__': unittest.main()
