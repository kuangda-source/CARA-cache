#!/usr/bin/env python3
"""H-T46: link existing recorded fields; never infer unrecorded full states."""
import gzip
import hashlib
import json
import time
from pathlib import Path

REG = Path('manifests/wc_cfg_teacher_endpoint_link_cpu_preregistration_20261009.json')
OUT = Path('reports/wc_cfg_teacher_endpoint_link_cpu_results_20261009.json')
OLD_PREFIX = 'reports/wc_w3_cfg_budget_complete_r1_20261009_'
NEW_PREFIX = 'reports/wc_cfg_guided_teacher_r1_terminal_20261009_'


def load(path):
    path = Path(path)
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def compare(old, new):
    return {'equal': old == new, 'old': old, 'teacher': new}


def main():
    reg = load(REG)
    for name, sha in reg['input_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    old_capture = load('reports/wc_w3_cfg_budget_complete_r1_terminal_capture_20261009.json')
    new_capture = load(NEW_PREFIX + 'capture.json')
    old_audit = load('reports/wc_w3_cfg_budget_complete_r1_independent_reconstruction_20261009.json')
    new_audit = load(NEW_PREFIX + 'independent_CPU_audit.json')
    assert old_audit['all_masks_independently_reconstructed']
    assert old_audit['strict_repeat_groups'] == 5 and new_audit['strict_repeat_groups'] == 20
    assert new_audit['full_parent_parity'] and new_audit['tensor_hashes_verified'] == 120
    for capture in (old_capture, new_capture):
        raw = gzip.decompress(Path(capture['files']['runner']['local_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == capture['files']['runner']['sha256']
    old = load(OLD_PREFIX + 'runner_native.gz')['cases'][0]['WC']['requests'][0]
    new = load(NEW_PREFIX + 'runner_native.gz')['teacher']['parents'][1]
    children = {r['label']: r for r in old['children']}
    origins = {r['label']: r for r in new['origins']}
    result = {'status': 'EXPOSED_CFG_TEACHER_ENDPOINT_RECORDED_FIELD_LINK_CPU_COMPLETE_NOT_MEDIATION_NOT_CONF',
        'preregistration': str(REG), 'preregistration_sha256': hashlib.sha256(REG.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'observed_unix': time.time(), 'input_sha256': reg['input_sha256'],
        'scope': reg['registered_denominator'], 'trace_joins': [], 'S22_state_comparisons': [],
        'one_step_and_own_history_bridges': [],
        'unrecorded_fields': {'old_full_pre47_components': 'UNRECORDED',
                             'old_post_denoise_signed_vectors': 'UNRECORDED'},
        'historical_full_S23_state_acceptance': False, 'unique_endpoint_causal_attribution': False,
        'independent_CONF': False, 'formal_RV_labels': False, 'new_generation_or_training': False,
        'CUDA_initialized': False, 'GPU_submissions': 0,
        'teacher_S23_origin_is_shared_first_repeat_bridge': True}
    for arm, mapping in reg['fixed_mapping'].items():
        root_first = next(r for r in origins['S22']['pairs']
                          if r['label'] == mapping['S22_mode'] + '_first')
        for repeat in reg['repeats']:
            child = children[arm + '_' + repeat]
            root = next(r for r in origins['S22']['pairs']
                        if r['label'] == mapping['S22_mode'] + '_' + repeat)
            later = next(r for r in origins[mapping['S23_origin']]['pairs']
                         if r['label'] == mapping['S23_mode'] + '_' + repeat)
            assert child['status'] == 'COMPLETE_SUFFIX_NOT_RV_LABEL'
            for pair, offset, calls in ((root, 0, [45, 46]), (later, 2, [47, 48])):
                assert pair['parent_restored']
                fields = {name: compare(child[name][offset:offset+2], pair[name])
                          for name in reg['exact_trace_fields']}
                result['trace_joins'].append({'arm': arm, 'repeat': repeat, 'calls': calls,
                    'teacher_origin': 'S22' if not offset else mapping['S23_origin'],
                    'teacher_cell': pair['mode'], 'fields': fields,
                    'all_recorded_trace_fields_equal': all(v['equal'] for v in fields.values())})
            point = child['pre45']
            keys = sorted(set(point['components']) | set(root['origin_components']))
            different = {key: compare(point['components'].get(key), root['origin_components'].get(key))
                         for key in keys if point['components'].get(key) != root['origin_components'].get(key)}
            result['S22_state_comparisons'].append({'arm': arm, 'repeat': repeat,
                'old_component_count': len(point['components']),
                'teacher_component_count': len(root['origin_components']),
                'inventory_equal': set(point['components']) == set(root['origin_components']),
                'different_components': different,
                'all_recorded_components_equal': point['components'] == root['origin_components'],
                'solver_configuration': compare(point['solver_configuration'], root['origin_solver_configuration']),
                'own_history': compare(point['own_history'], root['origin_own_history'])})
            old_history = child['record']['action_report']['suffix_events'][1]['true_full_history']
            bridge = {'arm': arm, 'repeat': repeat,
                'old_first_solver_output_vs_teacher_root_first_solver': compare(child['solver_outputs'][0], root_first['solver_outputs'][0]),
                'old_first_solver_output_vs_child_origin_latent': compare(child['solver_outputs'][0], later['origin_components']['output']),
                'old_call46_history_vs_child_own_history': compare(old_history, later['origin_own_history'])}
            bridge['all_registered_bridge_fields_equal'] = all(v['equal'] for v in bridge.values() if isinstance(v, dict))
            result['one_step_and_own_history_bridges'].append(bridge)
    assert len(result['trace_joins']) == 16 and len(result['S22_state_comparisons']) == len(result['one_step_and_own_history_bridges']) == 8
    result['summary'] = {
        'trace_joins_all_equal': sum(r['all_recorded_trace_fields_equal'] for r in result['trace_joins']),
        'S22_full_component_comparisons_equal': sum(r['all_recorded_components_equal'] for r in result['S22_state_comparisons']),
        'one_step_and_own_history_bridges_equal': sum(r['all_registered_bridge_fields_equal'] for r in result['one_step_and_own_history_bridges']),
        'S22_different_component_names': sorted({k for r in result['S22_state_comparisons'] for k in r['different_components']})}
    with OUT.open('x') as file:
        file.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'scope': result['scope'], 'summary': result['summary'],
                      'unrecorded_fields': result['unrecorded_fields'], 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
