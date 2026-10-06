"""Post-result exploration of existing fixed-schedule logs; no new data or gate."""
import hashlib
import json
import math
from pathlib import Path
import statistics

paths = {
    'replay': 'reports/w1_replay_r1_runner.json',
    'old_summary': 'reports/w1_replay_r1_summary.json',
    'new_native': 'reports/wc_w1_native_reference_runner_20261006.json',
    'new_scores': 'reports/wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json',
}
data = {k: json.loads(Path(p).read_text()) for k, p in paths.items()}
old = {r['name']: r for r in data['old_summary']['samples']}
new = {r['scene']: r for r in data['new_scores']['summary']['per_scene']}
rows = []
for case in data['replay']['cases']:
    name = case['name']
    observed = case['scalar_off']
    records = observed['replay']['records']
    clip = observed['replay']['calibration_params']['clip']
    values = [r['prediction']['beta'] for r in records
              if r['prediction'] and r['prediction']['reason'] == 'scalar']
    assert all(math.isfinite(v) for v in values)
    assert len(records) == len(observed['trace']) == 72
    assert all(r['execution_verified'] for r in records)
    assert observed['flags_before'] == observed['flags_after'] == data['new_native']['backend_flags']
    for record in records:
        prediction = record['prediction']
        if prediction:
            assert all(s < record['cache_counter_before'] for s in prediction['history']['anchor_steps'])
    forced_reuse = [r['call'] for r in records if r['planned_full'] is False and r['natural_skip'] is False]
    forced_full = [r['call'] for r in records if r['planned_full'] is True and r['natural_skip'] is True]
    assert len(forced_reuse) + len(forced_full) == old[name]['natural_vs_frozen_disagreements']
    assert len(values) == old[name]['scalar_applied_calls'] and old[name]['fallbacks'] == 0
    rows.append({'scene': name, 'W1_outcome': observed['outcome'], 'original_coverage': old[name]['coverage'],
        'scalar_applied_calls': len(values), 'beta_min': min(values), 'beta_median': statistics.median(values),
        'beta_max': max(values), 'beta_at_frozen_clip_count': sum(abs(v) == clip for v in values),
        'frozen_clip': clip, 'forced_reuse_while_natural_would_full_calls': forced_reuse,
        'forced_full_while_natural_would_reuse_calls': forced_full,
        'natural_vs_frozen_disagreements': len(forced_reuse) + len(forced_full),
        'past_anchor_and_backend_flags_checks_pass': True, 'full93_LPIPS': new.get(name),
        'previous_WC_W1_encoded_RGB_motion_proxy': old[name].get('video_difference'),
        'motion_proxy_is_not_Native_motion_or_physics_quality': True})
result = {'status': 'EXISTING_W1_FIXED_SCHEDULE_CONDITIONS_POST_RESULT_EXPLORATORY_NOT_CAUSAL',
    'source_sha256': {key: hashlib.sha256(Path(path).read_bytes()).hexdigest() for key, path in paths.items()},
    'analysis_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'original_denominator': [8, 7, 1], 'rows': rows,
    'all_original_past_anchor_flags_72_execution_records_checks_pass': True,
    'old_failed_or_rejected_rows_retained': True, 'new_fallback_threshold_fitted': False,
    'clip_hit_does_not_uniquely_explain_fidelity_loss': True,
    'no_new_state_drift_magnitude_or_teacher_MSE_was_measured': True,
    'GPU_submissions': 0, 'CPU_video_or_LPIPS_repeated': False, 'human_review_requested': False}
target = Path('reports/wc_w1_existing_replay_conditions_exploratory_20261006.json')
assert not target.exists(), 'Preserve original exploratory analysis'
target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps({'status': result['status'], 'original_rows': len(rows),
    'all_past_anchor_flags_72_record_checks_pass': True,
    'per_scene_conditions': [{k: r[k] for k in ['scene', 'beta_at_frozen_clip_count',
        'natural_vs_frozen_disagreements']} for r in rows]}))
