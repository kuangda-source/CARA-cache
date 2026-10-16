"""Real temporary v2 pools/UUID locks; all GPU telemetry and children are fake."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from test_runtime_profile40_production_r1 import fixture as contract_fixture
from wcomr.runtime_profile40_production_r1 import CONFIG, RUN, CPU_RESULT, CPU_STATUS, COUNTS
from wcomr.frozen_shared_production_r1 import fingerprint, sha, write
from wcomr.gpu_budget_approved_card_v2 import ApprovedCardBudgetPool
from wcomr.gpu_budget_pool_v2 import DeviceLease
from wcomr.runtime_profile40_post_r1 import GPU_TERMINAL_STATUS

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location('synthetic_' + name, ROOT / 'scripts' / (name + '.py'))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def fixture(root, *, limit=4.5):
    config, _, _, _, _, bound = contract_fixture()
    config['billed_limit_GPUh'] = limit
    stage = root / '.sync/SYNTHETIC_N09'; stage.mkdir(parents=True)
    (root / 'outputs').mkdir(); (root / 'runtime').mkdir()
    write(stage / CONFIG, config)
    worker = stage / 'scripts/run_wc_paper_N09_runtime_profile40_r1.py'
    worker.parent.mkdir(); worker.write_text('# EXPLICIT_SYNTHETIC_NEVER_EXECUTED\n')
    registration = dict(source_revision='1' * 40,
        payload_sha256={CONFIG: sha(stage / CONFIG), str(worker.relative_to(stage)): sha(worker)})
    write(stage / 'registration.json', registration)
    proof = dict(status=CPU_STATUS, exit_code=0, source_revision=registration['source_revision'],
        registration_sha256=sha(stage / 'registration.json'), config_sha256=sha(stage / CONFIG),
        runner_source_sha256=sha(worker), bound_profile_fingerprint=fingerprint(bound), scope_counts=COUNTS,
        CUDA_initialized=False, GPU_submissions=0, model_weights_loaded=0, ledger_written=False,
        actual_sample_argument_variants=10, matrix=bound['execution_plan'],
        guardrail_checks=[dict(scene=r['name'], unguarded_execution_refused=True) for r in bound['requests']])
    write(stage / CPU_RESULT, proof)
    cpu = dict(source_revision=registration['source_revision'], registration_sha256=sha(stage / 'registration.json'),
               identity=dict(pid=9999, start_ticks=99990))
    write(stage / 'N09-production-CPU-launch.json', cpu)
    write(stage / 'N09-production-CPU-exit.json', dict(cpu, exit_code=0))
    authority = dict(source_revision=registration['source_revision'], launch_id='SYNTHETIC_N09_NOT_REAL_APPROVAL',
        config_sha256=sha(stage / CONFIG), production_CPU_sha256=sha(stage / CPU_RESULT),
        bound_input_fingerprint=fingerprint(bound), scope_counts=COUNTS, whole_card_run=RUN,
        gpu_uuid='GPU-SYNTHETIC-N09', forecast_complete_GPUh=config['forecast_complete_GPUh'],
        billed_limit_GPUh=limit, cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
        budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
        direct_user_authorization=True, user_reply_quote='SYNTHETIC_ONLY_NOT_HUMAN_APPROVAL',
        kind='STANDING_STRICT_UNDER12' if limit < 12 else 'SPECIFIC_WHOLE_CARD_APPROVAL')
    write(stage / 'N09-launch-authorization.json', authority)
    pool = ApprovedCardBudgetPool(root)
    legacy = dict(job_id='SYNTHETIC_LEGACY', kind='LEGACY_W3', status='RESERVED_OR_RUNNING',
        billed_limit_GPUh=12., source_revision='SYNTHETIC_OLD', launch_id='SYNTHETIC_OLD',
        gpu_uuid='GPU-SYNTHETIC-OLD', supervisor_pid=1, supervisor_start_ticks=10, stage='SYNTHETIC_OLD')
    pool.initialize(cap=config['cumulative_cap_GPUh'], origin_used=config['budget_origin_used_GPUh'], origin_jobs=1,
        authorization=dict(direct_user_authorization=True, cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
            autonomy_exclusive_upper_GPUh=12, user_reply_quote='SYNTHETIC_ONLY_NOT_HUMAN_APPROVAL'), legacy_job=legacy)
    pool.settle(legacy['job_id'], .05, 'a' * 64)
    return config, bound, stage, registration, authority, pool


def process(pid):
    return dict(pid=pid, start_ticks=pid * 10, state='R', command='SYNTHETIC_NO_REAL_PROCESS')


def run_supervisor(root, values, *, fail_mkdir=False, spawn_error=None, alive_cpu=False,
                   observe_change=None, expiry=False):
    config, bound, stage, registration, authority, _ = values
    module = load_script('supervise_wc_paper_N09_runtime_profile40_r1')
    alive = [expiry]
    def wait(**kw):alive[0] = False; return 143 if expiry else 0
    child = SimpleNamespace(pid=54321, poll=lambda: None if alive[0] else (143 if expiry else 0), wait=wait)
    gpu = dict(uuid=authority['gpu_uuid'], name='NVIDIA RTX A6000', memory_used_mib=0, compute_cap='8.6', pids=[])
    if observe_change:gpu.update(observe_change)
    original_mkdir = Path.mkdir
    def mkdir(path, *a, **kw):
        if fail_mkdir and path == root / 'outputs' / RUN:raise OSError('SYNTHETIC_OUTPUT_MKDIR_FAILURE')
        return original_mkdir(path, *a, **kw)
    from contextlib import ExitStack
    with ExitStack() as stack:
        stack.enter_context(patch('wcomr.runtime_profile40_production_r1.validate',
            return_value=(config, registration, None, None, None, None, bound, None)))
        stack.enter_context(patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process))
        stack.enter_context(patch('wcomr.gpu_budget_pool_v2.same_live_process', return_value=alive_cpu))
        stack.enter_context(patch.object(module, 'observe', return_value=gpu))
        stack.enter_context(patch.object(module.signal, 'signal'))
        stack.enter_context(patch.object(Path, 'mkdir', mkdir))
        spawned = stack.enter_context(patch.object(module.subprocess, 'Popen', return_value=child, side_effect=spawn_error))
        killed = stack.enter_context(patch.object(module.os, 'killpg'))
        if expiry:
            boundary = 100 + config['billed_limit_GPUh'] * 3600 - 29
            stack.enter_context(patch.object(module.time, 'monotonic', side_effect=[100., boundary, boundary + .1]))
        state = module.run(root, stage, registration['source_revision'], authority['gpu_uuid'])
    return state, spawned, killed


class RuntimeProfile40SupervisionControls(unittest.TestCase):
    def test_complete40_single_child_additive_actual_bill_and_own_UUID_release(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root); before = values[-1].read()
            state, spawned, killed = run_supervisor(root, values)
            self.assertEqual(spawned.call_count, 1); killed.assert_not_called()
            self.assertEqual(state['status'], GPU_TERMINAL_STATUS)
            command = spawned.call_args.args[0]
            self.assertTrue(command[2].endswith('run_wc_paper_N09_runtime_profile40_r1.py'))
            self.assertEqual(spawned.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'], values[4]['gpu_uuid'])
            self.assertTrue(spawned.call_args.kwargs['start_new_session'])
            self.assertEqual(len(spawned.call_args.kwargs['pass_fds']), 1)
            billpath = root / 'outputs' / RUN / 'billing.json'; bill = json.loads(billpath.read_text())
            after = values[-1].read(); own = after['jobs'][RUN]
            self.assertEqual(own['scope_counts'], COUNTS)
            self.assertEqual(own['bound_profile_fingerprint'], fingerprint(values[1]))
            self.assertEqual(after['reserved_gpu_hours'], 0)
            self.assertAlmostEqual(after['used_gpu_hours'] - before['used_gpu_hours'], bill['actual_GPUh'])
            self.assertEqual(values[-1].settle(RUN, bill['actual_GPUh'], sha(billpath)), after)
            self.assertFalse(state['clean_repeated_latency_claim'])
            with DeviceLease(root, values[4]['gpu_uuid']):pass
            with self.assertRaises(FileExistsError):run_supervisor(root, values)

    def test_spawn_and_output_failures_still_bill_original_whole_wall_once(self):
        for mode in ('spawn', 'output'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                root = Path(folder); values = fixture(root)
                with self.assertRaises(OSError):
                    run_supervisor(root, values, fail_mkdir=mode == 'output',
                        spawn_error=OSError('SYNTHETIC_SPAWN_FAILURE') if mode == 'spawn' else None)
                path = (values[2] / 'N09-billing-fallback.json' if mode == 'output'
                        else root / 'outputs' / RUN / 'billing.json')
                self.assertTrue(path.is_file())
                self.assertEqual(values[-1].read()['jobs'][RUN]['status'], 'SETTLED')
                with DeviceLease(root, values[4]['gpu_uuid']):pass

    def test_same_card_at_exact12_needs_specific_whole_card_authority(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root, limit=12.)
            path = values[2] / 'N09-launch-authorization.json'
            authority = dict(values[4], kind='STANDING_STRICT_UNDER12'); write(path, authority)
            with self.assertRaises(ValueError):run_supervisor(root, values)
            self.assertNotIn(RUN, values[-1].read()['jobs'])
            write(path, values[4]); state, spawned, _ = run_supervisor(root, values)
            self.assertEqual(spawned.call_count, 1)
            self.assertEqual(values[-1].read()['jobs'][RUN]['kind'], 'V2_SPECIFIC_WHOLE_CARD_APPROVAL')

    def test_other_job_is_preserved_and_prevents_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root); pool = values[-1]
            job = dict(job_id='SYNTHETIC_OTHER_ACTIVE', forecast_GPUh=.5, billed_limit_GPUh=1.,
                gpu_uuid='GPU-SYNTHETIC-OTHER', source_revision='SYNTHETIC', config_sha256='a' * 64,
                launch_id='SYNTHETIC_OTHER')
            pool.reserve(job, dict(uuid=job['gpu_uuid'], name='NVIDIA RTX A6000',
                memory_used_mib=0, compute_cap='8.6', pids=[]))
            with self.assertRaisesRegex(ValueError, 'Another registered GPU'):run_supervisor(root, values)
            after = pool.read()
            self.assertNotIn(RUN, after['jobs'])
            self.assertEqual(after['jobs'][job['job_id']]['status'], 'RESERVED_OR_RUNNING')

    def test_actual_CPU_process_or_failed_exit_refuses_GPU(self):
        for mode in ('alive', 'failed_exit'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                root = Path(folder); values = fixture(root)
                if mode == 'failed_exit':
                    path = values[2] / 'N09-production-CPU-exit.json'; data = json.loads(path.read_text())
                    data['exit_code'] = 1; write(path, data)
                with self.assertRaisesRegex(ValueError, 'production CPU'):
                    run_supervisor(root, values, alive_cpu=mode == 'alive')
                self.assertNotIn(RUN, values[-1].read()['jobs'])

    def test_foreign_occupied_UUID_and_actual_balance_refuse_without_child(self):
        for mode in ('occupied', 'wrong_uuid', 'balance'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                root = Path(folder); values = fixture(root)
                if mode == 'balance':
                    pool = values[-1]
                    with pool.transaction() as value:
                        # Explicit synthetic historical cost, preserving the original origin/cap.
                        job = value['jobs']['SYNTHETIC_LEGACY']; job['actual_GPUh'] = 31.
                        pool.commit(value, dict(type='SYNTHETIC_HISTORICAL_COST_FIXTURE'))
                change = dict(pids=[777]) if mode == 'occupied' else dict(uuid='GPU-FOREIGN') if mode == 'wrong_uuid' else None
                with self.assertRaises(ValueError):run_supervisor(root, values, observe_change=change)
                self.assertNotIn(RUN, values[-1].read()['jobs'])
                with DeviceLease(root, values[4]['gpu_uuid']):pass

    def test_whole_billed_limit_stops_only_own_child_and_still_settles(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = fixture(root)
            state, spawned, killed = run_supervisor(root, values, expiry=True)
            self.assertTrue(state['own_billed_limit_stop']); self.assertEqual(state['child_exit_code'], 143)
            self.assertEqual(killed.call_count, 1); self.assertEqual(killed.call_args.args[0], 54321)
            self.assertEqual(values[-1].read()['jobs'][RUN]['status'], 'SETTLED')
            self.assertLess(state['actual_GPUh'], values[0]['billed_limit_GPUh'])

    def test_child_exit_race_preserves_settlement_stop_boundary(self):
        module = load_script('supervise_wc_paper_N09_runtime_profile40_r1')
        child = SimpleNamespace(pid=54321, poll=lambda:None, wait=Mock(return_value=0))
        with patch.object(module.os, 'killpg', side_effect=ProcessLookupError) as killed:
            module.stop(child)
        self.assertEqual(killed.call_count, 1); child.wait.assert_called_once()


if __name__ == '__main__':unittest.main()
