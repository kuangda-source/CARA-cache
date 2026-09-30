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
