"""Pure CPU production controls using original Human pipeline receipts."""
import argparse
import ast
import copy
import gzip
import json
from pathlib import Path
from wcomr.rv0_small_human_execution import (
    APPROVAL, validate_config, admission_budget, reserve_budget, settle_budget, audit_settlement)
from wcomr.rv0_small_human_evaluation import audit_trajectories, evaluation_plan


def run(config, raw, budget):
    # The supervisor's prepay --validate-only call must validate selected provenance.
    source = Path(__file__).resolve().parents[1]/'scripts/run_wc_w3_small_human.py'
    function = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'validate')
    calls = [n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'validate_stage']
    assert len(calls) == 1
    keyword = next(k for k in calls[0].keywords if k.arg == 'selected')
    assert ast.dump(keyword.value) == ast.dump(ast.parse("config['GPU_execution_selected']", mode='eval').body)
    refused = []
    def reject(name, action):
        try:
            action()
        except (ValueError, KeyError, AssertionError, TypeError):
            refused.append(name)
        else:
            raise AssertionError('Invalid Human production contract accepted: '+name)
    validate_config(config)
    reject('draft_cannot_admit_GPU', lambda: admission_budget(budget, config))
    # Only a virtual pure-function fixture: no approval file, ledger or launch is written.
    selected = copy.deepcopy(config)
    selected.update(GPU_execution_selected=True, gpu_uuid='GPU-CPU-CONTRACT-NOT-A-DEVICE')
    selected.update(production_cpu_receipt_sha256='c'*64, production_cpu_stage='.sync/CPU_SYNTHETIC_PROOF_ONLY',
        production_cpu_payload_sha256={**config['payload_sha256'], 'human-config.json': 'd'*64})
    selected['payload_sha256'][APPROVAL] = 'a'*64
    selected['execution_scope_authority'] = {'approval_ref': APPROVAL, 'approval_sha256': 'a'*64,
        'approved_card': config['card'], 'run_id': config['run_id'],
        'single_run_inclusive_cap_seconds': 4500, 'usage_reset': False,
        'source_user_text': 'CPU_SYNTHETIC_CONTRACT_NOT_HUMAN_AUTHORIZATION'}
    validate_config(selected, selected=True)
    for name, change in [
        ('old_card_approval', lambda c: c['execution_scope_authority'].update(approved_card='WC-W3-SMALL-CD-R1-20261004-A')),
        ('old_3900_cap', lambda c: c['execution_scope_authority'].update(single_run_inclusive_cap_seconds=3900)),
        ('approval_digest_changed', lambda c: c['execution_scope_authority'].update(approval_sha256='b'*64)),
        ('usage_reset', lambda c: c['execution_scope_authority'].update(usage_reset=True)),
        ('missing_actual_production_CPU_proof', lambda c: c.pop('production_cpu_receipt_sha256')),
        ('missing_production_source', lambda c: c['payload_sha256'].pop('scripts/run_wc_w3_small_human.py')),
        ('changed_actual_CPU_core', lambda c: c['payload_sha256'].update({'src/wcomr/rv0_small_human_causal.py': 'b'*64})),
        ('shrunk_suffix_controls', lambda c: c['scope'].update(complete_suffix_controls=2)),
        ('wrong_CFG_alias', lambda c: c.update(target_calls=[45])),
        ('extra_scene', lambda c: c['scope'].update(sample_names=['human_199', 'human_199']))]:
        broken = copy.deepcopy(selected); change(broken)
        reject(name, lambda: validate_config(broken, selected=True))
    for name, change in [('insufficient_complete_budget', {'used_gpu_hours': 23.5}),
                         ('inflight_job', {'another_inflight': {}}), ('wrong_cap', {'cap_gpu_hours': 13}),
                         ('nonfinite_usage', {'used_gpu_hours': float('nan')})]:
        broken = {**budget, **change}; reject(name, lambda: admission_budget(broken, selected))
    prepaid = reserve_budget(budget, selected, 1101)
    assert prepaid['used_gpu_hours'] == budget['used_gpu_hours']+4500/3600
    settled = settle_budget(prepaid, budget, selected, 600., 1101)
    assert settled['used_gpu_hours'] == budget['used_gpu_hours']+600/3600
    assert settled['gpu_jobs_launched'] == budget['gpu_jobs_launched']+1
    assert not any(k.endswith('_inflight') for k in settled)
    assert settle_budget(prepaid, budget, selected, 7., 1101)['used_gpu_hours'] == budget['used_gpu_hours']+7/3600
    for wall in [0, -1, float('inf'), float('nan')]:
        reject('invalid_wall_'+str(wall), lambda: settle_budget(prepaid, budget, selected, wall, 1101))
    broken = {**prepaid, 'gpu_jobs_launched': prepaid['gpu_jobs_launched']+1}
    reject('concurrent_ledger_change', lambda: settle_budget(broken, budget, selected, 600., 1101))
    source = 'a'*40
    supervisor = {'status': 'EXITED_REQUIRES_RESULT_AUDIT', 'exit_code': 0, 'source_revision': source,
        'run_id': selected['run_id'], 'config': selected, 'reserved_seconds': 4500,
        'hard_wall_cap_exceeded': False, 'wall_seconds': 600., 'planned_parent_phases': 1,
        'planned_suffix_controls': 6, 'planned_encoded_outputs': 4, 'pid': 1101, 'child_pid': 1102,
        'budget_before': budget, 'budget_after': settled}
    runner = {'source_revision': source, 'pid': 1103}
    assert audit_settlement(supervisor, runner, selected, settled, source) == [1101, 1102, 1103]
    for name, change in [('old_terminal_denominator', {'planned_parent_phases': 2}),
                         ('legacy_reserved_cap', {'reserved_seconds': 3900}),
                         ('same_PID', {'child_pid': 1101}), ('cap_exceeded', {'wall_seconds': 4501.})]:
        broken = {**supervisor, **change}
        reject(name, lambda: audit_settlement(broken, runner, selected, settled, source))
    success = [c['receipt'] for c in raw['checks'] if c['failure'] is None]
    assert len(success) == 2
    audits = [audit_trajectories(r, 2) for r in success]
    assert sum(a['parents'] for a in audits) == 2 and sum(a['complete_suffixes'] for a in audits) == 12
    for name, change in [
        ('wrong_singleton_CFG_slot', lambda r: r['requests'][0].update(slot=0)),
        ('incomplete_repeat', lambda r: r['requests'][0]['children'].pop()),
        ('second_fake_scene', lambda r: r['requests'].append(copy.deepcopy(r['requests'][0]))),
        ('wrong_target_call', lambda r: r['requests'][0].update(target_call=45)),
        ('future_truth_leak', lambda r: r['requests'][0]['children'][2]['record']['action_report']['suffix_events'][1].update(current_deep_truth_used=True)),
        ('unpaid_probe', lambda r: r['requests'][0]['children'][2]['record']['action_report']['suffix_events'][1].update(paid_probe=False)),
        ('repeat_output_changed', lambda r: r['requests'][0]['children'][5]['outputs'].__setitem__(0, 'f'*64)),
        ('failed_parent_restore', lambda r: r['requests'][0]['children'][2]['record'].update(parent_restored=False)),
        ('truncated_decoding_pipeline', lambda r: r['requests'][0]['decoded_children'][1]['pipeline'].pop())]:
        broken = copy.deepcopy(success[0]); change(broken)
        reject(name, lambda: audit_trajectories(broken, 2))
    synthetic = copy.deepcopy(success[0]); synthetic_config = copy.deepcopy(config)
    row = synthetic['requests'][0]; row['sample_name'] = 'human_199'
    row['context'] = [config['run_id']+':human_199', *config['references']['human_199']['model_and_condition_context']]
    row['historical_WC_encoded_bridge_pass'] = True
    synthetic_config['references']['human_199']['official_WC']['sha256'] = row['artifact']['sha256']
    plan = evaluation_plan(synthetic, synthetic_config, real_GPU_required=False)
    assert (len(plan['files']), len(plan['references']), len(plan['pairs']), len(plan['bridges'])) == (4, 1, 2, 1)
    assert [(p['CFG_slot'], p['target_call'], p['action']) for p in plan['pairs']] == [(1, 46, 'C'), (1, 46, 'D')]
    reject('Toy_is_not_GPU_video', lambda: evaluation_plan(synthetic, synthetic_config))
    broken = copy.deepcopy(synthetic); broken['requests'][0]['historical_WC_encoded_bridge_pass'] = False
    reject('missing_actual_historical_bridge', lambda: evaluation_plan(broken, synthetic_config, real_GPU_required=False))
    broken = copy.deepcopy(synthetic); broken['requests'][0]['slot'] = 0
    reject('scorer_wrong_CFG_zero', lambda: evaluation_plan(broken, synthetic_config, real_GPU_required=False))
    broken = copy.deepcopy(synthetic)
    broken['requests'][0]['decoded_children'][1]['artifact']['path'] = row['artifact']['path']
    reject('duplicate_video_path', lambda: evaluation_plan(broken, synthetic_config, real_GPU_required=False))
    return {'status': 'HUMAN_PRODUCTION_PURE_CPU_ORIGINAL_RAW_CONTRACTS_PASS_NOT_GPU',
        'refusal_count': len(refused), 'refusals': refused,
        'complete_raw_CPU_parents': 2, 'complete_raw_CPU_suffixes': 12,
        'evaluation_shape': {'new_videos': 4, 'Native_references': 1, 'Native_relative_losses': 2, 'signed_diagnostics': 1, 'CFG_slot': 1},
        'original_failed_scope_preserved': [2, 12, 8, 2], 'settlement_reconstructed': True,
        'selected_GPU_preflight_checks_actual_scope_and_production_CPU_originals': True,
        'failed_job_cost_retained': True, 'synthetic_authority_and_bridge_not_real_approval_or_video': True,
        'GPU_submissions': 0, 'ledger_written': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ['config', 'raw-receipt', 'budget']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(json.loads(args.config.read_text()), json.loads(gzip.decompress(args.raw_receipt.read_bytes())),
                         json.loads(args.budget.read_text()))))
