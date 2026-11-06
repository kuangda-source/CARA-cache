"""Five Native losses, two signed tail effects, explicit cost/count outcomes."""
import copy
import math

POLICY = {'comparison':'REGISTERED_JOINT_SWAP_FIXED_VS_NATIVE_OWN_STATE_TAIL69_70',
    'benefit':'LPIPS_FIXED_MINUS_TAIL_NEGATIVE_RETAINED', 'per_CFG_quota_matched':False,
    'single_action_RV_training_label':False, 'online_policy':False,
    'clean_speed_measurement':False, 'independent_CONF':False,
    'physics_or_quality_noninferiority':False}


def reused_losses(prior, plan, config, metric_protocol):
    if (prior['status'] != 'PLACEMENT_FULL93_FRAME_SIX_NATIVE_RELATIVE_LPIPS_AND4_SIGNED_JOINT_DIAGNOSTICS_NOT_RV_LABELS'
            or prior['CUDA_initialized'] is not False or prior['metric_protocol'] != metric_protocol
            or len(prior['pairs']) != 6):
        raise ValueError('Frozen actual R2 score and identical full93 metric required')
    scene = 'human_199'; reference = config['references'][scene]['Native35']
    by = {p['label']:p for p in prior['pairs'] if p['scene']==scene}
    current = {c['label']:c['artifact'] for c in plan['row']['decoded_children']}
    result = []
    for old, new, candidate in [('BASE1','BASE',plan['row']['artifact']),
        ('SWAP1_first','FIXED46_first',current['FIXED46_first']),
        ('SWAP0_first','FIXED61_first',current['FIXED61_first'])]:
        pair = by[old]; score = copy.deepcopy(pair['score'])
        if (pair['reference'] != reference or pair['candidate']['sha256'] != candidate['sha256']
                or score['reference_sha256'] != reference['sha256']
                or score['candidate_sha256'] != candidate['sha256']):
            raise ValueError('R2 reused loss must bind identical reference/candidate bytes')
        result.append({'scene':scene,'label':new,'CFG_slot':pair['CFG_slot'],
            'reference':reference,'candidate':candidate,'score':score,
            'reused_original_pair_label':old,'reused_identical_SHA_protocol_loss':True})
    return result


def signed_tail_diagnostics(pairs, receipt, config):
    expected = ['BASE','FIXED46_first','FIXED61_first','TAIL46_first','TAIL61_first']
    if len(pairs) != 5 or [p['label'] for p in pairs] != expected:
        raise ValueError('All five ordered Native losses required')
    reference = config['references']['human_199']['Native35']
    by = {}
    for pair in pairs:
        score = pair['score']; values = score['frame_distances']
        if (pair['scene'] != 'human_199' or pair['reference'] != reference
                or score['frames'] != 93 or len(values) != 93 or len(score['pts']) != 93
                or score['reference_sha256'] != reference['sha256']
                or score['candidate_sha256'] != pair['candidate']['sha256']
                or any(type(v) not in (int,float) or not math.isfinite(v) for v in values)
                or not math.isclose(score['mean_LPIPS'],sum(values)/93,rel_tol=1e-12,abs_tol=1e-12)):
            raise ValueError('Actual full93 score/frame/ref/candidate binding differs')
        by[pair['label']] = score
    row = receipt['requests'][0]; children = {c['label']:c for c in row['children']}
    result = []
    for case in config['scope']['scenes'][0]['cases']:
        name = case['name']; a = by['FIXED'+name+'_first']; b = by['TAIL'+name+'_first']
        if a['pts'] != b['pts'] or a['pts'] != by['BASE']['pts']:
            raise ValueError('Tail pair full-frame timestamp binding differs')
        costs = {}
        for mode in ('FIXED','TAIL'):
            controls = [children[mode+name+'_'+r] for r in ('first','second')]
            wall = [c['record']['control_wall_seconds'] for c in controls]
            if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in wall):
                raise ValueError('Both actual complete suffix timing records required')
            costs[mode] = {'whole_CFG_full_counts':controls[0]['record']['action_report']['per_CFG_full_counts'],
                'control_wall_seconds_repeats':wall,'mean_control_wall_seconds':sum(wall)/2}
        result.append({'scene':'human_199','case':name,'CFG_slot':case['CFG_slot'],
            'swap_calls':case['swap_calls'],'LPIPS_FIXED':a['mean_LPIPS'],'LPIPS_TAIL':b['mean_LPIPS'],
            'LPIPS_FIXED_minus_TAIL':a['mean_LPIPS']-b['mean_LPIPS'],
            'relative_fidelity_improvement':(a['mean_LPIPS']-b['mean_LPIPS'])/a['mean_LPIPS'],
            'tail_relative_to_BASE':(by['BASE']['mean_LPIPS']-b['mean_LPIPS'])/by['BASE']['mean_LPIPS'],
            'improved_frames':sum(x>y for x,y in zip(a['frame_distances'],b['frame_distances'])),
            'worse_frames':sum(x<y for x,y in zip(a['frame_distances'],b['frame_distances'])),
            'costs':costs,'mean_control_wall_FIXED_minus_TAIL':
                costs['FIXED']['mean_control_wall_seconds']-costs['TAIL']['mean_control_wall_seconds'],
            'actual_tail_action_changes':children['TAIL'+name+'_first']['record']['action_report']['tail_action_changes'],
            'policy_protocol':POLICY.copy(),'signed_negative_retained':True})
    return result
