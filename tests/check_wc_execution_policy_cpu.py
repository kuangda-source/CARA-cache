"""Affected autonomy, expense and direct-supervision checks; no GPU or model execution."""
import argparse
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from wcomr.rv0_placement_execution import (
    APPROVAL, COUNTS, INFLIGHT, validate_config, admission_budget, reserve_budget,
    settle_budget, audit_settlement)


def selected_config(config, exception=True):
    c = copy.deepcopy(config)
    c.update(GPU_execution_selected=True, gpu_uuid='GPU-CPU-TEST-NOT-A-DEVICE',
        production_cpu_receipt_sha256='c'*64, production_cpu_stage='.sync/CPU_ONLY_SYNTHETIC',
        production_cpu_payload_sha256={**config['payload_sha256'], 'placement-config.json': 'd'*64})
    if exception:
        c['payload_sha256'][APPROVAL] = 'a'*64
        c['execution_scope_authority'] = {'approval_ref': APPROVAL, 'approval_sha256': 'a'*64,
            'approved_card': config['card'], 'run_id': config['run_id'],
            'allow_single_job_above_2_gpu_hours': True, 'legacy_seconds_caps_revoked': True,
            'planning_proxy_seconds': c['cost']['complete_planning_proxy_seconds'],
            'science_counts': COUNTS, 'usage_reset': False,
            'source_user_text': 'SYNTHETIC_CPU_TEST_NOT_REAL_HUMAN_APPROVAL'}
    return c


