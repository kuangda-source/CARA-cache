#!/usr/bin/env python3
"""New H-T39 acceptance/refusal checks using prior real traces; no GPU/model run."""
import argparse
import copy
import json
from pathlib import Path
import time

from wc_w3_inactive_gt_forensic import (SCORE_STATUS, read, sha, compare_inputs,
    verify_conditional_history, reconstruct_quality)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); require_new = not a.output.exists()
    assert require_new; start = time.monotonic(); repo = a.repo
    files = ['reports/wc_w3_paired_cfg_parent_prefix_native_20261008.json.gz',
             'reports/wc_w3_d46_r3_complete_20261008_runner_json_native.gz',
             'reports/wc_w3_d46_r3_complete_20261008_CPU_score_json_native.gz',
             'reports/wc_w3_inactive_gt_semantics_cpu_r1_20261008_result_json_native.gz']
    prefix, old, oldscore, proof = [read(repo/f) for f in files]
    prior = old['cases'][1]['WC']['requests'][0]
    prefix_inputs = prefix['cases'][0]['WC']['requests'][0]['inputs'][:44]
    delta = compare_inputs(prefix_inputs, prior['inputs'][:44], proof['real_recorded_mask_hash'])
    assert len(delta) == 44 and all(d['field'] == 'kwargs.gt_frames' for d in delta)
    gt = delta[0]['current']; row = copy.deepcopy(prior)
    row['status'] = 'PAIRED_CFG_ALL_CONTROLS_COMPLETE_NOT_QUALITY'
    oldby = {c['label']: c for c in prior['children']}
    pairs = [('OFF1','OFF1'), ('OFF2','OFF2'), ('BASE_first','BASE_first'),
             ('SINGLE_second','REFRESH_second'), ('PAIRED_first','BASE_first'),
             ('PAIRED_second','BASE_second'), ('SINGLE_first','REFRESH_first'), ('BASE_second','BASE_second')]
    row['children'] = []
    for label, original in pairs:
        child = copy.deepcopy(oldby[original]); child['label'] = label; row['children'].append(child)
    olddecoded = {c['label']: c for c in prior['decoded_children']}
    row['decoded_children'] = []
    for label, original in [('OFF1','OFF1'), ('BASE_first','BASE_first'), ('PAIRED_first','BASE_first'), ('SINGLE_first','REFRESH_first')]:
        item = copy.deepcopy(olddecoded[original]); item['label'] = label; row['decoded_children'].append(item)
    for item in row['inputs']+[x for c in row['children'] for x in c['inputs']]: item['kwargs']['gt_frames'] = gt
    verdict = verify_conditional_history(row, prior, proof)
    assert verdict['checked_current_inputs'] == 296 and verdict['original_strict_GPU_acceptance'] is False
    mutations = {}
    def refuse(name, mutate):
        r, pr = copy.deepcopy(row), copy.deepcopy(proof); mutate(r, pr)
        try: verify_conditional_history(r, prior, pr)
        except (ValueError, KeyError): mutations[name] = True
        else: raise AssertionError('Unsafe evidence accepted: '+name)
    refuse('other_named_input', lambda r,p: r['inputs'][0]['kwargs'].__setitem__('x_B_C_T_H_W', '0'*64))
    refuse('args', lambda r,p: r['inputs'][0].__setitem__('args', ['extra']))
    refuse('missing_input_name', lambda r,p: r['inputs'][0]['kwargs'].pop('fps'))
    refuse('extra_input_name', lambda r,p: r['inputs'][0]['kwargs'].__setitem__('extra', '0'*64))
    refuse('nonzero_parent_mask', lambda r,p: r['inputs'][0]['kwargs'].__setitem__('condition_video_input_mask_B_C_T_H_W', '0'*64))
    refuse('nonzero_paired_mask', lambda r,p: r['children'][4]['inputs'][0]['kwargs'].__setitem__('condition_video_input_mask_B_C_T_H_W', '0'*64))
    refuse('invalid_GT', lambda r,p: r['inputs'][0]['kwargs'].__setitem__('gt_frames', 'invalid'))
    refuse('within_run_GT_change', lambda r,p: r['children'][4]['inputs'][0]['kwargs'].__setitem__('gt_frames', '0'*64))
    refuse('partial_parent', lambda r,p: r['inputs'].pop())
    refuse('partial_controls', lambda r,p: r['children'].pop())
    refuse('parent_output', lambda r,p: r['outputs'].__setitem__(0, '0'*64))
    refuse('parent_solver', lambda r,p: r['solver_outputs'].__setitem__(0, '0'*64))
    refuse('parent_bank', lambda r,p: r['banks'].__setitem__(0, {}))
    refuse('parent_components', lambda r,p: r['final_components'].__setitem__('output', '0'*64))
    refuse('parent_pipeline', lambda r,p: r['pipeline'].pop())
    refuse('parent_flags', lambda r,p: r['flags_after'].__setitem__('extra', True))
    refuse('parent_return', lambda r,p: r.__setitem__('sample_return_sha256', '0'*64))
    refuse('child_pre46', lambda r,p: r['children'][6]['pre46'].__setitem__('fingerprint', '0'*64))
    refuse('child_final', lambda r,p: r['children'][6]['record']['final_state_components'].__setitem__('output', '0'*64))
    refuse('child_encoded', lambda r,p: r['decoded_children'][3]['artifact'].__setitem__('sha256', '0'*64))
    refuse('parent_encoded', lambda r,p: r['artifact'].__setitem__('sha256', '0'*64))
    refuse('unfinished_row', lambda r,p: r.__setitem__('status', 'STARTED'))
    refuse('positive_controls_missing', lambda r,p: p['nonzero_mask_positive_controls'].pop())
    refuse('zero_mask_case_failed', lambda r,p: p['zero_mask_cases'][0].__setitem__('zero_mask_prediction_and_active_inputs_identical', False))
    refuse('finite_refusal_missing', lambda r,p: p.__setitem__('nonfinite_GT_refused', False))
    refuse('wrong_mask_dtype', lambda r,p: p.__setitem__('full_real_mask_reconstructed_dtype', 'torch.bfloat16'))
    # A fixture that repairs the old single-branch loss but merely ties BASE.
    # It must not be reported as a net improvement against original WC.
    by = {c['label']: c for c in row['children']}
    for label in ('PAIRED_first', 'PAIRED_second'):
        by[label]['deep'][:2] = [26, 26]
        for e in by[label]['record']['action_report']['suffix_events'][:2]: e['actual_action'] = 'D'
    oldcase = oldscore['cases'][1]
    score = {'status': SCORE_STATUS, 'original_strict_GPU_acceptance': False,
             'GPU_submissions': 0, 'CUDA_initialized': False, 'videos': [{'full93_decode': True} for _ in range(6)],
             'losses': {'BASE': copy.deepcopy(oldcase['losses']['BASE']), 'SINGLE': copy.deepcopy(oldcase['losses']['REFRESH']), 'PAIRED': copy.deepcopy(oldcase['losses']['BASE'])},
             'control_costs': {label: [by[label+'_'+suffix]['record']['control_wall_seconds'] for suffix in ('first','second')] for label in ('BASE','SINGLE','PAIRED')}}
    summary = reconstruct_quality(row, score)
    assert not summary['net_original_WC_fidelity_gain_at_exposed_state'] and summary['single_branch_repair_at_exposed_state']
    assert summary['comparisons'][0]['signed_quality'] == 0 and summary['comparisons'][0]['whole_full_saved'] == -2
    bad = copy.deepcopy(score); bad['losses']['PAIRED']['mean_LPIPS'] += 1
    try: reconstruct_quality(row, bad)
    except ValueError: mutations['incorrect_frame_mean'] = True
    else: raise AssertionError('Wrong frame arithmetic accepted')
    result = {'status': 'H_T39_NEW_CONDITIONAL_GATE_REAL_TRACE_MUTATION_AND_REPAIR_NET_SEPARATION_CPU_PASS_NOT_SCORE',
              'input_file_sha256': {f: sha(repo/f) for f in files}, 'actual_prefix_GT_only_differences': 44,
              'fixture_history_inputs_checked': 296, 'mutation_refusals': mutations,
              'repair_without_net_gain_separated': True, 'fixture_compute_added_retained': 2,
              'real_weights_or_new_quality': False, 'original_strict_GPU_acceptance': False,
              'GPU_submissions': 0, 'CPU_wall_seconds': time.monotonic()-start}
    with a.output.open('x') as f: f.write(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: result[k] for k in ('status','CPU_wall_seconds','repair_without_net_gain_separated')}))


if __name__ == '__main__': main()
