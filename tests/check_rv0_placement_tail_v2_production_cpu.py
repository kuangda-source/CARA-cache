"""Production scope, budget, retained raw provenance and scoring contracts, no Torch."""
import argparse
import ast
import copy
import gzip
import importlib.util
import json
from pathlib import Path

from wcomr.rv0_placement_v2_execution import (
    APPROVAL, COUNTS, validate_config, admission_budget, reserve_budget, settle_budget, audit_settlement)
from wcomr.rv0_placement_v2_evaluation import audit_trajectories


def run(config, raw, budget):
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root/'scripts/run_wc_w3_placement_tail_v2.py').read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'validate')
    call = next(n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'validate_stage')
    keyword = next(k for k in call.keywords if k.arg == 'selected')
    assert ast.dump(keyword.value) == ast.dump(ast.parse("config['GPU_execution_selected']", mode='eval').body)
    refused = []
    def reject(name, action):
        try: action()
        except (ValueError, KeyError, AssertionError, TypeError): refused.append(name)
        else: raise AssertionError('Invalid placement contract accepted: '+name)
    validate_config(config)
    reject('draft_cannot_admit_GPU', lambda: admission_budget(budget, config))
    # In-memory synthetic approval only; never writes a real permission file or ledger.
    selected = copy.deepcopy(config)
    selected.update(GPU_execution_selected=True, gpu_uuid='GPU-CPU-CONTRACT-NOT-A-DEVICE',
        production_cpu_receipt_sha256='c'*64, production_cpu_stage='.sync/CPU_SYNTHETIC_PROOF_ONLY',
        production_cpu_payload_sha256={**config['payload_sha256'], 'placement-config.json': 'd'*64})
    selected['payload_sha256'][APPROVAL] = 'a'*64
    selected['execution_scope_authority'] = {'approval_ref': APPROVAL, 'approval_sha256': 'a'*64,
        'approved_card': config['card'], 'run_id': config['run_id'],
        'allow_single_job_above_2_gpu_hours': True, 'legacy_seconds_caps_revoked': True,
        'planning_proxy_seconds': config['cost']['complete_planning_proxy_seconds'],
        'science_counts': COUNTS, 'usage_reset': False,
        'source_user_text': 'CPU_SYNTHETIC_CONTRACT_NOT_HUMAN_AUTHORIZATION'}
    validate_config(selected, selected=True)
    mutations = [
        ('consumed_R1_exception', lambda c: c['execution_scope_authority'].update(approval_ref='manifests/wc_w3_placement_gt2h_authorization_20261007.json')),
        ('old_tail_proposal_constraint', lambda c: c['scope'].update(protected_native_action_mismatch='INFEASIBLE_STOP_PRESERVE_DENOMINATOR_NO_FALLBACK')),
        ('changed_R2_executed_core', lambda c: c['payload_sha256'].update({'src/wcomr/rv0_fixed_mask_v2.py':'b'*64})),
        ('old_A_scope', lambda c: c['execution_scope_authority'].update(approved_card='WC-W3-SMALL-CD-R1-20261004-A')),
        ('old_Human_cap', lambda c: c['execution_scope_authority'].update(single_run_inclusive_cap_seconds=4500)),
        ('shrunk_approval_counts', lambda c: c['execution_scope_authority'].update(science_counts=[1, 8, 5, 2])),
        ('approval_digest_changed', lambda c: c['execution_scope_authority'].update(approval_sha256='b'*64)),
        ('usage_reset', lambda c: c['execution_scope_authority'].update(usage_reset=True)),
        ('missing_actual_production_CPU_proof', lambda c: c.pop('production_cpu_receipt_sha256')),
        ('missing_production_source', lambda c: c['payload_sha256'].pop('scripts/run_wc_w3_placement_tail_v2.py')),
        ('changed_actual_core', lambda c: c['payload_sha256'].update({'src/wcomr/rv0_placement_causal.py': 'b'*64})),
        ('shrunk_suffixes', lambda c: c['scope'].update(complete_suffix_controls=12)),
        ('changed_pair', lambda c: c['scope']['scenes'][0]['swaps'][0].update(calls=[45, 49])),
        ('wrong_sample_alias', lambda c: c.update(sample_names=['human_199'])),
        ('cap_change', lambda c: c['execution_limits'].update(timeout_seconds=9900)),
        ('missing_scoring_module', lambda c: c['payload_sha256'].pop('src/wcomr/rv0_placement_scores.py'))]
    for name, change in mutations:
        broken = copy.deepcopy(selected); change(broken)
        reject(name, lambda: validate_config(broken, selected=True))
    for name, change in [('insufficient_complete_budget', {'used_gpu_hours': 23.5}),
                         ('inflight_job', {'another_inflight': {}}), ('wrong_cap', {'cap_gpu_hours': 13}),
                         ('wrong_authority', {'budget_authorization_ref': 'old.json'}),
                         ('nonfinite_usage', {'used_gpu_hours': float('nan')})]:
        broken = {**budget, **change}; reject(name, lambda: admission_budget(broken, selected))
    prepaid = reserve_budget(budget, selected, 1101)
    assert prepaid['used_gpu_hours'] == 24
    settled = settle_budget(prepaid, budget, selected, 600., 1101)
    assert settled['used_gpu_hours'] == budget['used_gpu_hours']+600/3600
    assert settled['gpu_jobs_launched'] == budget['gpu_jobs_launched']+1
    assert not any(k.endswith('_inflight') for k in settled)
    # A wall beyond the former 9600s is charged, and is not itself a failure.
    assert settle_budget(prepaid, budget, selected, 9601., 1101)['used_gpu_hours'] == budget['used_gpu_hours']+9601/3600
    for wall in [0, -1, float('inf'), float('nan')]:
        reject('invalid_wall_'+str(wall), lambda: settle_budget(prepaid, budget, selected, wall, 1101))
    broken = {**prepaid, 'gpu_jobs_launched': prepaid['gpu_jobs_launched']+1}
    reject('concurrent_ledger_change', lambda: settle_budget(broken, budget, selected, 600., 1101))
    source = 'a'*40
    supervisor = {'status': 'EXITED_REQUIRES_RESULT_AUDIT', 'exit_code': 0, 'source_revision': source,
        'run_id': selected['run_id'], 'config': selected, 'reserved_seconds': (24-budget['used_gpu_hours'])*3600,
        'cumulative_budget_exceeded': False, 'wall_seconds': 600., 'planned_parent_phases': 2,
        'planned_suffix_controls': 16, 'planned_encoded_outputs': 10, 'pid': 1101, 'child_pid': 1102,
        'budget_before': budget, 'budget_after': settled}
    runner = {'source_revision': source, 'pid': 1102}
    assert audit_settlement(supervisor, runner, selected, settled, source) == [1101, 1102]
    for name, change in [('shrunk_terminal_scope', {'planned_suffix_controls': 12}),
                         ('old_cap', {'reserved_seconds': 4500}), ('same_PID', {'child_pid': 1101}),
                         ('different_actual_wall', {'wall_seconds': 9601.}), ('failed_card', {'exit_code': 124})]:
        broken = {**supervisor, **change}
        reject(name, lambda: audit_settlement(broken, runner, selected, settled, source))
    success = [c for c in raw['checks'] if c['failure'] in (None,'tail_proposal_difference')]
    assert len(success) == 3
    audits = [audit_trajectories(c['receipt'], c['fixture_config'], 3) for c in success]
    assert sum(a['parents'] for a in audits) == 6 and sum(a['complete_suffixes'] for a in audits) == 48
    for name, change in [
        ('missing_parent', lambda r: r['requests'].pop()),
        ('incomplete_repeat', lambda r: r['requests'][0]['children'].pop()),
        ('future_truth_leak', lambda r: r['requests'][0]['children'][3]['record']['action_report']['suffix_events'][1].update(current_deep_truth_used=True)),
        ('failed_restore', lambda r: r['requests'][0]['children'][3]['record'].update(parent_restored=False)),
        ('repeat_changed', lambda r: r['requests'][0]['children'][6]['outputs'].__setitem__(0, 'f'*64)),
        ('quota_changed', lambda r: r['requests'][0]['children'][3]['record']['action_report'].update(per_CFG_full_counts=[1, 1])),
        ('truncated_encoding', lambda r: r['requests'][0]['decoded_children'][1]['pipeline'].pop())]:
        damaged = copy.deepcopy(success[0]['receipt']); change(damaged)
        reject(name, lambda: audit_trajectories(damaged, success[0]['fixture_config'], 3))
    scores = {'status':'UNCHANGED_SIGNED_SCORE_CODE_AND_PRIOR_PROOF_REUSED_NOT_RERUN'}
    return {'status': 'PLACEMENT_PRODUCTION_RAW_PROVENANCE_BUDGET_AND_SIGNED_SCORE_CPU_PASS_NOT_GPU',
        'refusals': refused, 'retained_actual_CPU_parents': 6, 'retained_actual_CPU_suffixes': 48,
        'mock_outputs': 30, 'production_scope': COUNTS, 'signed_scores': scores,
        'actual_GPU_settlement_or_video_score': False, 'GPU_submissions': 0, 'ledger_written': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['config', 'raw-receipt', 'budget']: parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    raw=json.loads(gzip.decompress(args.raw_receipt.read_bytes()))
    if type(raw) is list:raw={'checks':raw}
    print(json.dumps(run(json.loads(args.config.read_text()), raw,
                         json.loads(args.budget.read_text())), allow_nan=False))
