"""Summarize F1 receipts without converting rejected or partial batches into passes."""
import math

TERMINAL_ARMS = {'ATTEMPTED_ALL_WITH_REJECTIONS', 'TECHNICAL_PASS_AWAITING_VIDEO_REVIEW'}


def positive(value):
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError('Expected finite positive measured seconds')
    return value


def summarize(native, worldcache, supervisor, expected):
    if len(set(expected)) != len(expected) or not expected:
        raise ValueError('Invalid frozen case list')
    observations = {}
    for mode, receipt in [('native', native), ('worldcache', worldcache)]:
        if receipt.get('mode') != mode or receipt.get('expected_samples') != expected:
            raise ValueError('Wrong arm or frozen case list')
        entries = {}
        for kind, items in [('ACCEPTED', receipt.get('samples', [])), ('REJECTED', receipt.get('rejections', []))]:
            for item in items:
                name = item['name']
                if name not in expected or name in entries:
                    raise ValueError('Unknown or duplicated outcome')
                outcome = kind if kind == 'ACCEPTED' else item['outcome']
                if outcome not in {'ACCEPTED', 'TEXT_REJECTED', 'VIDEO_REJECTED'}:
                    raise ValueError('Unknown rejection type')
                entries[name] = (outcome, item)
        if receipt.get('status') in TERMINAL_ARMS and len(entries) != len(expected):
            raise ValueError('Terminal arm is missing outcomes')
        if receipt.get('status') == 'TECHNICAL_PASS_AWAITING_VIDEO_REVIEW' and receipt.get('rejections'):
            raise ValueError('Pass receipt contains rejection')
        observations[mode] = entries
    # Compare the actual setup too: profile hash alone would miss runtime overrides.
    for field in ['input_sha256', 'profile_sha256', 'sampling_protocol_sha256',
                  'source_completion_commit', 'outcome_protocol', 'torch', 'cuda']:
        if field not in native or field not in worldcache or native[field] != worldcache[field]:
            raise ValueError('Unmatched provenance: ' + field)
    setups = []
    for receipt in [native, worldcache]:
        setup = dict(receipt['setup'])
        setup.pop('output_dir', None)
        if setup.pop('worldcache_enabled') != (receipt['mode'] == 'worldcache'):
            raise ValueError('Arm enable flag mismatch')
        setups.append(setup)
    if setups[0] != setups[1]:
        raise ValueError('Unmatched runtime setup')
    complete = (supervisor.get('status') == 'PAIR_EXITED_AWAITING_RECEIPT_AND_VIDEO_REVIEW'
                and [arm['mode'] for arm in supervisor.get('arms', [])] == ['native', 'worldcache']
                and all(arm['exit_code'] == 0 and arm.get('stop_reason') is None for arm in supervisor['arms'])
                and all(r.get('status') in TERMINAL_ARMS for r in [native, worldcache]))
    rows = []
    for name in expected:
        n = observations['native'].get(name, ('NOT_RECORDED', None))
        w = observations['worldcache'].get(name, ('NOT_RECORDED', None))
        row = {'name': name, 'native_outcome': n[0], 'worldcache_outcome': w[0]}
        if complete and n[0] == w[0] == 'ACCEPTED':
            if n[1]['index'] != w[1]['index'] or n[1]['cold_first_sample'] != w[1]['cold_first_sample']:
                raise ValueError('Unmatched sample order/cold label')
            row['cold_first_sample'] = n[1]['cold_first_sample']
            row['seconds'] = {}
            for mode, item in [('native', n[1]), ('worldcache', w[1])]:
                counts = item['block_counts']
                if counts['denoiser_calls'] != counts['full_calls'] + counts['skipped_deep_calls']:
                    raise ValueError('Inconsistent measured block counts')
                if mode == 'native' and counts['skipped_deep_calls']:
                    raise ValueError('Native skipped deep computation')
                row['seconds'][mode] = {'end_to_end': positive(item['end_to_end_seconds']),
                                       'denoising': positive(item['stages']['denoising']['seconds'])}
                row[mode + '_block_counts'] = counts
            row['native_over_worldcache'] = {
                metric: row['seconds']['native'][metric] / row['seconds']['worldcache'][metric]
                for metric in ['end_to_end', 'denoising']}
        rows.append(row)
    return {'status': 'COMPLETE_ATTEMPTS_REVIEW_PENDING' if complete else 'INCOMPLETE_NO_SPEED_CLAIM',
            'expected_cases_per_arm': len(expected),
            'counts': {mode: {'accepted': sum(v[0] == 'ACCEPTED' for v in entries.values()),
                              'rejected': sum(v[0].endswith('REJECTED') for v in entries.values()),
                              'not_recorded': len(expected) - len(entries)}
                       for mode, entries in observations.items()},
            'pairs': rows,
            'quality_status': 'NOT_REVIEWED',
            'limitations': ['Ratios describe only jointly accepted cases, not all prompts.',
                            'No quality-equivalent speedup established without full-video review.',
                            'Cold first sample remains separate; no aggregate hides rejected cases.',
                            'Receipt provenance does not independently verify video bytes or GPU exclusivity.']}
