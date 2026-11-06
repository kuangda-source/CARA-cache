"""H-T39 CPU-only evidence; original H-T38 strict refusal remains a refusal."""
import gzip
import hashlib
import json
import math
from pathlib import Path

FAILURE = 'Original seed2 parent raw-state bridge differs'
TRACE = ['inputs', 'outputs', 'deep', 'banks', 'solver_outputs']
SCORE_STATUS = 'INACTIVE_GT_CONDITIONAL_FULL93_THREE_LOSSES_TWO_PAIRS_NOT_ORIGINAL_ACCEPTANCE_NOT_CONF'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def compare_inputs(current, original, mask):
    """Allow only the registered inactive field; no general hash normalization."""
    require(len(current) == len(original) and bool(current), 'Input coverage differs')
    differences = []
    for index, (a, b) in enumerate(zip(current, original)):
        require(set(a) == set(b) == {'args', 'kwargs'} and a['args'] == b['args'], 'Positional input differs')
        require(set(a['kwargs']) == set(b['kwargs']), 'Named input inventory differs')
        for item in (a, b):
            kw = item['kwargs']
            require(kw['condition_video_input_mask_B_C_T_H_W'] == mask, 'Actual mask is not proven zero')
            gt = kw['gt_frames']
            require(isinstance(gt, str) and len(gt) == 64 and set(gt) <= set('0123456789abcdef'), 'GT trace hash invalid')
        for name in a['kwargs']:
            if a['kwargs'][name] != b['kwargs'][name]:
                require(name == 'gt_frames', 'Other historical input differs: ' + name)
                differences.append({'index': index, 'field': 'kwargs.gt_frames',
                                    'current': a['kwargs'][name], 'original': b['kwargs'][name]})
    return differences


def verify_semantics(proof):
    require(proof['status'] == 'INACTIVE_GT_ZERO_MASK_REAL_DENOISE_AST_AND_ACTUAL_MASK_CPU_PASS_NOT_REAL_WEIGHTS_OR_GPU_ACCEPTANCE'
            and proof['CUDA_initialized'] is False and proof['GPU_submissions'] == 0, 'Actual semantics CPU proof missing')
    require(len(proof['zero_mask_cases']) == 16 and all(x['zero_mask_prediction_and_active_inputs_identical'] for x in proof['zero_mask_cases'])
            and len(proof['nonzero_mask_positive_controls']) == 4 and all(x['nonzero_mask_detected_GT_effect'] for x in proof['nonzero_mask_positive_controls']), 'Semantics CPU denominator/control differs')
    require(proof['nonfinite_GT_refused'] and proof['gt_frames_never_read_by_WC_forward']
            and proof['WC_extra_kwargs_only_lookup'] == 'timestep_scale'
            and proof['real_text2world_num_input_frames_property_zero']
            and proof['full_real_mask_reconstructed_shape'] == [1, 1, 24, 54, 96]
            and proof['full_real_mask_reconstructed_dtype'] == 'torch.float32'
            and proof['original_strict_historical_input_criterion_unchanged'], 'Inactive GT scope proof differs')
    return proof['real_recorded_mask_hash']


