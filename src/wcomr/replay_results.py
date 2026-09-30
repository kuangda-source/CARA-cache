"""Receipt gates for frozen replay; no quality or clean speed classifier."""
import math

PARITY_KEYS = ['outcome', 'guardrail_events', 'forward_output_sha256', 'block_counts', 'trace',
               'cache_end_sha256', 'sampling', 'pipeline_events', 'decoder_calls',
               'video_sha256', 'decoded_rgb', 'flags_before', 'flags_after']


def strict_parity(reference, observed):
    checks = {key: reference[key] == observed[key] for key in PARITY_KEYS}
    checks['flags_restored'] = reference['flags_before'] == reference['flags_after'] == observed['flags_before'] == observed['flags_after']
    if not all(checks.values()):
        raise ValueError('Replay exact parity failed: '+str(checks))
    return checks


def validate_schedule_receipt(result, entry):
    if result['outcome'] == 'TEXT_REJECTED':
        if result['trace'] or result['forward_output_sha256'] or result['replay'] is not None:
            raise ValueError('Text rejection unexpectedly executed denoiser')
        return {'coverage': 'TEXT_REJECTED_NO_DENOISER'}
    schedule = entry['schedule']
    observed = result['trace']
    if observed != schedule or len(result['forward_output_sha256']) != len(schedule):
        raise ValueError('Measured replay trace/output count differs from frozen reference')
    counts = result['block_counts']
    full = sum(row['deep_executed'] for row in schedule)
    if counts != {'denoiser_calls': len(schedule), 'full_calls': full, 'skipped_deep_calls': len(schedule)-full}:
        raise ValueError('Replay measured deep-compute counts differ')
    replay = result['replay']
    if len(replay['records']) != len(schedule):
        raise ValueError('Replay controller count differs')
    for row, record in zip(schedule, replay['records']):
        if not record['execution_verified'] or any(record[key] != row[field] for key, field in
            [('call', 'call'), ('cache_counter_before', 'cache_counter_before'), ('planned_full', 'deep_executed')]):
            raise ValueError('Replay controller execution differs')
        pred = record['prediction']
        if pred is not None:
            history = pred['history']
            if any(step >= row['cache_counter_before'] for step in history['anchor_steps']):
                raise ValueError('Replay prediction used a current/future anchor')
            if any(not math.isfinite(history[key]) for key in ['numerator', 'denominator']):
                raise ValueError('Replay calibration history nonfinite')
            if pred['reason'] == 'scalar' and (len(history['anchor_steps']) < 2 or pred['beta'] is None or not math.isfinite(pred['beta'])):
                raise ValueError('Scalar prediction lacks valid past pair/beta')
    return {'coverage': 'FROZEN_SCHEDULE_VERIFIED', 'full': full, 'skip': len(schedule)-full}


def candidate_parity(off, on, entry):
    checks = strict_parity(off, on)
    checks['calibration_end'] = off['calibration_end_sha256'] == on['calibration_end_sha256']
    # Requests have distinct names but must carry identical numerical state.
    checks['replay_records'] = all(off['replay'][key] == on['replay'][key] for key in ['mode', 'calibration_params', 'records'])
    records = on['shadow_records']
    checks['selected_shadow_calls'] = [r['call'] for r in records] == entry['first_gate_shadow_calls']
    checks['finite_shadow'] = all(r['metrics'][kind]['status'] == 'OK' and all(
        value is None or math.isfinite(value) for key, value in r['metrics'][kind].items()
        if key not in ['status', 'groups']) for r in records for kind in ['residual', 'velocity'])
    validate_schedule_receipt(off, entry); validate_schedule_receipt(on, entry)
    if not all(checks.values()):
        raise ValueError('Candidate OFF/ON parity failed: '+str(checks))
    return checks


def summarize(receipt, partial=False, reference=None):
    if not partial and receipt['status'] != 'W1_REPLAY_ATTEMPTED_ALL_TECH_PASS':
        raise ValueError('Replay receipt is not complete')
    planned = receipt['protocol']['samples']
    if [c['name'] for c in receipt['cases']] != [c['name'] for c in planned[:len(receipt['cases'])]]:
        raise ValueError('Replay case order differs')
    if not partial and (len(receipt['cases']) != 8 or not all(receipt['gates'][key] for key in ['official_reference_pass', 'candidate_parity_pass'])):
        raise ValueError('Replay gates or sample coverage incomplete')
    if not partial:
        if reference is None:
            raise ValueError('Original CAL8 reference required to revalidate official gate')
        strict_parity(reference['cases'][0]['off'], receipt['official_gate'])
    rows = []
    for case, entry in zip(receipt['cases'], planned):
        if case['status'] != 'REPLAY_COMPLETED':
            if partial: continue
            raise ValueError('Incomplete replay sample')
        result = case['scalar_off']
        coverage = validate_schedule_receipt(result, entry)
        if result['replay'] and (result['replay']['mode'] != 'scalar' or result['replay']['calibration_params'] != receipt['protocol']['calibration_defaults']):
            raise ValueError('Candidate mode/parameters differ from frozen protocol')
        predictions = [r['prediction'] for r in result['replay']['records'] if r['prediction'] is not None] if result['replay'] else []
        rows.append({'name': case['name'], 'outcome': result['outcome'], 'coverage': coverage,
            'fallbacks': sum(p['reason'] != 'scalar' for p in predictions), 'scalar_applied_calls': sum(p['reason'] == 'scalar' for p in predictions),
            'natural_vs_frozen_disagreements': sum(r['natural_skip'] is not None and r['natural_skip'] == r['planned_full'] for r in result['replay']['records']) if result['replay'] else 0,
            'seconds_with_hashing': result['seconds_with_hashing_and_diagnostics'], 'video_difference': case.get('video_difference'),
            'peak_memory': result.get('peak_memory')})
    if not partial:
        first = receipt['cases'][0]
        candidate_parity(first['scalar_off'], first['scalar_on'], planned[0])
    return {'status': 'PARTIAL_REPLAY_NO_QUALITY_DECISION' if partial else 'FROZEN_REPLAY_TECH_PASS_QUALITY_UNASSESSED',
            'completed_candidates': len(rows), 'planned_candidates': 8,
            'accepted': sum(r['outcome'] == 'ACCEPTED' for r in rows),
            'text_rejected': sum(r['outcome'] == 'TEXT_REJECTED' for r in rows),
            'video_rejected': sum(r['outcome'] == 'VIDEO_REJECTED' for r in rows),
            'samples': rows, 'first_candidate_shadow_records': receipt['cases'][0].get('scalar_on', {}).get('shadow_records', []) if receipt['cases'] else [],
            'limitation': 'Own-trajectory frozen-schedule diagnostic only. Video distance is not quality/physics; hashing/shadow/cold-order timing is not clean deployment speed. Reusable CAL is not independent confirmation.'}
