"""Summarize only the independently captured, complete original E3 CPU chain.

No model, tensor, video, remote access, budget write, or new GPU execution.
Additional comparisons are explicitly exploratory; original24 stay intact.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = 'reports/wc_e3_complete64_terminal_r1_20261011_capture.json'
OUTPUT = 'reports/wc_e3_complete64_accepted_results_r1_20261012.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    content = (ROOT / CAPTURE).read_bytes()
    capture = json.loads(content)
    assert capture['status'] == 'E3_ORIGINAL_COMPLETE_SCOPE_TERMINAL_INDEPENDENTLY_CAPTURED'
    assert capture['complete_scope_post_chain_verified'] and capture['whole64_all_scored']
    assert capture['source_revision'] == '2e39cd31b593540130c08a394b92d9f5b5b5db42'
    assert capture['raw_valid_paths'] == capture['scored_pairs'] == 64
    assert capture['actual_original_reader_tensors'] == 2368
    assert capture['actual_frame_distances'] == 5952
    originals = {}
    for name, entry in capture['originals'].items():
        packed = (ROOT / entry['local_ref']).read_bytes()
        plain = gzip.decompress(packed)
        assert sha(packed) == entry['local_gzip_sha256']
        assert sha(plain) == entry['sha256'] and len(plain) == entry['bytes']
        originals[name] = json.loads(plain)
    scope = originals['scope']
    raw = originals['raw_audit']
    score = originals['score_result']
    assert len(raw['slots_all64']) == len(score['slots_all64']) == 64
    assert len(score['summary']['contrasts']) == len(capture['contrasts']) == 24
    assert score['summary']['contrasts'] == capture['contrasts']
    assert originals['post_CPU_supervisor']['budget_before_sha256'] == originals['post_CPU_supervisor']['budget_after_sha256']
    slots = {}
    raw_slots = {}
    per_slot = []
    for original, item in zip(raw['slots_all64'], score['slots_all64']):
        assert item['status'] == 'SCORED_FULL93' and item['compatible'] and item['scored']
        key = (item['strategy'], item['sample_name'], item['method'])
        assert key not in slots
        assert all(original[k] == item[k] for k in ('slot', 'strategy', 'sample_name', 'method'))
        slots[key] = item
        raw_slots[key] = original
        distances = item['score']['frame_distances']
        assert len(distances) == 93 and math.isclose(mean(distances), item['score']['mean_LPIPS'], rel_tol=1e-12, abs_tol=1e-12)
        cost = item['recorded_cost']
        actions = cost['actions']
        assert len(actions) == 36 and all(a in ('CC', 'PP', 'DD') for a in actions)
        p_step = None
        cc_after_p = []
        for step, action in enumerate(actions):
            if action == 'DD':
                p_step = None
            elif action == 'PP':
                p_step = step
            elif p_step is not None:
                cc_after_p.append({'step_zero_based': step, 'last_PP_step_zero_based': p_step,
                                   'updates_since_last_PP': step - p_step})
        per_slot.append({'slot': item['slot'], 'strategy': key[0], 'sample_name': key[1],
            'method': key[2], 'mean_LPIPS': mean(distances), 'recorded_cost': cost,
            'DD_pairs': actions.count('DD'), 'PP_pairs': actions.count('PP'), 'CC_pairs': actions.count('CC'),
            'CC_after_last_PP_before_next_DD': cc_after_p})
    def contrast(cs, cm, bs, bm):
        rows = []
        for name in scope['sample_names']:
            a, b = slots[(cs, name, cm)], slots[(bs, name, bm)]
            assert a['reference'] == b['reference'] and a['score']['pts'] == b['score']['pts']
            av, bv = [x['score']['mean_LPIPS'] for x in (a, b)]
            deltas = [y - x for x, y in zip(a['score']['frame_distances'], b['score']['frame_distances'])]
            rows.append({'sample_name': name, 'candidate_LPIPS': av, 'baseline_LPIPS': bv,
                'baseline_minus_candidate_LPIPS': mean(deltas),
                'relative_LPIPS_improvement_percent': 100 * mean(deltas) / bv if bv > 0 else None,
                'improved_frames': sum(x > 0 for x in deltas), 'degraded_frames': sum(x < 0 for x in deltas),
                'tied_frames': sum(x == 0 for x in deltas),
                'candidate_recorded_cost': a['recorded_cost'], 'baseline_recorded_cost': b['recorded_cost']})
        av, bv = [mean(x[k] for x in rows) for k in ('candidate_LPIPS', 'baseline_LPIPS')]
        relative = [x['relative_LPIPS_improvement_percent'] for x in rows]
        return {'candidate': [cs, cm], 'baseline': [bs, bm], 'registered_scenes': 4,
            'scene_equal_candidate_LPIPS': av, 'scene_equal_baseline_LPIPS': bv,
            'relative_improvement_of_scene_equal_mean_percent': 100 * (bv - av) / bv if bv > 0 else None,
            'scene_equal_mean_relative_improvement_percent': mean(relative) if all(x is not None for x in relative) else None,
            'median_scene_LPIPS_difference': median(x['baseline_minus_candidate_LPIPS'] for x in rows),
            'worst_scene_LPIPS_difference': min(x['baseline_minus_candidate_LPIPS'] for x in rows),
            'improved_scenes': sum(x['baseline_minus_candidate_LPIPS'] > 0 for x in rows),
            'degraded_scenes': sum(x['baseline_minus_candidate_LPIPS'] < 0 for x in rows),
            'tied_scenes': sum(x['baseline_minus_candidate_LPIPS'] == 0 for x in rows),
            'per_scene': rows, 'clean_speed_claim': False}
    contrasts = []
    for registered in capture['contrasts']:
        cs, cm = registered['candidate']; bs, bm = registered['baseline']
        entry = contrast(cs, cm, bs, bm)
        assert entry['improved_scenes'] == registered['improved_scenes']
        assert entry['degraded_scenes'] == registered['degraded_scenes']
        assert abs(mean(x['baseline_minus_candidate_LPIPS'] for x in entry['per_scene']) - registered['scene_equal_mean_LPIPS_difference']) < 1e-15
        entry['preregistered_contrast'] = True
        contrasts.append(entry)
    extra = []
    for strategy in scope['strategies']:
        for method in ('CPD', 'REF_CPD', 'A_CPD_W1_ONE_PHASE', 'A_CPD_BETA1_ONE_PHASE'):
            entry = contrast(strategy, method, strategy, 'SOURCE_RA')
            entry['preregistered_contrast'] = False
            entry['exploratory_reporting_comparison_not_new_confirmation'] = True
            extra.append(entry)
    groups = []
    controls = []
    for strategy in scope['strategies']:
        for method in scope['methods']:
            rows = [x for x in per_slot if x['strategy'] == strategy and x['method'] == method]
            groups.append({'strategy': strategy, 'method': method, 'scenes': 4,
                'scene_equal_mean_LPIPS': mean(x['mean_LPIPS'] for x in rows),
                'total_DD_pairs': sum(x['DD_pairs'] for x in rows),
                'total_PP_pairs': sum(x['PP_pairs'] for x in rows),
                'total_CC_pairs': sum(x['CC_pairs'] for x in rows),
                'extra_candidate_heads': sum(x['recorded_cost']['extra_candidate_heads'] for x in rows),
                'CC_after_last_PP_before_next_DD': sum(len(x['CC_after_last_PP_before_next_DD']) for x in rows),
                'instrumented_mean_pipeline_seconds': mean(x['recorded_cost']['instrumented_pipeline_wall_seconds'] for x in rows),
                'clean_speed_claim': False})
        for name in scope['sample_names']:
            off = slots[(strategy, name, 'A_CPD_OFF')]; cpd = slots[(strategy, name, 'CPD')]
            a, b = [raw_slots[(strategy, name, m)]['actual_vector_read']['file']['tensor_sha256'] for m in ('A_CPD_OFF', 'CPD')]
            controls.append({'strategy': strategy, 'sample_name': name,
                'CPD_OFF_all37_tensor_content_hashes_equal': a == b,
                'CPD_OFF_actions_equal': off['recorded_cost']['actions'] == cpd['recorded_cost']['actions'],
                'CPD_OFF_all93_distances_equal': off['score']['frame_distances'] == cpd['score']['frame_distances'],
                'DENSE_CONTROL_all93_LPIPS_zero': all(x == 0 for x in slots[(strategy, name, 'DENSE_CONTROL')]['score']['frame_distances'])})
    result = {'status': 'E3_ACCEPTED_COMPLETE64_ORIGINAL_CPU_RESULTS_RECONSTRUCTED',
        'capture_ref': CAPTURE, 'capture_sha256': sha(content), 'source_revision': capture['source_revision'],
        'registered_positions': 64, 'qualified_reuses': 10, 'fresh_paths': 54,
        'real_tensor_reads': 2368, 'full93_scored_pairs': 64, 'frame_distances': 5952,
        'groups': groups, 'all24_preregistered_contrasts': contrasts,
        'additional8_exploratory_RA_comparisons': extra, 'all8_control_positions': controls,
        'per_slot_all64': per_slot, 'billed_GPUh': capture['billed_GPUh'],
        'settled_ledger': capture['settled_ledger'], 'remaining_GPUh': capture['remaining_GPUh_at_settlement'],
        'new_GPU_submissions': 0, 'ledger_written': False, 'original_CPU_reader_rerun': False,
        'development_scenes': 4, 'seeds_per_scene': 1, 'frames_are_independent_samples': False,
        'two_source_rules_are_not8_independent_scenes': True, 'clean_speed_claim': False,
        'LPIPS_fidelity_not_semantic_or_physics_quality': True,
        'CPD_OFF_controls_all_equal': all(all(x[k] for k in ('CPD_OFF_all37_tensor_content_hashes_equal', 'CPD_OFF_actions_equal', 'CPD_OFF_all93_distances_equal')) for x in controls),
        'DENSE_CONTROL_all_zero': all(x['DENSE_CONTROL_all93_LPIPS_zero'] for x in controls)}
    destination = ROOT / OUTPUT
    assert not destination.exists()
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'full93_scored_pairs', 'CPD_OFF_controls_all_equal', 'DENSE_CONTROL_all_zero', 'remaining_GPUh')}))


if __name__ == '__main__':
    main()