def verify_conditional_history(row, prior, proof):
    mask = verify_semantics(proof)
    require(row['status'] == 'PAIRED_CFG_ALL_CONTROLS_COMPLETE_NOT_QUALITY', 'Complete original row required')
    require(all(len(row[k]) == (36 if k == 'solver_outputs' else 72) for k in TRACE), 'Parent coverage differs')
    changes = {'parent': compare_inputs(row['inputs'], prior['inputs'], mask)}
    require(len(changes['parent']) == 72, 'Previously observed GT-only difference not retained through full parent')
    for key in TRACE[1:] + ['final_latent_sha256', 'final_components', 'pipeline', 'flags_before', 'flags_after', 'sample_return_sha256']:
        require(row[key] == prior[key], 'Historical parent state/output differs: ' + key)
    current = {c['label']: c for c in row['children']}
    original = {c['label']: c for c in prior['children']}
    decoded = {c['label']: c['artifact'] for c in row['decoded_children']}
    olddecoded = {c['label']: c['artifact'] for c in prior['decoded_children']}
    for name, oldname in [('BASE_first', 'BASE_first'), ('SINGLE_first', 'REFRESH_first')]:
        a, b = current[name], original[oldname]
        changes[name] = compare_inputs(a['inputs'], b['inputs'], mask)
        require(len(changes[name]) == 28, 'Full historical child GT-only coverage differs')
        for key in TRACE[1:] + ['final_latent_sha256', 'pre46']:
            require(a[key] == b[key], 'Historical child state/output differs: ' + name + ':' + key)
        require(a['record']['final_state_components'] == b['record']['final_state_components'], 'Historical final components differ')
        for key in ('sha256', 'bytes'):
            require(decoded[name][key] == olddecoded[oldname][key], 'Historical encoding differs')
    require(all(row['artifact'][k] == prior['artifact'][k] for k in ('sha256', 'bytes')), 'Historical parent encoding differs')
    all_inputs = row['inputs'] + [x for child in row['children'] for x in child['inputs']]
    require(len(all_inputs) == 296, 'All current arm input coverage differs')
    require(all(x['kwargs']['condition_video_input_mask_B_C_T_H_W'] == mask for x in all_inputs), 'A current arm mask differs')
    current_gt = {d['current'] for ds in changes.values() for d in ds}
    old_gt = {d['original'] for ds in changes.values() for d in ds}
    require(len(current_gt) == len(old_gt) == 1 and all(x['kwargs']['gt_frames'] in current_gt for x in all_inputs), 'GT changes within a run')
    return {'status': 'GT_ONLY_CONDITIONAL_HISTORY_PASS_ORIGINAL_STRICT_GATE_FAILED',
            'allowed_named_field': 'kwargs.gt_frames', 'historical_differences': changes,
            'checked_current_inputs': len(all_inputs), 'actual_zero_mask_hash': mask,
            'all_other_historical_inputs_states_outputs_and_encoded_bytes_equal': True,
            'original_strict_GPU_acceptance': False, 'independent_CONF': False}


def verify_terminal(r, sup, post, budget, config):
    require(sup['exit_code'] == 1 and sup['status'] == 'EXITED_REQUIRES_RESULT_AUDIT'
            and r['status'] == 'PAIRED_CFG_TECH_BLOCKED_FULL_DENOMINATOR_RETAINED'
            and r['error'] == FAILURE, 'Original failure is not the registered GT input bridge refusal')
    require(post['exit_code'] == 1 and post['status'] == 'PAIRED_CFG_POST_CPU_FAILED_OR_GPU_FAILED_NOT_METHOD_DENIAL'
            and post['error'] == 'Original GPU failed; preserve denominator and costs, do not score/restart'
            and post['scored_videos'] == post['GPU_submissions'] == 0 and 'score_pid' not in post, 'Original no-score refusal not preserved')
    require(sup['source_revision'] == r['source_revision'] == post['source_revision'] == 'aa996edf2d8fc3eb99018fac916a63034c5f53d5'
            and [sup['pid'], sup['child_pid']] == post['bound_GPU_PIDs'], 'Original execution identity differs')
    require(sup['run_id'] == r['run_id'] == config['execution_run_id'] == 'wc-w3-paired-cfg-r1'
            and r['config'] == config and r['planned_scope'] == config['preregistration']['scope_counts'], 'Original config/scope differs')
    require(budget == sup['budget_after'] == post['budget_at_end'] and budget['cap_gpu_hours'] == 24
            and not any('inflight' in key for key in budget)
            and budget['gpu_jobs_launched'] == sup['budget_before']['gpu_jobs_launched'] + 1
            and math.isclose(budget['used_gpu_hours'], sup['budget_before']['used_gpu_hours'] + sup['wall_seconds']/3600, abs_tol=1e-12), 'All original costs not settled')
    require(not sup['release']['pids'] and sup['release']['memory_used_mib'] <= 1024
            and not sup.get('cumulative_budget_stop', False), 'GPU release or full completion differs')
    require(len(r['cases']) == 1 and r['cases'][0]['seed'] == 2
            and r['cases'][0]['WC']['status'] == 'PAIRED_CFG_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT', 'Full original generation did not complete')
    return r['cases'][0]['WC']['requests'][0]


