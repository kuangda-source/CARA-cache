"""Descriptive CAL alignment only; retain old metrics, rejection and missing rows."""
import hashlib
import json
from pathlib import Path
import statistics

paths = {
    'scores': 'reports/wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json',
    'independent_audit': 'reports/wc_w1_native_reference_final_original_native_audit_20261006.json',
    'mechanism': 'reports/w1d_cal8_r1_summary.json',
    'imaging': 'reports/w1_imaging_r1_runner.json',
    'VQA': 'reports/w1_vqa_r1_summary.json',
    'old_two_LPIPS': 'reports/wc_existing_fair_w1_lpips_summary_20261004.json',
}
data = {k: json.loads(Path(p).read_text()) for k, p in paths.items()}
scores = data['scores']
summary = scores['summary']
assert data['independent_audit']['independent_recomputed_per_scene'] == summary['per_scene']
mechanism = {r['name']: r for r in data['mechanism']['samples']}
imaging = {r['name']: r for r in data['imaging']['pairs']}
vqa = {r['name']: r for r in data['VQA']['samples']}
old_lpips = {r['sample']: r for r in data['old_two_LPIPS']['W1']}
endpoint = {r['scene']: r for r in summary['per_scene']}
rows = []
for row in scores['reference_plan']['rows']:
    name = row['scene']
    local = mechanism[name]['candidates']['scalar']['metrics']
    result = {**row, 'mechanism_velocity_MSE_ratio': local['velocity']['sum_mse_ratio'],
        'mechanism_postwarp_MSE_ratio': local['postwarp_residual']['sum_mse_ratio'],
        'MUSIQ_candidate_minus_WC': imaging[name].get('delta'),
        'development_VQA_candidate_minus_WC': vqa[name].get('delta'),
        'LPIPS': endpoint.get(name), 'missing_not_zero': True}
    if name in endpoint:
        pairs = [p for p in scores['pairs'] if p['scene'] == name]
        assert imaging[name]['status'] == 'SCORED'
        assert imaging[name]['reference']['video_sha256'] == pairs[0]['candidate']['sha256']
        assert imaging[name]['candidate']['video_sha256'] == pairs[1]['candidate']['sha256']
        result['same_WC_W1_artifact_SHA256_as_prior_MUSIQ'] = True
    if name in old_lpips:
        result['old_two_LPIPS_recomputed_difference'] = {
            key: endpoint[name][key] - old_lpips[name][key] for key in ['WC_LPIPS', 'W1_LPIPS']}
    rows.append(result)
available = list(endpoint.values())
mean_wc = statistics.mean(r['WC_LPIPS'] for r in available)
mean_w1 = statistics.mean(r['W1_LPIPS'] for r in available)
result = {
    'status': 'W1_FULL_CAL_NATIVE_FIDELITY_AND_OLD_METRIC_ALIGNMENT_DESCRIPTIVE_NOT_CONF',
    'input_sha256': {key: hashlib.sha256(Path(path).read_bytes()).hexdigest() for key, path in paths.items()},
    'analysis_wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'rows': rows, 'original_denominator': [8, 7, 1], 'matched_scenes': len(available),
    'equal_scene_mean_WC_LPIPS': mean_wc, 'equal_scene_mean_W1_LPIPS': mean_w1,
    'reduction_of_equal_scene_mean_LPIPS_percent': 100 * (mean_wc - mean_w1) / mean_wc,
    'equal_scene_mean_of_relative_reductions_percent': statistics.mean(
        r['relative_improvement_percent'] for r in available),
    'equal_scene_median_relative_reduction_percent': statistics.median(
        r['relative_improvement_percent'] for r in available),
    'improved_degraded_tied_scenes': [summary['improved_scenes'], summary['degraded_scenes'], summary['tied_scenes']],
    'old_MUSIQ_3_up_4_down_and_VQA_6_tie_1_down_retained': True,
    'endpoint_or_speed_or_physics_or_independent_confirmation_threshold_added': False,
    'no_hypothesis_registered_after_seeing_results_as_if_preregistered': True,
    'GPU_submissions': 0, 'human_review_requested': False,
}
target = Path('reports/wc_w1_native_reference_metric_alignment_20261006.json')
assert not target.exists(), 'Preserve original descriptive analysis'
target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps({key: result[key] for key in ['status', 'matched_scenes',
    'equal_scene_mean_WC_LPIPS', 'equal_scene_mean_W1_LPIPS',
    'reduction_of_equal_scene_mean_LPIPS_percent', 'improved_degraded_tied_scenes']}))
