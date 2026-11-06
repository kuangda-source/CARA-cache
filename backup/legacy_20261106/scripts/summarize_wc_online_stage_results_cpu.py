#!/usr/bin/env python3
"""Bind all online-stage results and settled follow-up costs without GPU work."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(runner_path, audit_path, metrics_path, terminal_path, cost_path,
              previous_path):
    raw = gzip.decompress(runner_path.read_bytes())
    runner = json.loads(raw)
    raw_sha = hashlib.sha256(raw).hexdigest()
    audit, metrics, terminal, cost, previous = (
        json.loads(p.read_text()) for p in
        (audit_path, metrics_path, terminal_path, cost_path, previous_path))
    assert raw_sha == audit['receipt_sha256'] == terminal['receipt_sha256']
    assert metrics['input_audit_sha256'] == sha(audit_path)
    assert runner['status'] == 'EIGHT_ONLINE_STAGE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    assert audit['status'] == 'EIGHT_ONLINE_STAGE_ADAPTIVE_SOURCE_POLICY_VIDEO_AUDIT_PASS_NOT_QUALITY'
    assert metrics['status'] == 'TWO_EXPOSED_CAL_FOUR_ONLINE_STAGE_FIDELITY_DIAGNOSTICS_NOT_ACCEPTANCE'
    assert terminal['status'] == 'ONLINE_STAGE_SOURCE_ASSETS_FULL_COST_RELEASE_AUDIT_PASS_REQUIRES_EIGHT_OUTPUT_AUDIT'
    assert terminal['source_revision'] == audit['frozen_gpu_source']
    assert len(audit['files']) == runner['planned_output_files'] == 8
    assert len(metrics['pairs']) == 4
    assert terminal['original_pids_absent'] == [2758008, 2758025, 2758027]
    assert terminal['global_lock_free'] and not terminal['compute_after'].strip()
    assert audit['original_GPU_budget_unchanged_during_CPU']
    assert metrics['CPU_only'] and not metrics['new_GPU_submission']
    assert metrics['original_GPU_budget_unchanged_during_CPU']
    budget = terminal['budget']
    supervisor = terminal['supervisor']
    assert budget == supervisor['budget_after'] and supervisor['exit_code'] == 0
    assert budget['cap_gpu_hours'] == 12 and budget['gpu_jobs_launched'] == 43
    assert not any(k.endswith('_inflight') for k in budget)
    assert supervisor['reserved_seconds'] == 3600
    wall = terminal['gpu_wall_seconds']
    assert 0 < wall <= 3600 and math.isfinite(wall)
    assert math.isclose(budget['used_gpu_hours'],
                        supervisor['budget_before']['used_gpu_hours'] + wall / 3600,
                        rel_tol=0, abs_tol=1e-12)
    pairs = {(p['sample_name'], p['variant']): p for p in metrics['pairs']}
    assert len(pairs) == 4
    rows = []
    groups = audit['measurement_groups']
    requests = runner['measurements']['requests']
    assert len(groups) == len(requests) == 2
    for group, request in zip(groups, requests):
        name = group['sample_name']
        assert name == request['sample_name']
        baseline, *candidates = group['files']
        base_trace = request['phases'][0]['trace']
        assert len(base_trace) == 72
        for file, phase in zip(candidates, request['phases'][1:]):
            variant = file['variant']
            pair = pairs[(name, variant)]
            assert pair['baseline_sha256'] == baseline['sha256']
            assert pair['candidate_sha256'] == file['sha256']
            assert pair['whole_video']['frames'] == 93
            assert pair['whole_video']['transitions'] == 92
            trace = phase['trace']
            assert len(trace) == 72
            differences = []
            for ref, current in zip(base_trace, trace):
                call = ref['call']
                assert call == current['call']
                if ref['deep_executed'] != current['deep_executed']:
                    differences.append({'call': call, 'solver_step': (call + 1) // 2,
                                        'CFG_slot': (call - 1) % 2,
                                        'WC_deep': ref['deep_executed'],
                                        'candidate_deep': current['deep_executed']})
            provenance = file['provenance']
            events = phase['refresh_provenance']['events']
            reads = [e['call'] for e in events if e['action'] == 'cache'
                     and any(s['kind'] != 'dense' for s in e['references_read'])]
            assert reads == provenance['cache_calls_reading_approximate']
            assert sum(t['deep_executed'] for t in trace) == file['deep_CFG_calls']
            seconds = file['pipeline_wall_seconds']
            assert math.isfinite(seconds) and seconds > 0
            rows.append({'sample_name': name, 'variant': variant,
                         'baseline_video_sha256': baseline['sha256'],
                         'candidate_video_sha256': file['sha256'],
                         'baseline_pipeline_wall_seconds': baseline['pipeline_wall_seconds'],
                         'candidate_pipeline_wall_seconds': seconds,
                         'descriptive_WC_over_candidate': baseline['pipeline_wall_seconds'] / seconds,
                         'descriptive_wall_reduction_fraction': 1 - seconds / baseline['pipeline_wall_seconds'],
                         'baseline_deep_CFG_calls': baseline['deep_CFG_calls'],
                         'candidate_deep_CFG_calls': file['deep_CFG_calls'],
                         'S_CFG_calls': provenance['sparse_CFG_calls'],
                         'S_count': len(provenance['sparse_CFG_calls']),
                         'S_attention_operators': provenance['sparse_attention_operators'],
                         'window_eligible_per_CFG': provenance['window_eligible_per_CFG'],
                         'cache_calls_reading_approximate': reads,
                         'approximate_reads_after_stage_window': [c for c in reads if (c + 1) // 2 > 27],
                         'native_decision_differences_vs_WC': differences,
                         'whole_video': pair['whole_video']})
    # This checks an encoded output bridge, not equality of all internal states
    # between the old offline mask and the current online policy.
    human = next(r for r in rows if r['sample_name'] == 'human_199'
                 and r['variant'] == 'stage_every1')
    prior = previous['factorial_arms']['E0L0']
    assert human['candidate_video_sha256'] == prior['video_sha256']
    assert human['baseline_video_sha256'] == previous['baseline_video_sha256']
    assert human['S_CFG_calls'] == prior['sparse_CFG_calls']
    for k, value in human['whole_video'].items():
        assert value == prior[k]
    remaining = (12 - budget['used_gpu_hours']) * 3600
    followups = cost['cards'][1:]
    assert [c['planned_outputs'] for c in followups] == [14, 6]
    cards = []
    for c in followups:
        cap = c['proposed_cap_seconds']
        assert c['complete_planning_seconds'] <= cap
        cards.append({**c, 'selected': False, 'GPU_submitted': False,
                      'fits_settled_budget_with_15s_admission': cap + 15 <= remaining})
    total = sum(c['proposed_cap_seconds'] for c in cards)
    return {'status': 'ALL_EIGHT_ONLINE_STAGE_OUTPUTS_AUDITED_FOUR_CAL_DIAGNOSTICS_NOT_FRONTIER',
            'CPU_only': True, 'run_id': runner['scope']['run_id'],
            'card': runner['run_card'], 'source_revision': terminal['source_revision'],
            'receipt_sha256': raw_sha, 'planned_outputs': 8, 'audited_outputs': 8,
            'candidate_pairs': 4, 'rows': rows,
            'human_every1_encoded_bridge_to_offline_E0L0': {
                'video_sha256': human['candidate_video_sha256'],
                'baseline_SHA_S_calls_and_all_whole_video_metrics_equal': True,
                'internal_full_state_equivalence_claim': False},
            'GPU_wall_seconds': wall, 'GPU_hours': wall / 3600, 'budget': budget,
            'remaining_GPU_hours': remaining / 3600, 'remaining_seconds': remaining,
            'original_PIDs_lock_GPU_released': True,
            'followup_budget': {'cards': cards, 'remaining_proposed_caps_seconds': total,
                                'admission_margin_seconds': 15,
                                'both_caps_jointly_fit': total + 15 <= remaining,
                                'additional_seconds_for_both_caps': max(0, total + 15 - remaining),
                                'actual_refund_may_change_later_admission': True,
                                'reserved_seconds': 0},
            'next_GPU_card_selected': False, 'new_GPU_submission': False,
            'quality_acceptance': False, 'semantic_or_physics_acceptance': False,
            'quality_time_frontier_claim': False, 'independent_confirmation': False,
            'causal_refresh_value_labels': False, 'replicated_speed_claim': False,
            'next_action': 'CPU_PREPARE_NATIVE_FULL_FEWER_STEP_AND_TUNED_WC_FAIR_BASELINES_BEFORE_NEW_GPU_CARD',
            'candidate_for_fair_comparison': 'stage_every1_CAL_SELECTED_NOT_METHOD_ACCEPTANCE',
            'limits': [
                'Two exposed CAL inputs; all four candidates and failures remain in the denominator.',
                'Single ordered complete pipeline timings include necessary online overhead and first S; not stable speed.',
                'Reference is official WC, not Native. RGB fidelity and motion proxies do not establish semantics or physics.',
                'Fewer S can change later native full/cache decisions and degrade fidelity. No matched-cost causal attribution.',
                'Approximate sources can be read after the S window; no safe cache lifetime proven.',
                'Native/fewer-step complete entry and parity, tuned WC, independent CONF and automatic semantic/physics assessment remain incomplete.',
                'Future full14 and CONF6 caps do not fit jointly; re-admit after actual settlement without shrinking baselines or resetting budget.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runner', 'audit', 'metrics', 'terminal', 'cost', 'previous', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    paths = [args.runner, args.audit, args.metrics, args.terminal, args.cost, args.previous]
    result = summarize(*paths)
    result['input_files_sha256'] = {str(p): sha(p) for p in paths}
    result['summary_code_sha256'] = sha(Path(__file__))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in
                      ('status', 'rows', 'GPU_wall_seconds', 'remaining_GPU_hours', 'followup_budget')}))