def reconstruct_quality(row, score):
    """Independent arithmetic from all frames and raw actual deep-call records."""
    require(score['status'] == SCORE_STATUS and score['original_strict_GPU_acceptance'] is False
            and score['GPU_submissions'] == 0 and score['CUDA_initialized'] is False
            and len(score['videos']) == 6 and all(v['full93_decode'] for v in score['videos']), 'Conditional full score boundary differs')
    require(set(score['losses']) == {'BASE', 'SINGLE', 'PAIRED'}, 'Three losses required')
    by = {c['label']: c for c in row['children']}
    decoded = {c['label']: c['artifact'] for c in row['decoded_children']}
    counts = {}
    costs = {}
    for label in ('BASE', 'SINGLE', 'PAIRED'):
        loss = score['losses'][label]
        require(loss['frames'] == len(loss['frame_distances']) == len(loss['pts']) == 93
                and all(math.isfinite(v) and v >= 0 for v in loss['frame_distances'])
                and loss['mean_LPIPS'] == sum(loss['frame_distances'])/93
                and loss['candidate_sha256'] == decoded[label+'_first']['sha256']
                and loss['pts'] == score['losses']['BASE']['pts']
                and loss['reference_sha256'] == score['losses']['BASE']['reference_sha256'], 'Full93 loss/identity differs')
        child = by[label+'_first']; deep = child['deep']; events = child['record']['action_report']['suffix_events']
        require(len(deep) == 28 and [e['call'] for e in events] == list(range(45, 73))
                and all(x in (0, 26) for x in row['deep'][:44]+deep)
                and all((e['actual_action'] == 'D') == (d == 26) for e, d in zip(events, deep)), 'Actual compute trace differs')
        counts[label] = {'whole_CFG': [sum(x == 26 for x in (row['deep'][:44]+deep)[slot::2]) for slot in (0, 1)],
                         'current45_46_CFG': [int(x == 26) for x in deep[:2]],
                         'future47_72_CFG': [sum(x == 26 for x in deep[2:][slot::2]) for slot in (0, 1)]}
        costs[label] = [by[label+'_'+part]['record']['control_wall_seconds'] for part in ('first', 'second')]
        require(costs[label] == score['control_costs'][label] and all(math.isfinite(t) and t > 0 for t in costs[label]), 'Actual repeated costs differ')
    require([counts[k]['current45_46_CFG'] for k in ('BASE', 'SINGLE', 'PAIRED')] == [[0, 0], [0, 1], [1, 1]], 'Three actual current actions differ')
    comparisons = []
    for label in ('BASE', 'SINGLE'):
        a, b = score['losses'][label], score['losses']['PAIRED']
        delta = [x-y for x, y in zip(a['frame_distances'], b['frame_distances'])]
        q = a['mean_LPIPS']-b['mean_LPIPS']
        current = sum(counts['PAIRED']['current45_46_CFG'])-sum(counts[label]['current45_46_CFG'])
        future = sum(counts[label]['future47_72_CFG'])-sum(counts['PAIRED']['future47_72_CFG'])
        total = sum(counts[label]['whole_CFG'])-sum(counts['PAIRED']['whole_CFG'])
        require(total == future-current, 'Whole compute accounting differs')
        comparisons.append({'comparison': 'PAIRED_vs_'+label, 'reference_LPIPS': a['mean_LPIPS'], 'PAIRED_LPIPS': b['mean_LPIPS'],
            'signed_quality': q, 'relative_improvement_percent': 100*q/a['mean_LPIPS'],
            'improved_frames': sum(v > 0 for v in delta), 'worse_frames': sum(v < 0 for v in delta), 'tied_frames': sum(v == 0 for v in delta),
            'frame_signed_changes': delta, 'three_equal31_frame_mean_changes': [math.fsum(delta[i:i+31])/31 for i in (0, 31, 62)],
            'reference_counts': counts[label], 'PAIRED_counts': counts['PAIRED'], 'current_full_added': current,
            'strict_future_full_saved': future, 'whole_full_saved': total,
            'signed_diagnostic_seconds': math.fsum(costs[label])/2-math.fsum(costs['PAIRED'])/2})
    return {'comparisons': comparisons, 'raw_compute_counts': counts,
            'net_original_WC_fidelity_gain_at_exposed_state': comparisons[0]['signed_quality'] > 0,
            'single_branch_repair_at_exposed_state': comparisons[1]['signed_quality'] > 0,
            'repeat_diagnostic_ranges': {k: max(v)-min(v) for k, v in costs.items()},
            'original_strict_GPU_acceptance': False, 'independent_CONF': False,
            'clean_speed_measurement': False, 'physics_or_semantic_acceptance': False}
