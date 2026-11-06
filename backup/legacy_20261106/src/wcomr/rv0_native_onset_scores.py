"""Five Native losses and two preregistered earlier-vs-late response effects."""
import copy
import math

POLICY = {'comparison': 'REGISTERED_COMMON61_63_SWAP_EARLIER_VS_LATE_NATIVE_OWN_STATE_RESPONSE',
    'benefit': 'LPIPS_LATE69_MINUS_RESPONSE_NEGATIVE_RETAINED', 'per_CFG_quota_matched': False,
    'single_action_RV_training_label': False, 'online_policy': False,
    'clean_speed_measurement': False, 'independent_CONF': False,
    'physics_or_quality_noninferiority': False}


def reused_losses(prior, plan, config, metric_protocol):
    if (prior['status'] != 'NATIVE_TAIL_FULL93_FIVE_LOSSES_THREE_REUSED_TWO_NEW_AND2_SIGNED_POLICY_EFFECTS_NOT_RV_LABELS'
            or prior['CUDA_initialized'] is not False or prior['metric_protocol'] != metric_protocol
            or len(prior['pairs']) != 5):
        raise ValueError('Actual previous tail score and identical full93 metric required')
    scene = 'human_199'; reference = config['references'][scene]['Native35']
    by = {p['label']: p for p in prior['pairs'] if p['scene'] == scene}
    current = {c['label']: c['artifact'] for c in plan['row']['decoded_children']}
    result = []
    for old, new, candidate in [('BASE', 'BASE', plan['row']['artifact']),
            ('FIXED61_first', 'FIXED61_first', current['FIXED61_first']),
            ('TAIL61_first', 'LATE69_first', current['LATE69_first'])]:
        pair = by[old]; score = copy.deepcopy(pair['score'])
        if (pair['reference'] != reference or pair['candidate']['sha256'] != candidate['sha256']
                or score['reference_sha256'] != reference['sha256']
                or score['candidate_sha256'] != candidate['sha256']):
            raise ValueError('Reused loss must bind identical reference/candidate bytes')
        result.append({'scene': scene, 'label': new, 'CFG_slot': pair.get('CFG_slot'),
            'reference': reference, 'candidate': candidate, 'score': score,
            'reused_original_pair_label': old, 'reused_identical_SHA_protocol_loss': True})
    return result


def signed_response_diagnostics(pairs, receipt, config):
    expected = ['BASE', 'FIXED61_first', 'LATE69_first', 'RESP65_first', 'RESP67_first']
    if len(pairs) != 5 or [p['label'] for p in pairs] != expected:
        raise ValueError('All five ordered Native losses required')
    reference = config['references']['human_199']['Native35']; by = {}
    for pair in pairs:
        score = pair['score']; values = score['frame_distances']
        if (pair['scene'] != 'human_199' or pair['reference'] != reference
                or score['frames'] != 93 or len(values) != 93 or len(score['pts']) != 93
                or score['reference_sha256'] != reference['sha256']
                or score['candidate_sha256'] != pair['candidate']['sha256']
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
                or not math.isclose(score['mean_LPIPS'], sum(values)/93, rel_tol=1e-12, abs_tol=1e-12)):
            raise ValueError('Full93 score/frame/ref/candidate binding differs')
        by[pair['label']] = score
    if any(s['pts'] != by['BASE']['pts'] for s in by.values()):
        raise ValueError('All five full-frame timestamp bindings required')
    row = receipt['requests'][0]; children = {c['label']: c for c in row['children']}
    result = []
    for start in (65, 67):
        mode = 'RESP'+str(start); a = by['LATE69_first']; b = by[mode+'_first']
        costs = {}
        for name in ('LATE69', mode):
            controls = [children[name+'_'+r] for r in ('first', 'second')]
            wall = [c['record']['control_wall_seconds'] for c in controls]
            if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in wall):
                raise ValueError('Both actual complete suffix timings required')
            costs[name] = {'whole_CFG_full_counts': controls[0]['record']['action_report']['per_CFG_full_counts'],
                'control_wall_seconds_repeats': wall, 'mean_control_wall_seconds': sum(wall)/2}
        baseline = by['BASE']['mean_LPIPS']; fixed = by['FIXED61_first']['mean_LPIPS']
        result.append({'scene': 'human_199', 'response_start': start, 'swap_calls': [61, 63],
            'LPIPS_LATE69': a['mean_LPIPS'], 'LPIPS_RESPONSE': b['mean_LPIPS'],
            'LPIPS_LATE69_minus_RESPONSE': a['mean_LPIPS']-b['mean_LPIPS'],
            'relative_fidelity_improvement': (a['mean_LPIPS']-b['mean_LPIPS'])/a['mean_LPIPS'],
            'response_relative_to_BASE': (baseline-b['mean_LPIPS'])/baseline,
            'relative_improvement_vs_FIXED61': (fixed-b['mean_LPIPS'])/fixed,
            'fraction_FIXED61_excess_distortion_repaired': (fixed-b['mean_LPIPS'])/(fixed-baseline) if fixed > baseline else None,
            'improved_frames_vs_LATE69': sum(x > y for x,y in zip(a['frame_distances'],b['frame_distances'])),
            'worse_frames_vs_LATE69': sum(x < y for x,y in zip(a['frame_distances'],b['frame_distances'])),
            'costs': costs, 'mean_control_wall_LATE69_minus_RESPONSE':
                costs['LATE69']['mean_control_wall_seconds']-costs[mode]['mean_control_wall_seconds'],
            'actual_response_action_changes': children[mode+'_first']['record']['action_report']['response_action_changes'],
            'policy_protocol': POLICY.copy(), 'signed_negative_retained': True})
    return result