def run(config, budget):
    refused = []
    def reject(name, action):
        try: action()
        except (ValueError, KeyError, TypeError): refused.append(name)
        else: raise AssertionError('Unexpected acceptance: '+name)
    c = selected_config(config)
    validate_config(c, selected=True)
    reject('complete_B_above_2h_without_exception', lambda: admission_budget(budget, selected_config(config, False)))
    # Threshold boundary tests are synthetic finance inputs, not alternative B designs.
    for forecast in [7199., 7200.]:
        small = selected_config(config, False)
        small['cost']['complete_nominal_proxy_seconds'] = forecast-1
        small['cost']['complete_planning_proxy_seconds'] = forecast
        assert admission_budget(budget, small)['fits']
    above = selected_config(config, False)
    above['cost']['complete_nominal_proxy_seconds'] = 7200.
    above['cost']['complete_planning_proxy_seconds'] = 7200.001
    reject('strictly_above_2h', lambda: admission_budget(budget, above))
    broken = copy.deepcopy(c); broken['execution_limits']['timeout_seconds'] = 9600
    reject('legacy_GPU_deadline_reintroduced', lambda: validate_config(broken, selected=True))
    broken = copy.deepcopy(c); broken['execution_policy_authority']['automatic_single_job_gpu_hours'] = 3
    reject('unapproved_automatic_limit', lambda: validate_config(broken, selected=True))
    reject('budget_insufficient', lambda: admission_budget({**budget, 'used_gpu_hours': 23.}, c))
    paid = reserve_budget(budget, c, 1101)
    assert paid['used_gpu_hours'] == 24 and paid[INFLIGHT]['reserved_seconds'] == (24-budget['used_gpu_hours'])*3600
    # Above the removed 9600s cap can now be a valid complete terminal result.
    after = settle_budget(paid, budget, c, 10000., 1101)
    supervisor = {'status': 'EXITED_REQUIRES_RESULT_AUDIT', 'exit_code': 0,
        'source_revision': 'a'*40, 'run_id': c['run_id'], 'config': c,
        'reserved_seconds': paid[INFLIGHT]['reserved_seconds'], 'cumulative_budget_exceeded': False,
        'wall_seconds': 10000., 'planned_parent_phases': 2, 'planned_suffix_controls': 16,
        'planned_encoded_outputs': 10, 'budget_before': budget, 'budget_after': after,
        'pid': 1101, 'child_pid': 1102}
    assert audit_settlement(supervisor, {'source_revision': 'a'*40, 'pid': 1102}, c, after, 'a'*40) == [1101, 1102]
    # Failure or unexpected cumulative overrun is always charged, never hidden or truncated.
    overrun = paid[INFLIGHT]['reserved_seconds']+1
    assert settle_budget(paid, budget, c, overrun, 1101)['used_gpu_hours'] > 24
    reject('concurrent_ledger_not_overwritten', lambda: settle_budget({**paid, 'gpu_jobs_launched': 999}, budget, c, 10., 1101))
    stage = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('policy_supervisor_cpu_only', stage/'scripts/supervise_wc_w3_placement.py')
    sup = importlib.util.module_from_spec(spec); spec.loader.exec_module(sup)
    tree = ast.parse((stage/'scripts/supervise_wc_w3_placement.py').read_text())
    assert not any(isinstance(n, ast.Constant) and n.value == 'timeout' for n in ast.walk(tree))
    real_popen = subprocess.Popen
    scenarios = []
    # CPU children exercise real wait/kill/reap/expense paths in disposable fake projects.
    for scenario in ['complete', 'spawn_failure', 'foreign_GPU', 'cumulative_guard', 'automatic_2h_guard']:
        with tempfile.TemporaryDirectory(prefix='wc-policy-cpu-', dir=stage) as directory:
            root = Path(directory)
            for name in ['.sync', 'reports', 'runtime']: (root/name).mkdir()
            selected = selected_config(config)
            fixture_budget = copy.deepcopy(budget)
            if scenario == 'cumulative_guard':
                # Only the admission planning predicate is mocked for a 30s remaining fake budget.
                fixture_budget['used_gpu_hours'] = 24-30/3600
            if scenario == 'automatic_2h_guard':
                selected = selected_config(config, False)
                selected['cost']['complete_nominal_proxy_seconds'] = 1.
                selected['cost']['complete_planning_proxy_seconds'] = 2.
            (root/'reports/budget.json').write_text(json.dumps(fixture_budget))
            (root/'placement-config.json').write_text(json.dumps(selected))
            args = SimpleNamespace(project=root, stage=root, output=root/'outputs'/config['run_id'],
                gpu_uuid=selected['gpu_uuid'], source_revision='b'*40)
            queries = [0]
            def query(command, **kwargs):
                if '--query-gpu=uuid,name,memory.used,compute_cap' in command:
                    return args.gpu_uuid+', NVIDIA RTX A6000, 0, 8.6\n'
                queries[0] += 1
                return args.gpu_uuid+', '+str(os.getpid())+'\n' if scenario == 'foreign_GPU' and queries[0] > 2 else ''
            def launch(command, **kwargs):
                assert 'timeout' not in command and kwargs['start_new_session'] and len(kwargs['pass_fds']) == 1
                assert kwargs['env']['WC_SUPERVISOR_PID'] == str(os.getpid())
                if scenario == 'spawn_failure': raise OSError('CPU_SIMULATED_SPAWN_FAILURE')
                delay = .01 if scenario == 'complete' else 5
                return real_popen([sys.executable, '-c', 'import time; time.sleep('+str(delay)+')'], **kwargs)
            original_monotonic = sup.time.monotonic
            times = [0]
            def fake_elapsed():
                times[0] += 1
                return 0. if times[0] == 1 else 7171.
            original_signal = signal.getsignal(signal.SIGTERM)
            try:
                with patch.object(sup.argparse.ArgumentParser, 'parse_args', return_value=args), \
                     patch.object(sup.subprocess, 'check_output', side_effect=query), \
                     patch.object(sup.subprocess, 'run', return_value=SimpleNamespace(returncode=0)), \
                     patch.object(sup.subprocess, 'Popen', side_effect=launch), \
                     patch('wcomr.rv0_placement_execution.admission_budget', return_value={'fits': True}) if scenario == 'cumulative_guard' else patch.object(sup, 'CPU_TEST_SENTINEL', True, create=True):
                    if scenario == 'automatic_2h_guard':
                        with patch.object(sup.time, 'monotonic', side_effect=fake_elapsed): sup.main()
                    else: sup.main()
            finally:
                signal.signal(signal.SIGTERM, original_signal)
                assert sup.time.monotonic is original_monotonic
            receipt = json.loads((args.output/'supervisor.json').read_text())
            settled = json.loads((root/'reports/budget.json').read_text())
            assert abs(settled['used_gpu_hours']-fixture_budget['used_gpu_hours']-receipt['wall_seconds']/3600) < 1e-12
            assert settled['gpu_jobs_launched'] == fixture_budget['gpu_jobs_launched']+1
            assert not any(k.endswith('_inflight') for k in settled)
            expected = {'complete': 'EXITED_REQUIRES_RESULT_AUDIT', 'spawn_failure': 'SUPERVISOR_ERROR',
                'foreign_GPU': 'GPU_CONFLICT', 'cumulative_guard': 'CUMULATIVE_BUDGET_GUARD',
                'automatic_2h_guard': 'ABOVE_2H_REQUIRES_USER_DECISION'}
            assert receipt['status'] == expected[scenario], receipt
            if receipt['child_pid'] is not None:
                try: os.kill(receipt['child_pid'], 0)
                except ProcessLookupError: pass
                else: raise AssertionError('Own CPU child still live')
            os.kill(os.getpid(), 0)
            scenarios.append({'scenario': scenario, 'status': receipt['status'], 'own_child_reaped': True,
                'temporary_CPU_expense_settled': True, 'other_process_not_signalled': True})
    return {'status': 'WC_EXECUTION_AUTONOMY_DIRECT_SUPERVISION_CPU_PASS_NOT_GPU',
        'refusals': refused, 'real_CPU_child_scenarios': scenarios, 'complete_B_counts_unchanged': COUNTS,
        'former_9600s_no_longer_terminal_failure': True, 'threshold_boundary_checked': True,
        'root_budget_written': False, 'GPU_submissions': 0, 'CUDA_initialized': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['config', 'budget']: parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(json.loads(args.config.read_text()), json.loads(args.budget.read_text()))))
