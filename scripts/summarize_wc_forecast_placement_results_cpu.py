#!/usr/bin/env python3
"""Join independent complete-card receipts and proxies without accepting quality."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def summarize(receipt, audit, metrics, terminal):
    assert receipt['status'] == 'SIX_FORECAST_PLACEMENT_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    assert receipt['scope']['run_id'] == 'wc-forecast-placement-human-r1'
    assert audit['status'] == 'SIX_FORECAST_PLACEMENT_SOURCE_POLICY_MASK_VIDEO_AUDIT_PASS_NOT_QUALITY'
    assert metrics['status'] == 'EXPOSED_HUMAN_THREE_FORECAST_PLACEMENT_ENCODED_PROXY_RESULTS_NOT_ACCEPTANCE'
    assert terminal['status'] == 'FORECAST_PLACEMENT_SOURCE_ASSETS_FULL_COST_RELEASE_AUDIT_PASS_REQUIRES_SIX_OUTPUT_AUDIT'
    assert terminal['source_revision'] == '395eae6dee91730cdb8f6f7997a1fba50913c2a1'
    assert terminal['supervisor']['exit_code'] == 0 and len(audit['files']) == 6
    assert terminal['receipt_sha256'] == audit['receipt_sha256']
    assert [f['variant'] for f in audit['measurement_files']] == ['fixed_D','legacy_SD','first_S_matched','minimum_footprint']
    assert [p['variant'] for p in metrics['pairs']] == ['legacy_SD','first_S_matched','minimum_footprint']
    assert len(receipt['measurement']['phases']) == 4
    rows = []
    legacy_mse = metrics['pairs'][0]['whole_video']['RGB_MSE_0to1']
    assert math.isfinite(legacy_mse) and legacy_mse >= 0
    for file, phase, pair, timing in zip(audit['measurement_files'][1:], receipt['measurement']['phases'][1:], metrics['pairs'], audit['descriptive_timings'][1:]):
        assert file['sha256'] == pair['candidate_sha256'] == phase['artifacts'][0]['sha256']
        assert pair['baseline_sha256'] == audit['measurement_files'][0]['sha256']
        proof = file['provenance']; whole = pair['whole_video']
        assert whole['frames'] == 93 and whole['transitions'] == 92
        assert proof['S_per_CFG'] == [6,5] and proof['sparse_attention_operators'] == 253
        assert all(math.isfinite(whole[k]) for k in ('RGB_MSE_0to1','mean_luma_SSIM_win7','temporal_difference_MSE_0to1','candidate_over_baseline_frame_change'))
        fractions = [op['selected_fraction'] for e in phase['refresh_provenance']['events'] for op in e.get('operator_metadata',[])]
        assert len(fractions) == 253 and all(math.isfinite(v) and 0 < v <= 1 for v in fractions)
        rows.append({'variant': file['variant'], 'video_sha256': file['sha256'],
                     'pipeline_wall_seconds': file['pipeline_wall_seconds'],
                     'descriptive_D_over_variant': timing['D_over_variant'],
                     'descriptive_wall_reduction_fraction': timing['wall_reduction_fraction'],
                     **proof, **whole,
                     'RGB_MSE_reduction_vs_legacy_fraction': (1-whole['RGB_MSE_0to1']/legacy_mse) if legacy_mse else None,
                     'mean_recorded_selected_fraction': sum(fractions)/len(fractions),
                     'nominal_operator_count_matched_actual_sparse_work_not_fixed': True})
    b = terminal['budget']; wall = terminal['gpu_wall_seconds']
    assert b['cap_gpu_hours'] == 12 and b['gpu_jobs_launched'] == 41
    assert not any(k.endswith('_inflight') for k in b) and b == terminal['supervisor']['budget_after']
    assert math.isclose(b['used_gpu_hours'], terminal['supervisor']['budget_before']['used_gpu_hours']+wall/3600, abs_tol=1e-10)
    assert all(f['deep_CFG_calls'] == 38 for f in audit['files'])
    return {'status': 'FORECAST_PLACEMENT_SIX_OUTPUTS_COST_RELEASE_AND_ENCODED_RESULTS_AUDITED_NOT_ACCEPTANCE',
            'run': receipt['scope']['run_id'], 'card': receipt['run_card'],
            'source_revision': terminal['source_revision'], 'receipt_sha256': terminal['receipt_sha256'],
            'baseline_pipeline_wall_seconds': audit['measurement_files'][0]['pipeline_wall_seconds'],
            'variants': rows, 'GPU_wall_seconds': wall, 'new_GPU_hours': wall/3600,
            'budget': b, 'remaining_GPU_hours': 12-b['used_gpu_hours'],
            'original_PIDs_lock_GPU_released': True, 'all_six_common_deep_CFG_calls': 38,
            'total_sparse_attention_operators': sum(r['sparse_attention_operators'] for r in rows),
            'total_cache_calls_reading_approximate': sum(len(r['cache_calls_reading_approximate']) for r in rows),
            'total_approximate_source_reads': sum(r['approximate_source_reads'] for r in rows),
            'historical_legacy_SD_video_exactly_reproduced': True,
            'quality_acceptance': False, 'independent_confirmation': False,
            'quality_time_frontier_claim': False, 'semantic_or_physics_acceptance': False,
            'online_policy': False, 'causal_refresh_value_labels': False,
            'next_GPU_card_selected': False,
            'limits': ['One exposed human seed0 and one run per variant; future-mask oracle positions, not an online policy.',
                       'Noise time, instantaneous S error, source reuse and sparse workload change together; no unique causal attribution.',
                       'Encoded official-WC-relative fidelity is not Native, semantic, physics or CONF acceptance.',
                       'Single fixed-order wall measurements are descriptive; no replicated or same-quality speed claim.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('receipt','audit','metrics','terminal','output'): p.add_argument('--'+n,type=Path,required=True)
    a = p.parse_args(); raw = gzip.decompress(a.receipt.read_bytes())
    receipt = json.loads(raw); audit = json.loads(a.audit.read_text())
    assert hashlib.sha256(raw).hexdigest() == audit['receipt_sha256']
    result = summarize(receipt,audit,json.loads(a.metrics.read_text()),json.loads(a.terminal.read_text()))
    result['input_files_sha256'] = {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in (a.receipt,a.audit,a.metrics,a.terminal)}
    result['summary_code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'variants':result['variants'],'budget':result['budget']}))
