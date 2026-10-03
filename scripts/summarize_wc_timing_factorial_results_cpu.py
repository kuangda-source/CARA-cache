#!/usr/bin/env python3
"""Join two audited cards and report signed early/late encoded-loss effects."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

spec = importlib.util.spec_from_file_location('old_summary', Path(__file__).with_name('summarize_wc_forecast_placement_results_cpu.py'))
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def signed_effects(losses):
    assert set(losses) == {'E0L0', 'E1L0', 'E0L1', 'E1L1'}
    assert all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in losses.values())
    d00, d10, d01, d11 = (losses[k] for k in ('E0L0', 'E1L0', 'E0L1', 'E1L1'))
    return {'early_at_L0': d10-d00, 'early_at_L1': d11-d01,
            'late_at_E0': d01-d00, 'late_at_E1': d11-d10,
            'interaction': d11-d10-d01+d00,
            'sign_convention': 'positive increases encoded loss; negative decreases it; no clipping'}


def summarize(receipt, audit, metrics, terminal, previous_receipt, previous_audit, previous_metrics, previous_terminal):
    previous = old.summarize(previous_receipt, previous_audit, previous_metrics, previous_terminal)
    assert previous['receipt_sha256'] == 'f6fb44d6b9f6133c23d7b7b291e22e53d60f55db14beb9117132b0e901d3d11c'
    assert receipt['status'] == 'SIX_TIMING_FACTORIAL_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    assert receipt['scope']['run_id'] == 'wc-timing-factorial-human-r1'
    assert audit['status'] == 'SIX_TIMING_FACTORIAL_SOURCE_POLICY_MASK_VIDEO_AUDIT_PASS_NOT_QUALITY'
    assert metrics['status'] == 'EXPOSED_HUMAN_LEGACY_AND_TWO_MISSING_TIMING_ENCODED_PROXY_RESULTS_NOT_ACCEPTANCE'
    assert terminal['status'] == 'TIMING_FACTORIAL_SOURCE_ASSETS_FULL_COST_RELEASE_AUDIT_PASS_REQUIRES_SIX_OUTPUT_AUDIT'
    assert terminal['source_revision'] == 'a86050cf9536a4431f9e77b711f54ab0a13feadf'
    assert terminal['supervisor']['exit_code'] == 0 and terminal['receipt_sha256'] == audit['receipt_sha256']
    assert len(audit['files']) == 6 and all(f['deep_CFG_calls'] == 38 for f in audit['files'])
    assert audit['fixed_mask'] == previous_audit['fixed_mask']
    assert audit['reference_context'][1:] == previous_audit['reference_context'][1:]
    assert receipt['wc_settings'] == previous_receipt['wc_settings']
    assert receipt['mode_setup'] == previous_receipt['mode_setup']
    for key in ('seed','policy','dense_fallback_layers','upstream_source_sha256',
                'request_lifecycle_source_sha256','unipc_source_sha256','cal_config_sha256',
                'f1_setup_sha256','shared_entry_RNG_across_control_and_measurement'):
        assert receipt['scope'][key] == previous_receipt['scope'][key]
    assert receipt['scope']['seed'] == 0
    assert receipt['scope']['shared_entry_RNG_across_control_and_measurement'] is True
    for key in ('sampling','flags_before'):
        assert receipt['dense_control']['phases'][0][key] == previous_receipt['dense_control']['phases'][0][key]
    assert metrics['metric_packages'] == previous_metrics['metric_packages']
    assert metrics['reused_pair_code_sha256'] == previous_metrics['reused_pair_code_sha256']
    assert metrics['reused_metric_code_sha256'] == previous_metrics['reused_metric_code_sha256']
    assert [f['variant'] for f in audit['measurement_files']] == ['fixed_D', 'legacy_SD', 'E0L0', 'E1L1']
    assert [p['variant'] for p in metrics['pairs']] == ['legacy_SD', 'E0L0', 'E1L1']
    assert len(receipt['measurement']['phases']) == 4
    assert audit['measurement_files'][0]['sha256'] == previous_audit['measurement_files'][0]['sha256']
    assert audit['measurement_files'][1]['sha256'] == previous_audit['measurement_files'][1]['sha256']
    assert metrics['pairs'][0]['whole_video'] == previous_metrics['pairs'][0]['whole_video']
    rows = []
    for file, phase, pair, timing, quota, operators in zip(audit['measurement_files'][1:], receipt['measurement']['phases'][1:], metrics['pairs'], audit['descriptive_timings'][1:], ([6,5], [5,4], [7,6]), (253,207,299)):
        assert file['sha256'] == pair['candidate_sha256'] == phase['artifacts'][0]['sha256']
        assert pair['baseline_sha256'] == audit['measurement_files'][0]['sha256']
        proof, whole = file['provenance'], pair['whole_video']
        assert whole['frames'] == 93 and whole['transitions'] == 92
        assert proof['S_per_CFG'] == quota and proof['sparse_attention_operators'] == operators
        assert all(math.isfinite(whole[k]) for k in ('RGB_MSE_0to1', 'mean_luma_SSIM_win7', 'temporal_difference_MSE_0to1', 'candidate_over_baseline_frame_change'))
        fractions = [op['selected_fraction'] for e in phase['refresh_provenance']['events'] for op in e.get('operator_metadata', [])]
        assert len(fractions) == operators and all(math.isfinite(v) and 0 < v <= 1 for v in fractions)
        rows.append({'variant': file['variant'], 'video_sha256': file['sha256'],
                     'pipeline_wall_seconds': file['pipeline_wall_seconds'], **proof, **whole,
                     'descriptive_D_over_variant': timing['D_over_variant'],
                     'descriptive_wall_reduction_fraction': timing['wall_reduction_fraction'],
                     'mean_recorded_selected_fraction': sum(fractions)/len(fractions)})
    b, wall = terminal['budget'], terminal['gpu_wall_seconds']
    assert b['cap_gpu_hours'] == 12 and b['gpu_jobs_launched'] == 42
    assert not any(k.endswith('_inflight') for k in b) and b == terminal['supervisor']['budget_after']
    assert math.isclose(b['used_gpu_hours'], terminal['supervisor']['budget_before']['used_gpu_hours']+wall/3600, abs_tol=1e-10)
    assert terminal['supervisor']['budget_before'] == previous_terminal['budget']
    arms = {k: dict(v, factor_arm=k, source_run=run) for k, v, run in (
        ('E0L0', rows[1], receipt['scope']['run_id']),
        ('E1L0', previous['variants'][1], previous['run']),
        ('E0L1', previous['variants'][2], previous['run']),
        ('E1L1', rows[2], receipt['scope']['run_id']))}
    common = {45,47,48,49,50,51,52,53,54}
    for key, additions in (('E0L0',set()), ('E1L0',{23,24}), ('E0L1',{55,58}), ('E1L1',{23,24,55,58})):
        assert set(arms[key]['sparse_CFG_calls']) == common | additions
        arms[key].pop('nominal_operator_count_matched_actual_sparse_work_not_fixed', None)
        arms[key]['S_count'] = sum(arms[key]['S_per_CFG'])
    effects = {metric: signed_effects({k: v[metric] for k,v in arms.items()}) for metric in ('RGB_MSE_0to1','temporal_difference_MSE_0to1')}
    effects['one_minus_mean_luma_SSIM_win7'] = signed_effects({k: 1-v['mean_luma_SSIM_win7'] for k,v in arms.items()})
    return {'status': 'TIMING_FACTORIAL_FOUR_ARMS_SOURCE_COST_AND_SIGNED_ENCODED_EFFECTS_AUDITED_NOT_ACCEPTANCE',
            'run': receipt['scope']['run_id'], 'card': receipt['run_card'],
            'source_revision': terminal['source_revision'], 'receipt_sha256': terminal['receipt_sha256'],
            'previous_receipt_sha256': previous['receipt_sha256'],
            'baseline_video_sha256': audit['measurement_files'][0]['sha256'],
            'baseline_pipeline_wall_seconds': audit['measurement_files'][0]['pipeline_wall_seconds'],
            'new_variants': rows, 'factorial_arms': arms, 'signed_loss_effects': effects,
            'GPU_wall_seconds': wall, 'new_GPU_hours': wall/3600,
            'budget': b, 'remaining_GPU_hours': 12-b['used_gpu_hours'],
            'original_PIDs_lock_GPU_released': True,
            'historical_D_and_legacy_SD_exactly_reproduced': True,
            'quality_acceptance': False, 'independent_confirmation': False,
            'quality_time_frontier_claim': False, 'semantic_or_physics_acceptance': False,
            'online_policy': False, 'causal_refresh_value_labels': False, 'next_GPU_card_selected': False,
            'limits': ['One exposed human seed0; four fixed-mask interventions including accumulated propagation.',
                       'Different S quotas9/11/11/13 and sparse workloads; no matched-cost effect or speed frontier.',
                       'Effects concern whole encoded outputs, not a unique instantaneous-error or cache-propagation decomposition.',
                       'Two prior arms reused after exact reference/legacy bridge, model, condition, mask and metric binding; no new independent CONF.',
                       'Native, fewer-step, tuned-WC and semantic/physics quality remain unmeasured here.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    names = ('receipt','audit','metrics','terminal','previous-receipt','previous-audit','previous-metrics','previous-terminal')
    for name in (*names, 'output'): p.add_argument('--'+name,type=Path,required=True)
    a = p.parse_args(); paths = [getattr(a,n.replace('-','_')) for n in names]
    payloads = [gzip.decompress(f.read_bytes()) if f.suffix == '.gz' else f.read_bytes() for f in paths]
    data = [json.loads(raw) for raw in payloads]
    for offset, expected in ((5,'78383f3b652cd5bcf1d673d66d50b976adbf91e6143e27360395f2b2c0a7bd7b'),
                             (6,'5cf181af1756864a837e2b6a99e0c5a95364f84c33663158d7cf067b9c13149b'),
                             (7,'bc3c23d69e03ae8259008ec8c6fb3cdd5d2ea3f6c2346c3d57c22ff008b53ea3')):
        assert hashlib.sha256(payloads[offset]).hexdigest() == expected
    for offset in (0,4):
        assert hashlib.sha256(payloads[offset]).hexdigest() == data[offset+1]['receipt_sha256']
        assert hashlib.sha256(payloads[offset+1]).hexdigest() == data[offset+2]['input_audit_sha256']
    r = summarize(*data)
    r['input_files_sha256'] = {str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
    r['summary_code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    r['reused_previous_summary_code_sha256'] = hashlib.sha256(Path(__file__).with_name('summarize_wc_forecast_placement_results_cpu.py').read_bytes()).hexdigest()
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':r['status'], 'effects':r['signed_loss_effects'], 'budget':r['budget']}))
