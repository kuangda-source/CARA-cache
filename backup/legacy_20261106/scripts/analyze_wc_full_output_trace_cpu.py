#!/usr/bin/env python3
"""Hash-bound CPU trajectory comparison; hashes are not error norms or causality."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def first_difference(left, right):
    if len(left) != len(right):
        raise ValueError('Unequal full-trajectory coverage')
    return next((i for i, (a, b) in enumerate(zip(left, right), 1) if a != b), None)


def analyze(summary, runner_bytes):
    if hashlib.sha256(runner_bytes).hexdigest() != summary['runner_receipt']['uncompressed_sha256']:
        raise ValueError('Full raw receipt SHA differs from audited summary')
    r = json.loads(runner_bytes)
    if (r['status'] != 'COMPLETE_SIX_OUTPUTS_DD_AND_TWO_WC_S_PAIRS_REQUIRES_AUDIT'
            or summary['completed_phases'] != 6 or not summary['independent_full_provenance_video_audit_pass']):
        raise ValueError('Six-output technical evidence incomplete')
    rows = []
    for q in r['comparison']['requests']:
        a, b = q['phases']
        assert len(a['trace']) == len(b['trace']) == len(a['output_hashes']) == 72
        events = b['refresh_provenance']['events']
        assert len(events) == 72
        sparse = [v['call'] for v in events if v['sparse_layers']]
        changed = [{'call': x['call'], 'solver_update': (x['call'] + 1) // 2,
                    'CFG_slot': (x['call'] - 1) % 2,
                    'official_deep': x['deep_executed'], 'candidate_deep': y['deep_executed']}
                   for x, y in zip(a['trace'], b['trace']) if x != y]
        ages = [{'cache_call': e['call'], 'source_call': s['call'],
                 'CFG_slot': e['cfg'], 'source_kind': s['kind'],
                 'effective_solver_age': (e['call'] - s['call']) // 2}
                for e in events if e['action'] == 'cache' for s in e['references_read']]
        assert all(v['effective_solver_age'] >= 1 for v in ages)
        first_output = first_difference(a['output_hashes'], b['output_hashes'])
        assert first_output == sparse[0]
        first_input = first_difference(a['named_inputs'], b['named_inputs'])
        assert a['conditions'] == b['conditions'] and a['sampling'] == b['sampling']
        rows.append({'sample_name': q['sample_name'], 'first_sparse_CFG_call': sparse[0],
            'first_changed_model_output_CFG_call': first_output,
            'first_changed_named_model_input_CFG_call': first_input,
            'first_changed_refresh_decision_CFG_call': changed[0]['call'] if changed else None,
            'full_cache_decision_differences': changed,
            'deep_calls_official_candidate': [sum(v['deep_executed'] for v in p['trace']) for p in (a, b)],
            'model_output_equal_CFG_calls': [i for i, (x, y) in enumerate(zip(a['output_hashes'], b['output_hashes']), 1) if x == y],
            'last_two_calls': [{'call': i + 1, 'official_deep': a['trace'][i]['deep_executed'],
                'candidate_deep': b['trace'][i]['deep_executed'],
                'model_input_equal': a['named_inputs'][i] == b['named_inputs'][i],
                'model_output_equal': a['output_hashes'][i] == b['output_hashes'][i]} for i in (70, 71)],
            'cache_reference_ages': ages,
            'max_cache_reference_age': max(v['effective_solver_age'] for v in ages),
            'debug_wall_seconds_official_candidate': [a['wall_seconds'], b['wall_seconds']],
            'conditions_and_grid_equal': True})
    return {'status': 'FULL_TWO_CAL_TRACE_CPU_DIAGNOSTIC_COMPLETE_NO_CAUSAL_OR_COST_ATTRIBUTION',
        'CPU_only': True, 'rows': rows, 'same_state_error_norms_available': False,
        'per_component_elapsed_costs_available': False,
        'source_reset_is_not_latent_trajectory_reset': True,
        'quality_acceptance': False, 'clean_E2E_speed_claim': False,
        'limits': ['Order of hash/decision divergence does not isolate a causal quality contribution.',
            'Output hash mismatch cannot quantify velocity, residual or latent error.',
            'Completed debug receipts contain total phase wall, not per-hook elapsed costs.',
            'Video frame segments and denoising solver steps are different coordinates.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--summary', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    s = json.loads(args.summary.read_text())
    receipt = args.summary.parent.parent / s['runner_receipt']['path']
    result = analyze(s, gzip.decompress(receipt.read_bytes()))
    result['summary_sha256'] = hashlib.sha256(args.summary.read_bytes()).hexdigest()
    result['analysis_code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'rows': [{k: v for k, v in x.items()
        if k in ['sample_name', 'first_sparse_CFG_call', 'first_changed_named_model_input_CFG_call',
                 'first_changed_refresh_decision_CFG_call', 'max_cache_reference_age', 'last_two_calls']}
        for x in result['rows']]}))
