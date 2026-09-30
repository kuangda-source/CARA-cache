"""Frozen CAL8 timing coverage. No statistical or quality acceptance claims."""
import hashlib
import math
import statistics
from contextlib import contextmanager
import time

ARMS = ['official', 'scalar']
FORBIDDEN = ['per_call_tensor_hash', 'pipeline_tensor_hash', 'shadow', 'profiler', 'full_tensor_dump']


def attempts(names):
    if len(names) != 8 or len(set(names)) != 8:
        raise ValueError('Original8 unique scenes required')
    ranked = sorted(names, key=lambda n: hashlib.sha256(('w1-clean-timing-v1/'+n).encode()).hexdigest())
    first = {name: ARMS[i % 2] for i, name in enumerate(ranked)}
    result = [{'id': 'warmup/'+arm, 'name': names[0], 'arm': arm, 'repeat': None, 'timed': False} for arm in ARMS]
    for repeat in range(3):
        order = names[repeat*3:] + names[:repeat*3]
        for name in order:
            lead = first[name] if repeat % 2 == 0 else ARMS[1-ARMS.index(first[name])]
            for arm in [lead, ARMS[1-ARMS.index(lead)]]:
                result.append({'id': 'r'+str(repeat)+'/'+name+'/'+arm, 'name': name,
                               'arm': arm, 'repeat': repeat, 'timed': True})
    return result


def validate_protocol(p, frozen):
    names = [s['name'] for s in frozen['samples']]
    if (p['samples'] != names or p['attempts'] != attempts(names) or p['repeats'] != 3
            or p['timed_attempts'] != 48 or p['warmup_attempts'] != 2
            or p['max_gpu_seconds'] != 14400 or p['minimum_project_cap_gpu_hours'] != 8
            or p['disabled_observers'] != FORBIDDEN or p['calibration_defaults'] != frozen['calibration_defaults']
            or p['decoder_policy'] != frozen['decoder_policy']
            or p['warmup_gate'] != 'Post-timer all93 decoded RGB hashes equal prior official/scalar first-scene artifacts'):
        raise ValueError('Frozen timing scope/configuration differs')


@contextmanager
def synchronized_timer(synchronize, measurement, clock=time.perf_counter):
    """Only the generation call belongs inside. Preflight/audit/flush stay outside."""
    synchronize()
    start = clock()
    try:
        yield
    finally:
        synchronize()
        measurement['end_to_end_seconds'] = clock()-start


def validate_attempt(row, expected, schedule):
    if row['attempt'] != expected or row['status'] != 'AUDITED':
        raise ValueError('Missing/reordered/incomplete attempt')
    seconds = row['end_to_end_seconds']
    if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Nonfinite/nonpositive timing')
    if row['disabled_observers'] != FORBIDDEN or row['flags_before'] != row['flags_after']:
        raise ValueError('Observer or backend policy drift')
    outcome = row['outcome']
    if outcome not in ['ACCEPTED', 'TEXT_REJECTED', 'VIDEO_REJECTED']:
        raise ValueError('Unknown outcome')
    guard = [{'stage': 'text', 'accepted': outcome != 'TEXT_REJECTED'}]
    if outcome != 'TEXT_REJECTED':
        guard.append({'stage': 'video', 'accepted': outcome == 'ACCEPTED'})
    if row['guardrail_events'] != guard:
        raise ValueError('Guardrail/outcome mismatch')
    if outcome == 'TEXT_REJECTED':
        if row['trace'] or row['replay'] is not None or row['decode_flags']:
            raise ValueError('Text rejection executed generation')
        expected_counts = {'denoiser_calls': 0, 'full_calls': 0, 'skipped_deep_calls': 0}
    else:
        if row['trace'] != schedule:
            raise ValueError('Measured full/skip schedule drift')
        full = sum(x['deep_executed'] for x in schedule)
        expected_counts = {'denoiser_calls': len(schedule), 'full_calls': full, 'skipped_deep_calls': len(schedule)-full}
        replay = row['replay']
        if replay['mode'] != expected['arm'] or len(replay['records']) != len(schedule):
            raise ValueError('Replay mode/coverage drift')
        for entry, record in zip(schedule, replay['records']):
            if not record['execution_verified'] or any(record[k] != entry[e] for k,e in
                    [('call','call'),('cache_counter_before','cache_counter_before'),('planned_full','deep_executed')]):
                raise ValueError('Controller/measured execution differs')
            prediction = record['prediction']
            if expected['arm'] == 'scalar' and not entry['deep_executed'] and prediction is None:
                raise ValueError('Scalar skip without recorded prediction')
            if prediction:
                history = prediction['history']
                if (any(step >= entry['cache_counter_before'] for step in history['anchor_steps'])
                        or any(not math.isfinite(history[k]) for k in ['numerator','denominator'])
                        or (prediction['beta'] is not None and not math.isfinite(prediction['beta']))):
                    raise ValueError('Invalid/future anchor history')
        flags = dict(row['flags_before'], cudnn_benchmark=False, cudnn_deterministic=True)
        if row['decode_flags'] != [flags]:
            raise ValueError('Missing or changed scoped decode policy')
    if row['block_counts'] != expected_counts:
        raise ValueError('Measured block counts differ')
    artifact = row['artifact']
    if outcome == 'ACCEPTED':
        if (not artifact or artifact['frames'] != 93 or artifact['shape'] != [432,768,3]
                or not artifact['finite'] or not artifact['timestamps_strictly_increasing']
                or len(artifact['sha256']) != 64 or len(artifact['decoded_rgb_sha256']) != 93):
            raise ValueError('Accepted video not fully audited')
    elif artifact is not None:
        raise ValueError('Rejected video saved')


