#!/usr/bin/env python3
"""Bind measured restore/fair receipts to the full next RV0 proposal, CPU only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); sys.path.insert(0, str(a.project/'src'))
    from wcomr.rv0_causal_scope import proposal, validate_scope, price, budget_gate, SCENES
    files = ['reports/wc_rv0_restore_r1_summary_20261004.json',
             'reports/wc_rv0_restore_r1_runner_20261004.json',
             'reports/wc_fair_cal_r1_summary_20261004.json', 'reports/budget.json']
    raw = {n: (a.project/n).read_bytes() for n in files}
    restore, runner, fair, budget = [json.loads(raw[n]) for n in files]
    assert restore['parent_phases'] == 2 and restore['complete_suffixes'] == 4
    assert restore['full_RV0_acceptance'] is False
    assert all(restore['budget'][k] == budget[k] for k in ['used_gpu_hours', 'gpu_jobs_launched'])
    authorization = json.loads((a.project/budget['budget_authorization_ref']).read_text())
    assert authorization['previous_cap_gpu_hours'] == 12
    assert authorization['cumulative_cap_gpu_hours'] == budget['cap_gpu_hours'] == 13
    assert authorization['usage_reset'] is authorization['transfers_between_projects'] is False
    assert authorization['source_user_text'] == '允许增加 GPUh'
    assert authorization['user_message_id'] == 'Sentinel_861e63a87d8c819180ec9a8bcfa6dc92'
    assert [r['sample'] for r in restore['rows']] == SCENES
    assert len(fair['rows']) == 12 and fair['audited_outputs'] == 14
    native = [r['pipeline_wall_seconds'] for r in fair['rows'] if r['variant'] == 'native35']
    wc = [r['pipeline_wall_seconds'] for r in fair['rows'] if r['variant'] == 'wc006']
    assert len(native) == len(wc) == 2
    parent_without_children = [r['parent_pipeline_including_diagnostics_wall_seconds']-
         sum(s['inclusive_wall_seconds'] for s in r['suffixes']) for r in restore['rows']]
    scope = proposal(); validate_scope(scope)
    cost = price(scope, loading=runner['load_seconds'], native_pipeline=max(native),
        wc_pipeline=max(wc), diagnostic_parent_without_children=max(parent_without_children),
        unchanged_suffix_inclusive=max(s['inclusive_wall_seconds'] for r in restore['rows'] for s in r['suffixes']))
    remaining = (scope['cumulative_cap_gpu_hours']-budget['used_gpu_hours'])*3600
    required = scope['proposed_timeout_seconds']+scope['admission_allowance_seconds']
    admissible = False; reason = None
    try: budget_gate(budget, scope); admissible = True
    except ValueError as error: reason = str(error)
    result = {'status': 'FULL_RV0_CAUSAL_SCOPE_PRICED_CPU_ONLY_NOT_SELECTED',
        'scope': scope, 'cost': cost, 'budget': budget, 'remaining_seconds': remaining,
        'required_cap_plus_admission_seconds': required,
        'shortfall_seconds': max(0, required-remaining), 'budget_admissible': admissible,
        'budget_refusal': reason, 'new_GPU_submission': False, 'reserved_seconds': 0, 'RV_labels': 0,
        'measured_input_values': {'load_seconds': runner['load_seconds'],
            'Native_pipeline_by_scene': native, 'WC_pipeline_by_scene': wc,
            'diagnostic_parent_without_children_by_scene': parent_without_children,
            'unchanged_suffixes_by_scene': [[s['inclusive_wall_seconds'] for s in r['suffixes']] for r in restore['rows']]},
        'input_files_sha256': {n: hashlib.sha256(v).hexdigest() for n, v in raw.items()},
        'limits': ['These are measured-source proxies plus explicit allowances, not a proven C/D runtime bound.',
                   'Do not drop scenes/CFG/suffixes/Native/OFF controls or increase the authorized13h ledger automatically.',
                   'LPIPS CPU resources/protocol are prepared; server original audits, budget-matched suffix, production runner/deployment and real C/D gates remain incomplete.']}
    a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['status', 'remaining_seconds', 'required_cap_plus_admission_seconds',
        'shortfall_seconds', 'budget_admissible']} | {'conditional_estimated_seconds': cost['conditional_estimated_seconds']}))


if __name__ == '__main__': main()
