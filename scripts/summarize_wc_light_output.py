#!/usr/bin/env python3
"""Combine immutable receipts; descriptive development results, no acceptance."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import statistics


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def summarize(root):
    names = {
        'terminal': 'wc_light_output_r1_terminal_20261004.json',
        'artifact_audit': 'wc_light_output_r1_audit_20261004.json',
        'metrics': 'wc_light_output_r1_metrics_20261004.json',
        'runner_gzip': 'wc_light_output_r1_runner_20261004.json.gz',
        'audit_CPU_control': 'wc_light_output_r1_audit_cpu_control_20261003.json',
        'earlier_debug_metrics': 'wc_full_output_r1_video_metrics_20261003.json',
    }
    inputs = {key: (root / 'reports' / name).read_bytes() for key, name in names.items()}
    terminal, audit, metrics, controls, old = [json.loads(inputs[k]) for k in
        ('terminal', 'artifact_audit', 'metrics', 'audit_CPU_control', 'earlier_debug_metrics')]
    raw = gzip.decompress(inputs['runner_gzip'])
    runner = json.loads(raw)
    assert terminal['receipt_sha256'] == audit['receipt_sha256'] == digest(raw)
    assert metrics['input_audit_sha256'] == digest(inputs['artifact_audit'])
    assert audit['audit_code_sha256'] == digest((root / 'scripts/audit_wc_light_output_receipts.py').read_bytes())
    assert controls['audit_code_sha256'] == audit['audit_code_sha256']
    assert controls['test_code_sha256'] == digest((root / 'tests/check_light_output_audit_cpu.py').read_bytes())
    assert terminal['terminal_analysis_code_sha256'] == digest((root / 'scripts/audit_wc_light_output_terminal.py').read_bytes())
    assert metrics['analysis_code_sha256'] == digest((root / 'scripts/analyze_wc_light_video_pairs_cpu.py').read_bytes())
    assert metrics['reused_metric_code_sha256'] == digest((root / 'scripts/analyze_wc_video_pairs_cpu.py').read_bytes())
    assert terminal['supervisor']['exit_code'] == 0
    assert terminal['original_pids_absent'] == [2701874, 2701892, 2701894]
    assert len(audit['files']) == len(terminal['existing_mp4_files']) == 10
    assert all(f['full93_decode'] for f in audit['files'])
    assert len(metrics['pairs']) == 4 and metrics['original_GPU_budget_unchanged_during_CPU']
    assert all(audit['nine_checks_recomputed'].values()) and all(audit['pipeline_checks_recomputed'].values())
    assert audit['state_components_per_checkpoint'] == [1216] * 5
    scenes = []
    for group, request in zip(audit['measurement_groups'], runner['measurements']['requests']):
        scene = group['sample_name']
        pairs = [p for p in metrics['pairs'] if p['sample_name'] == scene]
        assert len(pairs) == 2 and pairs[0]['whole_video'] == pairs[1]['whole_video']
        assert all(group['repeat_artifact_SHA_equal'].values())
        phases = request['phases']
        official = [p for p in phases if p['kind'] == 'official']
        candidate = [p for p in phases if p['kind'] == 'candidate']
        assert len(official) == len(candidate) == 2
        raw_times = {k: [p['pipeline_wall_seconds'] for p in phases if p['kind'] == k]
                     for k in ('official', 'candidate')}
        means = {k: statistics.mean(v) for k, v in raw_times.items()}
        assert means['official'] == group['official_mean_seconds']
        assert means['candidate'] == group['candidate_mean_seconds']
        changes = [i for i, (a, b) in enumerate(zip(official[0]['trace'], candidate[0]['trace']), 1)
                   if a['deep_executed'] != b['deep_executed']]
        encoded_matches = [p for p in old['pairs'] if p['sample_name'] == scene]
        assert len(encoded_matches) == 1
        assert pairs[0]['baseline_sha256'] == encoded_matches[0]['baseline_sha256']
        assert pairs[0]['candidate_sha256'] == encoded_matches[0]['candidate_sha256']
        scenes.append({'sample_name': scene, 'sequence': group['sequence'],
            'pipeline_seconds_all_repeats': raw_times, 'mean_pipeline_seconds': means,
            'mean_official_over_candidate': means['official'] / means['candidate'],
            'mean_time_reduction_percent': 100 * (1 - means['candidate'] / means['official']),
            'sample_stdev_seconds': {k: statistics.stdev(v) for k, v in raw_times.items()},
            'deep_CFG_calls': {k: [f['deep_CFG_calls'] for f in group['files'] if f['kind'] == k]
                               for k in ('official', 'candidate')},
            'changed_adaptive_decision_calls': changes,
            'sparse_attention_operators_per_candidate': [f['provenance']['sparse_attention_operators']
                for f in group['files'] if f['kind'] == 'candidate'],
            'approximate_cache_reads_per_candidate': [len(f['provenance']['cache_calls_reading_approximate'])
                for f in group['files'] if f['kind'] == 'candidate'],
            'repeat_artifact_SHA_equal': group['repeat_artifact_SHA_equal'],
            'encoded_quality_metrics_per_fixed_pair': pairs[0]['whole_video'],
            'artifact_SHA_equal_to_earlier_debug_pair': True,
            'host_substage_seconds_sum_is_not_CUDA_decomposition': True})
    budget = terminal['budget']
    assert budget['cap_gpu_hours'] == 12 and budget['gpu_jobs_launched'] == 38
    assert not any(k.endswith('_inflight') for k in budget)
    return {'status': 'TEN_OUTPUT_AUDITS_PASS_DESCRIPTIVE_SPEED_WITH_UNRESOLVED_HUMAN_FIDELITY',
        'run_card': runner['run_card'], 'source_revision': terminal['source_revision'],
        'planned_outputs': 10, 'completed_outputs': 10, 'deployment_measurements': 8,
        'all_measurement_repeats_included': True, 'DD_observer_timings_excluded': True,
        'DD_nine_and_final_pipeline_pass': True, 'DD_native_components_per_checkpoint': [1216] * 5,
        'first_sparse_pipeline_included': audit['first_sparse_use_preserved'],
        'scenes': scenes, 'gpu_wall_seconds': terminal['gpu_wall_seconds'],
        'this_job_gpu_hours': terminal['gpu_wall_seconds'] / 3600,
        'cumulative_gpu_hours': budget['used_gpu_hours'],
        'remaining_gpu_hours': budget['cap_gpu_hours'] - budget['used_gpu_hours'],
        'gpu_jobs_launched': budget['gpu_jobs_launched'], 'no_inflight_and_original_resources_released': True,
        'monitor_rows': terminal['gpu_monitor_rows'], 'peak_memory_mib': terminal['gpu_peak_memory_mib'],
        'runner_raw_bytes': len(raw), 'runner_raw_sha256': digest(raw),
        'input_receipts': {k: {'path': 'reports/' + names[k], 'sha256': digest(v)} for k, v in inputs.items()},
        'summary_code_sha256': digest(Path(__file__).read_bytes()),
        'quality_acceptance': False, 'independent_confirmation': False, 'quality_time_frontier_claim': False,
        'new_GPU_card_selected': False, 'training_started': False,
        'decision': 'Continue WC with CPU preparation of fidelity and adaptive-schedule controls; defer learned routing.',
        'limits': ['Two exposed CAL scenes; two same-seed repeats per arm are not independent quality observations.',
            'Measured same-host warm pipeline includes prepare, native generation, guardrails, decode, write and necessary provenance.',
            'Load95.916 seconds and DD diagnostics remain in the total fee, outside the eight measured pipelines.',
            'Host substage timings are unsynchronized and incomplete; do not sum them or attribute the gap to a specific module.',
            'Human38 versus35 deep CFG calls and9 changed decisions confound a pure sparse-kernel speed attribution.',
            'Official WC encoded video is the reference; no current matched native-full, fewer-step, tuned-WC frontier or CONF.',
            'SSIM/PSNR and frame-change ratios do not establish semantic or physical preservation.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = summarize(args.project)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'scenes': result['scenes'],
        'cumulative_gpu_hours': result['cumulative_gpu_hours']}))
