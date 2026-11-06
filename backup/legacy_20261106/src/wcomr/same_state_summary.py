"""Receipt-bound mechanism summary; engineering points are not independent trials."""
import math
from statistics import median


METRICS = ('prewarp_residual', 'postwarp_residual', 'velocity')
PARITY_FIELDS = ('forward_output_sha256', 'block_counts', 'trace', 'cache_end_sha256', 'video_sha256')


def summarize(receipt, supervisor):
    if (receipt.get('status') != 'SAME_STATE_CANDIDATE_DIAGNOSTIC_PARITY_PASS_SINGLE_SAMPLE'
            or supervisor.get('status') != 'W1_SAME_STATE_EXITED_REQUIRES_REVIEW'):
        raise ValueError('Terminal successful diagnostic and supervisor required')
    arms = supervisor.get('arms', [])
    if len(arms) != 1 or arms[0]['exit_code'] != 0 or arms[0]['stop_reason'] is not None:
        raise ValueError('One completed supervised job required')
    if len(receipt.get('runs', [])) != 2:
        raise ValueError('New-version off and on runs required')
    off, on = receipt['runs']
    if [off['mode'], on['mode']] != ['off', 'on']:
        raise ValueError('Wrong run identities')
    if any(off[k] != on[k] for k in PARITY_FIELDS) or off['sampling'] != on['sampling']:
        raise ValueError('Observed output/state/sampling parity mismatch')
    if len(off['forward_output_sha256']) != 72 or on['block_counts']['denoiser_calls'] != 72:
        raise ValueError('Expected frozen 72-call protocol')
    if not receipt.get('checks') or not all(v is True for v in receipt['checks'].values()):
        raise ValueError('Unsuccessful parity checks')
    records = on['shadow_records']
    calls = [r['call'] for r in records]
    if calls != receipt['protocol']['shadow_calls'] or len(set(calls)) != len(calls):
        raise ValueError('Missing, duplicate or changed diagnostic selection')
    details = []
    for r in records:
        if set(r['candidates']) != {'official', 'scalar', 'shrink'}:
            raise ValueError('Missing candidate')
        row = {'call': r['call'], 'cfg_branch': r['cfg_branch'], 'ratios_to_official': {}}
        for mode in ('official', 'scalar', 'shrink'):
            c = r['candidates'][mode]
            for metric in METRICS:
                item = c[metric]
                if item['status'] != 'OK' or any(not math.isfinite(item[k]) or item[k] < 0 for k in ('mse','reference_mean_square')):
                    raise ValueError('Invalid diagnostic metric')
                if item['reference_mean_square'] != r['candidates']['official'][metric]['reference_mean_square']:
                    raise ValueError('Candidates did not use same truth reference')
            if mode != 'official':
                if any(step >= r['cache_counter'] for step in c['history']['anchor_steps']):
                    raise ValueError('Nonpast full anchor')
                row['ratios_to_official'][mode] = {
                    k: (c[k]['mse']/r['candidates']['official'][k]['mse']
                        if r['candidates']['official'][k]['mse'] > 0 else None) for k in METRICS}
        details.append(row)
    candidates = {}
    for mode in ('scalar', 'shrink'):
        info = {'fallback_count':sum(r['candidates'][mode]['reason'] != mode for r in records), 'metrics':{}}
        for metric in METRICS:
            values = [r['ratios_to_official'][mode][metric] for r in details]
            denom = sum(r['candidates']['official'][metric]['mse'] for r in records)
            num = sum(r['candidates'][mode][metric]['mse'] for r in records)
            info['metrics'][metric] = {'sum_mse_ratio': num/denom if denom > 0 else None,
                'improved_points':sum(x is not None and x < 1 for x in values),
                'points':len(values), 'median_point_ratio':median(values) if all(x is not None for x in values) else None,
                'range_point_ratio':[min(values),max(values)] if all(x is not None for x in values) else None}
        candidates[mode] = info
    # Descriptive engineering screen fixed before inspecting real candidate data.
    signals = [mode for mode, item in candidates.items()
               if item['fallback_count'] == 0
               and item['metrics']['velocity']['sum_mse_ratio'] is not None
               and item['metrics']['velocity']['sum_mse_ratio'] < 1
               and item['metrics']['velocity']['improved_points'] >= 3
               and item['metrics']['postwarp_residual']['sum_mse_ratio'] is not None
               and item['metrics']['postwarp_residual']['sum_mse_ratio'] < 1]
    status = 'MECHANISM_ONLY' if signals else 'NO_GAIN_IN_SCOPE' if all(
        c['fallback_count'] == 0 and c['metrics']['velocity']['sum_mse_ratio'] is not None
        and c['metrics']['velocity']['sum_mse_ratio'] >= 1 for c in candidates.values()) else 'INCONCLUSIVE'
    return {'status':status, 'candidate_screen_signals':signals, 'candidates':candidates,
            'points':details, 'supervised_gpu_hours':arms[0]['wall_seconds']/3600,
            'scope':'One engineering sample, four dependent selected states on official trajectory; not quality, closed-loop, clean latency, independent CAL or statistical confirmation.'}


