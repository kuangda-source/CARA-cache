#!/usr/bin/env python3
"""Price complete diagnostic controls and select swaps from audited parent masks."""
import gzip
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sha = lambda name: hashlib.sha256((root/name).read_bytes()).hexdigest()
fair = json.loads(gzip.decompress((root/'reports/wc_fair_cal_r1_runner_20261004.json.gz').read_bytes()))
restore = json.loads((root/'reports/wc_rv0_restore_r1_summary_20261004.json').read_text())
runner = json.loads((root/'reports/wc_rv0_restore_r1_runner_20261004.json').read_text())
summary = json.loads((root/'reports/wc_fair_cal_r1_summary_20261004.json').read_text())
budget = json.loads((root/'reports/budget.json').read_text())
selected = []
for request in fair['measurements']['requests']:
    phase = next(p for p in request['phases'] if p['workpoint']['name'] == 'wc006')
    trace = phase['trace']
    assert [r['call'] for r in trace] == list(range(1, 73))
    mask = {row['call']: 'D' if row['deep_executed'] else 'C' for row in trace}
    counts = [sum(v == 'D' for c, v in mask.items() if (c-1) % 2 == slot) for slot in [0, 1]]
    for slot in [0, 1]:
        candidates = []
        for n in range(45+slot, 69, 2):
            if mask[n] != 'C': continue
            for m in range(n+2, 69, 2):
                if mask[m] != 'D': continue
                swapped = dict(mask); swapped[n] = 'D'; swapped[m] = 'C'
                changed = [c for c in mask if mask[c] != swapped[c]]
                new_counts = [sum(v == 'D' for c, v in swapped.items() if (c-1) % 2 == b) for b in [0, 1]]
                assert changed == [n, m] and counts == new_counts
                assert all(mask[c] == swapped[c] for c in list(range(1, 45))+[69, 70, 71, 72])
                candidates.append((n, m))
        if candidates:
            n, m = candidates[0]
            selected.append({'sample': request['sample_name'], 'cfg_slot': slot,
                'from_cache_call_n': n, 'donor_full_call_m': m,
                'n_solver_step': (n+1)//2, 'm_solver_step': (m+1)//2,
                'parent_full_CFG_counts': counts, 'swapped_full_CFG_counts': counts,
                'parent_mask': [mask[c] for c in range(1,73)],
                'selection_rule': 'Earliest parent C, then nearest later parent D in same CFG slot, calls45..68 only',
                'candidate_pairs_in_parent_mask': len(candidates),
                'selection_reads_video_score_or_local_error': False,
                'parent_mask_static_check': True,
                'branch_own_state_legality_checked': False,
                'fixed_mask_CPU_router_implemented': False,
                'protected_actions_may_not_be_overridden_to_force_equality': True})
assert len(selected) == 4
load = runner['load_seconds']
parent = max(r['parent_pipeline_including_diagnostics_wall_seconds']-
             sum(s['inclusive_wall_seconds'] for s in r['suffixes']) for r in restore['rows'])
suffix = max(s['inclusive_wall_seconds'] for r in restore['rows'] for s in r['suffixes'])
native = max(r['pipeline_wall_seconds'] for r in summary['rows'] if r['variant']=='native35')
# New proposal; no edits to original8/24/18 source or config. Two parents, OFF/OFF+C/D/D/C per scene.
components = {'loading': load, 'two_diagnostic_parent_only': 2*parent,
              'twelve_unchanged_suffix_proxies': 12*suffix,
              'six_unique_child_decode_encode_allowance_unmeasured': 180,
              'new_bookkeeping_allowance_unmeasured': 75}
subtotal = sum(components.values()); nominal = subtotal*1.2+30
# Entire measured Native35 pipeline per short suffix plus restore allowance is a stress proxy, not a theorem.
stress_components = dict(components)
stress_components['twelve_unchanged_suffix_proxies'] = 12*(native+25)
stress = sum(stress_components.values())*1.2+30
remaining = (budget['cap_gpu_hours']-budget['used_gpu_hours'])*3600
result = {'status': 'W3_SMALL_WINDOW_PARENT_MASK_AND_COST_CPU_PREPARATION_NOT_SELECTED',
    'CPU_only': True, 'selected_parent_mask_swaps': selected,
    'adaptive_CD_candidate': {'scenes': 2, 'one_checkpoint_per_scene': 22,
        'target_call_by_scene': {selected[0]['sample']:45, selected[2]['sample']:46},
        'action_unit': 'one_CFG_call', 'first_action_native_D_or_C_both_allowed_if_legality_passes': True,
        'scope': 'TWO_CURRENT_C_D_PAIRS_WITH_ADAPTIVE_FUTURE_NOT_BUDGET_MATCHED',
        'proposed_parent_phases': 2, 'suffixes_per_scene': ['OFF','OFF','C','D','D','C'],
        'complete_suffix_controls': 12, 'proposed_new_encoded_outputs': 8,
        'existing_matched_Native_references': 2,
        'true_GPU_OFF_OFF_CC_DD_order_source_controls_preserved': True,
        'new_small_card_frozen_or_selected': False,
        'full_original8_24_18_card_modified': False,
        'real_native_uninstrumented_GPU_parity_requirement_status': 'INCOMPLETE_DO_NOT_CLAIM_FULL_RV0'},
    'cost': {'components_seconds': components, 'nominal_complete_seconds': nominal,
        'stress_proxy_complete_seconds': stress, 'stress_suffix_seconds_each': native+25,
        'planning_factor': 1.2, 'shutdown_allowance_seconds': 30,
        'proposed_GPU_timeout_seconds': None,
        'remaining_seconds': remaining, 'nominal_remaining_seconds': remaining-nominal,
        'stress_remaining_seconds': remaining-stress,
        'adaptive_CD_future_cost_measured': False, 'proxies_are_hard_bounds': False,
        'three_batches_committed_or_guaranteed': False,
        '1080_second_suggestion_below_even_nominal_complete_card': nominal>1080},
    'budget_snapshot': budget,
    'input_receipt_sha256': {n:sha(n) for n in ['reports/wc_fair_cal_r1_runner_20261004.json.gz',
        'reports/wc_fair_cal_r1_summary_20261004.json', 'reports/wc_rv0_restore_r1_summary_20261004.json',
        'reports/wc_rv0_restore_r1_runner_20261004.json','reports/budget.json']},
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'new_GPU_submission': False, 'new_RV_labels': 0, 'fixed_quota_swap_GPU_evidence': False,
    'limitations': ['Four syntactic swaps are not four independent samples; two exposed CAL parents.',
        'Own-branch legality/finite/max-age/reset/source and protected native-action checks require new router contracts and actual model verification.',
        'Parent trace selection contains no endpoint feedback, but a parent future mask is offline diagnostic information, not an online policy.',
        'No branch, Native parity, or control is silently removed from the original full card.',
        'Small proposal is a new diagnostic identity; Native references may be reused only under frozen source/config/encoded bridges.',
        'Full Native pipeline stress proxy is conservative planning, not a guaranteed runtime/memory bound.']}
out=root/'reports/wc_w3_small_window_cpu_preparation_20261004.json'
assert not out.exists(), 'Preserve previous preparation identity'
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'swaps':[(r['sample'],r['cfg_slot'],r['from_cache_call_n'],r['donor_full_call_m']) for r in selected],
    'nominal_seconds':nominal,'stress_proxy_seconds':stress,'remaining_seconds':remaining},ensure_ascii=False))