def summarize(receipt, frozen, reference, prior):
    p = receipt['protocol'];validate_protocol(p, frozen)
    if receipt['status'] != 'W1_CLEAN_TIMING_ALL50_AUDITED' or len(receipt['rows']) != 50:
        raise ValueError('Full original8/50 audited coverage required')
    schedule = {x['name']: x['schedule'] for x in frozen['samples']}
    for row, expected in zip(receipt['rows'], p['attempts']):
        validate_attempt(row, expected, schedule[expected['name']])
        if row['replay'] and row['replay']['calibration_params'] != p['calibration_defaults']:
            raise ValueError('Calibration configuration differs')
    targets = {'official':reference['cases'][0]['off'], 'scalar':prior['cases'][0]['scalar_off']}
    for row in receipt['rows'][:2]:
        validate_warmup_artifact(row, targets[row['attempt']['arm']])
    rows = [x for x in receipt['rows'] if x['attempt']['timed']]
    scenes = []
    for name in p['samples']:
        by_arm = {a: [x for x in rows if x['attempt']['name']==name and x['attempt']['arm']==a] for a in ARMS}
        paired = []
        for repeat in range(3):
            pair = [next(x for x in by_arm[a] if x['attempt']['repeat']==repeat) for a in ARMS]
            paired.append({'repeat': repeat, 'outcomes': {a:x['outcome'] for a,x in zip(ARMS,pair)},
                           'accepted_pair_official_over_scalar_ratio': pair[0]['end_to_end_seconds']/pair[1]['end_to_end_seconds']
                           if all(x['outcome']=='ACCEPTED' for x in pair) else None})
        scenes.append({'name':name, 'arms': {a: {'attempts':3,'seconds':[x['end_to_end_seconds'] for x in by_arm[a]],
                          'median_all_attempt_seconds': statistics.median(x['end_to_end_seconds'] for x in by_arm[a]),
                          'outcomes':[x['outcome'] for x in by_arm[a]]} for a in ARMS}, 'paired_repeats':paired})
    return {'status':'ORIGINAL8_REPEATED_COST_ONLY_NOT_METHOD_ACCEPTANCE','planned_scenes':8,'timed_attempts':48,
            'warmup_attempts_excluded_from_timing_summary':2,'scenes':scenes,
            'outcome_counts':{a:{o:sum(x['attempt']['arm']==a and x['outcome']==o for x in rows)
                                for o in ['ACCEPTED','TEXT_REJECTED','VIDEO_REJECTED']} for a in ARMS},
            'scope':'Same CAL8/seed0/frozen schedule; descriptive repeated costs, no independent samples/quality, online reuse, tuned baseline frontier, CI or method acceptance. Warmups and outside-timer audit count in supervisor ledger.'}


def validate_warmup_artifact(row, original):
    if row['attempt']['timed'] or row['attempt']['repeat'] is not None:
        raise ValueError('Warmup identity differs')
    if row['outcome'] != original['outcome'] or row['outcome'] != 'ACCEPTED':
        raise ValueError('Warmup outcome differs from prior accepted gate scene')
    if row['artifact']['decoded_rgb_sha256'] != [x['sha256'] for x in original['decoded_rgb']]:
        raise ValueError('Removing diagnostic observers changed prior warmup RGB; technical review required')