def compare_recent_revision(initial, revised, artifact_check=None):
    """Verify the one-variable contrast and the unchanged shrink control."""
    expected = 'SAME_STATE_CANDIDATE_DIAGNOSTIC_PARITY_PASS_SINGLE_SAMPLE'
    for receipt in (initial, revised):
        if receipt.get('status') != expected or not all(v is True for v in receipt['checks'].values()):
            raise ValueError('Both contrast receipts must pass real-model gates')
        if len(receipt['runs']) != 2 or any(receipt['runs'][0][k] != receipt['runs'][1][k] for k in PARITY_FIELDS):
            raise ValueError('Within-run deployment parity failed')
    left, right = initial['runs'][0], revised['runs'][0]
    if any(left[k] != right[k] for k in PARITY_FIELDS if k != 'video_sha256') or left['sampling'] != right['sampling']:
        raise ValueError('Official trajectory changed across revision')
    videos_equal = left['video_sha256'] == right['video_sha256']
    decoded_equal = None
    if not videos_equal:
        if (not artifact_check or artifact_check.get('status') != 'CROSS_RUN_FULL_DECODE_CHECK'
                or len(artifact_check.get('runs',[])) != 2
                or [r['video_sha256'] for r in artifact_check['runs']] != [left['video_sha256'],right['video_sha256']]
                or any(r['frames'] != 93 or r['shape'] != [432,768,3] or not r['all_frames_same_shape'] for r in artifact_check['runs'])
                or not artifact_check['timestamps_identical']):
            raise ValueError('Cross-run video mismatch requires full decode audit; no video reproducibility claim')
        decoded_equal = artifact_check['decoded_rgb_identical']
    def setup(r):
        return {k:v for k,v in r['setup'].items() if k != 'output_dir'}
    if setup(initial) != setup(revised) or initial['sample'] != revised['sample']:
        raise ValueError('Inputs/runtime configuration changed')
    p, q = initial['protocol'], revised['protocol']
    if p['shadow_calls'] != q['shadow_calls'] or p['sample'] != q['sample']:
        raise ValueError('Diagnostic points changed')
    a,b=p['calibration_defaults'],q['calibration_defaults']
    if a['decay'] != .9 or b['decay'] != 0 or {k:v for k,v in a.items() if k!='decay'} != {k:v for k,v in b.items() if k!='decay'}:
        raise ValueError('Expected only decay .9 to 0 revision')
    before, after = initial['runs'][1]['shadow_records'], revised['runs'][1]['shadow_records']
    if [r['call'] for r in before] != [r['call'] for r in after]:
        raise ValueError('Changed/missing comparison records')
    for x,y in zip(before,after):
        for candidate in ('official','shrink'):
            for metric in METRICS:
                if x['candidates'][candidate][metric] != y['candidates'][candidate][metric]:
                    raise ValueError('Unchanged candidate control differs')
    ratios={}
    for metric in METRICS:
        num=sum(r['candidates']['scalar'][metric]['mse'] for r in after)
        den=sum(r['candidates']['scalar'][metric]['mse'] for r in before)
        ratios[metric]=num/den if den>0 else None
    return {'status':'MATCHED_ONE_VARIABLE_RECENT_PAIR_CONTRAST' if videos_equal else 'MATCHED_DENOISER_ONLY_RECENT_PAIR_CONTRAST',
            'encoded_video_identical':videos_equal, 'decoded_rgb_identical':decoded_equal,
            'artifact_reproducibility':'MATCHED' if videos_equal else 'POST_MODEL_VIDEO_MISMATCH_UNRESOLVED',
            'official_trajectory_identical':True,'shrink_scores_identical':True,
            'scalar_recent_over_initial_sum_mse_ratio':ratios,
            'scope':'One AV engineering sample; exact denoiser/cache trajectory and shrink control support numerical contrast only; downstream video mismatch, if present, remains unresolved. Not independent replication, video reproducibility, closed-loop or quality gain.'}
