"""Read-only aggregation controls against original GPU and CPU receipts."""
import argparse
import copy
import gzip
import importlib.util
import json
from pathlib import Path

from wcomr.rv0_small_partial import partial_plan
from wcomr.rv0_two_point_summary import ORIGINAL, summarize, physical_accounting, validate_scores, historical_masks


def run(root):
    spec = importlib.util.spec_from_file_location('summary_cli', root/'scripts/summarize_wc_w3_two_points_cpu.py')
    cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
    first = cli.load_bundle(root/'configs/wc_w3_small_cd_approved_r1_20261005.json',
        root/'reports/wc_w3_small_cd_runner_20261005.json.gz',
        root/'reports/wc_w3_small_cd_failed_terminal_audit_20261005.json',
        root/'reports/wc_w3_small_cd_failed_card_lpips_cpu_20261005.json',
        root/'reports/wc_w3_small_cd_failed_card_lpips_cpu_audit_20261005.json',
        root/'reports/wc_w3_small_cd_supervisor_20261005.json',
        root/'reports/wc_w3_small_cd_original_receipts_20261005.json')
    result = summarize(first)
    assert result['original_scientific_denominator'] == ORIGINAL
    assert result['actual_complete_scientific_points'] == 1 and result['whole_requested_scene_mean_C_minus_D'] is None
    assert all(result['points'][1][k] is None for k in ['LPIPS_C', 'LPIPS_D', 'LPIPS_C_minus_D'])
    assert result['original_GPU_card_accepted'] is False
    assert result['points'][0]['official_WC_target_action'] == 'D'
    assert result['physical_attempt_accounting'] == {
        'planned_parents': 2, 'planned_suffixes': 12, 'planned_new_videos': 8,
        'started_parents': 2, 'started_suffixes': 7, 'completed_suffixes': 6,
        'audited_new_videos': 4, 'total_actual_GPU_wall_seconds_including_failed_card': 3872.2579837469384}
    # These hashes deliberately differ: GPU execution and CPU scoring have separate supervisors.
    assert first['score_audit']['supervisor_original_sha256'] != first['sha256']['supervisor']
    refused = []
    def reject(name, action):
        try: action()
        except (ValueError, KeyError, AssertionError, TypeError, ZeroDivisionError): refused.append(name)
        else: raise AssertionError('Invalid aggregation accepted: '+name)
    for name, change in [
        ('original_scientific_denominator_shrunk', lambda b: b['score']['original_denominator'].update(signed_diagnostics=1)),
        ('original_timeout_reclassified', lambda b: b['supervisor'].update(status='EXITED_REQUIRES_RESULT_AUDIT', exit_code=0)),
        ('failure_cost_zero', lambda b: (b['supervisor'].update(wall_seconds=0), b['terminal'].update(gpu_wall_seconds=0))),
        ('failure_cost_modified', lambda b: b['supervisor'].update(wall_seconds=1)),
        ('failure_budget_hidden', lambda b: (b['terminal']['budget'].update(used_gpu_hours=11), b['supervisor']['budget_after'].update(used_gpu_hours=11))),
        ('original_physical_scope_shrunk', lambda b: b['supervisor'].update(planned_parent_phases=1)),
        ('GPU_supervisor_replaced_by_CPU_supervisor', lambda b: b['originals']['files']['supervisor'].update(original_sha256=b['score_audit']['supervisor_original_sha256'])),
        ('GPU_original_runner_wrong_digest', lambda b: b['originals']['files']['runner'].update(original_sha256='f'*64)),
        ('GPU_original_runner_wrong_bytes', lambda b: b['originals']['files']['runner'].update(original_bytes=1)),
        ('GPU_original_wrong_run_path', lambda b: b['originals']['files']['supervisor'].update(original_path='/unbound/supervisor.json')),
        ('partial_93_frame_score', lambda b: b['score']['pairs'][0]['score']['frame_distances'].pop()),
        ('mean_not_raw93_average', lambda b: b['score']['pairs'][0]['score'].update(mean_LPIPS=0)),
        ('nonfinite_frame_score', lambda b: b['score']['pairs'][0]['score']['frame_distances'].__setitem__(0, float('nan'))),
        ('signed_benefit_changed', lambda b: b['score']['signed_diagnostics'][0].update(LPIPS_C_minus_D=0)),
        ('metric_protocol_changed', lambda b: b['score']['protocol'].update(resize_crop_subsample=True)),
        ('duplicate_PTS', lambda b: b['score']['pairs'][0]['score']['pts'].__setitem__(1, [0, '1/16384'])),
        ('scored_reference_wrong_digest', lambda b: b['score']['pairs'][0]['reference'].update(sha256='f'*64)),
        ('video_not_fully_decoded', lambda b: b['terminal']['videos'][0].update(full93_decode=False)),
        ('current_deep_truth_leak', lambda b: b['receipt']['requests'][0]['children'][2]['record']['action_report']['suffix_events'][0].update(current_deep_truth_used=True)),
        ('incomplete_repeat', lambda b: b['receipt']['requests'][0]['children'].pop()),
        ('first_CPU_fixture', lambda b: b.update(CPU_fixture=True))]:
        broken = copy.deepcopy(first); change(broken)
        reject(name, lambda: summarize(broken))
    raw = json.loads(gzip.decompress((root/'reports/wc_w3_small_human_core_raw_cpu_20261005.json.gz').read_bytes()))
    toy = next(c['receipt'] for c in raw['checks'] if c['failure'] is None)
    draft = json.loads((root/'configs/wc_w3_small_human_production_r2_draft.json').read_text())
    human = {'config': draft, 'receipt': toy, 'terminal': {}, 'score': {}}
    reject('CPU_Human_fixture_as_real_point', lambda: summarize(first, {**human, 'CPU_fixture': True}))
    reject('CPU_Human_deep2_without_fixture_tag', lambda: summarize(first, human))
    historical = json.loads(gzip.decompress((root/'reports/wc_fair_cal_r1_runner_20261004.json.gz').read_bytes()))
    masks = historical_masks(first['config'], historical)
    assert [m['historical_official_WC_target_action'] for m in masks] == ['D', 'C']
    assert [m['historical_suffix_full_calls_per_CFG'] for m in masks] == [[8, 7], [10, 8]]
    for name, change in [
        ('historical_mask_truncated', lambda h: h['measurements']['requests'][1]['phases'][3]['trace'].pop()),
        ('historical_CFG_call_order_changed', lambda h: h['measurements']['requests'][1]['phases'][3]['trace'][45].update(call=45)),
        ('historical_horizon_reset_removed', lambda h: h['measurements']['requests'][1]['phases'][3]['trace'][70].update(cache_counter_before=70)),
        ('historical_video_bridge_changed', lambda h: h['measurements']['requests'][1]['phases'][3]['artifacts'][0].update(sha256='f'*64)),
        ('historical_grid_changed', lambda h: h['measurements']['requests'][1]['phases'][3]['sampling']['timesteps'].__setitem__(22, 999))]:
        broken = copy.deepcopy(historical); change(broken)
        reject(name, lambda: historical_masks(first['config'], broken))
    # Pure arithmetic control; synthetic scores are never saved as scientific points.
    plan = partial_plan(first['receipt'], first['config'])
    negative = copy.deepcopy(first['score']); metric = negative['pairs'][0]['score']
    metric['frame_distances'] = [v/2 for v in negative['pairs'][1]['score']['frame_distances']]
    metric['mean_LPIPS'] = sum(metric['frame_distances'])/93
    signed = metric['mean_LPIPS']-negative['pairs'][1]['score']['mean_LPIPS']
    negative['signed_diagnostics'][0]['LPIPS_C_minus_D'] = signed
    assert validate_scores(negative, plan['pairs'], first['terminal'])['LPIPS_C_minus_D'] == signed < 0
    # Hypothetical bookkeeping only, not a Human completion or measured GPU cost.
    hypothetical = physical_accounting(result['cards_and_failure_costs']+[
        {'planned_attempts': {'parents': 1, 'suffixes': 6, 'new_videos': 4},
         'started_parents': 1, 'started_suffixes': 6, 'completed_suffixes': 6,
         'audited_new_videos': 4, 'actual_GPU_wall_seconds': 4500}])
    assert (hypothetical['planned_parents'], hypothetical['planned_suffixes'], hypothetical['planned_new_videos']) == (3, 18, 12)
    assert (hypothetical['started_parents'], hypothetical['started_suffixes'], hypothetical['completed_suffixes'], hypothetical['audited_new_videos']) == (3, 13, 12, 8)
    assert hypothetical['total_actual_GPU_wall_seconds_including_failed_card'] == 3872.2579837469384+4500
    return {'status': 'TWO_POINT_AGGREGATION_ORIGINAL_READONLY_CPU_CONTROLS_PASS_NOT_NEW_GPU',
        'refusal_count': len(refused), 'refusals': refused, 'actual_real_points': 1,
        'whole_scene_mean_missing_until_real_Human': True, 'original_failed_cost_reconstructed': True,
        'GPU_and_CPU_supervisors_bound_separately': True, 'synthetic_negative_sign_control': True,
        'historical_actions_only': ['D', 'C'], 'historical_full_per_CFG_only': [[8, 7], [10, 8]],
        'hypothetical_cross_card_counts_only': {'planned': [3, 18, 12], 'actual_if_complete': [3, 13, 12, 8]},
        'future_Human_GPU_acceptance_not_executed_or_proven': True, 'GPU_submissions': 0, 'ledger_written': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(run(args.root.resolve())))
