"""Complete response-onset traces, all repeats and actual prefix state gates."""
from pathlib import Path

from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256
from .rv0_native_onset import response_policy
from .rv0_native_onset_scope import LABELS, ENCODED, CALLS, label_mode
from .rv0_placement_v2_evaluation import TRACE, PIPELINE

CORE_DONE = 'NATIVE_RESPONSE_ONSET_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'
ROW_DONE = 'NATIVE_RESPONSE_ONSET_ALL10_REPEATS_STATE_GATES_AND6_BRIDGES_PASS_NOT_QUALITY'


def verify_native_response_row(row, scene, deep_count):
    mask = tuple(scene['parent_action_mask']); swap = tuple(scene['case']['swap_calls'])
    fixed = FixedMaskPlan(mask, swap).action_mask()
    if (type(deep_count) is not int or deep_count <= 0 or row['sample_name'] != scene['scene']
            or row['prepare_calls'] != 1 or row['flags_before'] != row['flags_after']
            or row['sample_return_sha256'] != row['final_latent_sha256']
            or [e['stage'] for e in row['pipeline']] != PIPELINE
            or any(len(row[k]) != (36 if k == 'solver_outputs' else 72) for k in TRACE)
            or any(d not in (0, deep_count) for d in row['deep'])
            or tuple('C' if d == 0 else 'D' for d in row['deep']) != mask):
        raise ValueError('Response-onset complete original parent differs')
    by = {c['label']: c for c in row['children']}
    if list(by) != LABELS or len(row['children']) != 10:
        raise ValueError('All ten ordered complete response-onset suffixes required')
    off = by['OFF1']
    if (any(off[k] != row[k][22 if k == 'solver_outputs' else 44:] for k in TRACE)
            or off['final_latent_sha256'] != row['final_latent_sha256']
            or off['record']['final_state_components'] != row['final_components']
            or off['response_boundaries'] != row['response_boundaries']):
        raise ValueError('Original adaptive OFF complete continuation differs from parent')
    repeats = [('OFF1', 'OFF2')]+[(m+'_first', m+'_second') for m in CALLS]
    for first, second in repeats:
        a, b = by[first], by[second]
        if (any(a[k] != b[k] for k in TRACE+['final_latent_sha256', 'response_boundaries'])
                or a['record']['final_state_components'] != b['record']['final_state_components']
                or a['record']['action_report'] != b['record']['action_report']):
            raise ValueError('Response-onset complete repeat/order state or actions differ')
    for label, child in by.items():
        mode = label_mode(label); calls = [] if mode is None else CALLS[mode]
        report = child['record']['action_report']; record = child['record']
        actual = report['actual_actions']; events = report['suffix_events']
        if (child['swap_calls'] != ([] if mode is None else list(swap))
                or child['responsive_calls'] != calls
                or child['status'] != 'COMPLETE_NATIVE_RESPONSE_SUFFIX_NOT_RV_LABEL'
                or record['parent_restored'] is not True or record['counterfactual_label'] is not False
                or record['completed_updates'] != 22 or record['planned_remaining_updates'] != 14
                or record['final_latent_sha256'] != child['final_latent_sha256']
                or any(len(child[k]) != (14 if k == 'solver_outputs' else 28) for k in TRACE)
                or set(child['response_boundaries']) != {'65', '67', '69'}
                or any(not v['components'] or not v['own_CFG_history']
                       for v in child['response_boundaries'].values())
                or len(actual) != 72 or actual[70:] != ['D', 'D']
                or any(a not in ('C', 'D') for a in actual)
                or [e['call'] for e in events] != list(range(45, 73))
                or [e['cfg_slot'] for e in events] != [n % 2 for n in range(28)]
                or any(e['current_deep_truth_used'] for e in events)
                or any(d not in (0, deep_count) for d in child['deep'])
                or ['C' if d == 0 else 'D' for d in child['deep']] != actual[44:]
                or [e['actual_action'] for e in events] != actual[44:]
                or report['per_CFG_full_counts'] != list(cfg_full_counts(actual))
                or report['equal_runtime'] is not False or report['online_policy'] is not False
                or report['single_step_RV_label'] is not False or not events[-3]['native_cycle_reset']):
            raise ValueError('Response-onset full coverage, decisions, reset or restoration differs')
        if calls:
            if (actual[:calls[0]-1] != list(fixed[:calls[0]-1])
                    or report['remaining_policy'] != response_policy(tuple(calls))
                    or report['quota_matched_per_CFG'] is not False
                    or report['responsive_calls_only'] != calls
                    or report['fixed_actions'] != list(fixed)
                    or report['fixed_mask_sha256'] != mask_sha256(fixed)
                    or report['actual_mask_sha256'] != mask_sha256(actual)
                    or report['current_truth_used_for_decision'] is not False):
                raise ValueError('Sealed native-response window/report differs')
            changes = []
            for e in events:
                if e['call'] not in calls:
                    if e.get('native_response') is True:
                        raise ValueError('Native response leaked outside its registered window')
                    continue
                if (e.get('native_response') is not True or e['paid_probe'] is not True
                        or e['actual_action'] != ('C' if e['native_skip'] else 'D')
                        or e['actual_native_override'] is not False
                        or e['fixed_counterfactual_action'] != fixed[e['call']-1]
                        or e['response_policy'] != response_policy(tuple(calls))
                        or e['response_changes_fixed_action'] != (e['actual_action'] != fixed[e['call']-1])):
                    raise ValueError('Native response must use the actual paid own-state proposal')
                if e['response_changes_fixed_action']:
                    changes.append(e['call'])
            if report['response_action_changes'] != changes:
                raise ValueError('Actual native-response changed-action report differs')
        elif mode == 'FIXED61':
            if (actual != list(fixed) or report['quota_matched_per_CFG'] is not True
                    or report['per_CFG_full_counts'] != list(cfg_full_counts(mask))
                    or report['remaining_policy'] != 'OFFLINE_FIXED_PARENT_MASK_WITH_OPTIONAL_TWO_POSITION_SWAP'):
                raise ValueError('Historical FIXED61 executed mask/quota differs')
        elif (report['remaining_policy'] != 'ORIGINAL_WC_ADAPTIVE'
                or report['quota_matched_per_CFG'] is not False or actual != list(mask)):
            raise ValueError('OFF must be the original adaptive complete continuation')
        if mode:
            if tuple(report['plan']['parent_mask']) != mask or tuple(report['plan']['swap_calls']) != swap:
                raise ValueError('The registered common61/63 plan differs')
            for e in events:
                if e['actual_action'] == 'C' or e['call'] in swap:
                    if not e['paid_probe'] or not 1 <= e['age_solver_steps'] <= 33:
                        raise ValueError('Own-CFG true cache source age/paid probe missing')
                if e['paid_probe'] and e['actual_native_override'] != ((e['actual_action'] == 'C') != bool(e['native_skip'])):
                    raise ValueError('Paid-probe native and executed action evidence differs')
            n, m = swap
            if (child['inputs'][:n-44] != off['inputs'][:n-44]
                    or [i+45 for i, (a, b) in enumerate(zip(off['deep'][:20], child['deep'][:20])) if a != b] != [n, m]):
                raise ValueError('Common joint swap changed extra actions before65 or its first input')
    groups = {'65': ['FIXED61', 'LATE69', 'RESP65', 'RESP67'],
              '67': ['FIXED61', 'LATE69', 'RESP67'], '69': ['FIXED61', 'LATE69']}
    for start, modes in groups.items():
        n = int(start); prefix = n-45; a = by[modes[0]+'_first']
        for mode in modes[1:]:
            b = by[mode+'_first']
            if (a['inputs'][:prefix+1] != b['inputs'][:prefix+1]
                    or any(a[k][:prefix//2 if k == 'solver_outputs' else prefix]
                           != b[k][:prefix//2 if k == 'solver_outputs' else prefix]
                           for k in TRACE if k != 'inputs')
                    or a['response_boundaries'][start] != b['response_boundaries'][start]):
                raise ValueError('Actual complete state/history/input before'+start+' differs')
    decoded = {c['label']: c for c in row['decoded_children']}
    if list(decoded) != ENCODED or len(row['decoded_children']) != 5:
        raise ValueError('All five encoded children plus parent required')
    for label, child in decoded.items():
        if (child['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                or child['flags_before'] != child['flags_after']
                or [e['stage'] for e in child['pipeline']] != PIPELINE):
            raise ValueError('Original decode/guardrail/write pipeline incomplete')
        if label == 'OFF1' and (child['pipeline'] != row['pipeline']
                or child['artifact']['sha256'] != row['artifact']['sha256']):
            raise ValueError('Original OFF encoded parent bridge differs')


def audit_trajectories(receipt, config, deep_count):
    if (receipt['planned_parent_phases'], receipt['planned_suffix_controls'],
            receipt['planned_encoded_outputs'], len(receipt['requests'])) != (1, 10, 6, 1):
        raise ValueError('Complete response-onset denominator differs')
    row = receipt['requests'][0]
    if row['status'] != ROW_DONE:
        raise ValueError('Complete response-onset row required')
    verify_native_response_row(row, config['scope']['scenes'][0], deep_count)
    return {'parents': 1, 'complete_suffixes': 10, 'new_outputs': 6, 'response_pairs': 2,
            'pre_response_state_gates': [65, 67, 69], 'counts_may_change': True,
            'equal_runtime': False, 'RV_labels': False}


def evaluation_plan(receipt, config):
    if (receipt['status'] != CORE_DONE or receipt['CUDA_initialized'] is not True
            or receipt['toy_fixture'] is not False or receipt['complete_video'] is not True
            or receipt['scope'] != config or receipt['run_card'] != config['card']):
        raise ValueError('Actual complete response-onset GPU receipt/config required')
    row = receipt['requests'][0]; scene = row['sample_name']; reference = config['references'][scene]
    if (row['historical_WC_encoded_bridge_pass'] is not True
            or row['historical_FIXED61_LATE69_encoded_bridges_pass'] is not True
            or row['context'][1:] != reference['model_and_condition_context']):
        raise ValueError('Historical WC, FIXED61 and LATE69 byte/provenance bridges required')
    decoded = {c['label']: c['artifact'] for c in row['decoded_children']}
    files = [row['artifact']]+[decoded[label] for label in ENCODED]
    refs = [reference[k] for k in ('Native35', 'official_WC', 'FIXED61', 'LATE69')]
    bridges = [(row['artifact'], reference['official_WC']), (decoded['OFF1'], row['artifact'])]
    bridges += [(decoded[m+'_first'], reference[m]) for m in ('FIXED61', 'LATE69')]
    if any(a['sha256'] != b['sha256'] for a, b in bridges):
        raise ValueError('Current/historical encoded byte bridge differs')
    root = (Path(config['expected_project_root'])/'outputs'/config['run_id']/'diagnostic').resolve()
    paths = [Path(f['path']).resolve(strict=True) for f in files+refs]
    if len(set(paths)) != 10 or any(not p.is_relative_to(root) for p in paths[:6]):
        raise ValueError('All6 new plus4 existing files require their frozen roots')
    pairs = [{'scene': scene, 'label': m+'_first', 'reference': reference['Native35'],
              'candidate': decoded[m+'_first']} for m in ('RESP65', 'RESP67')]
    return {'files': files, 'references': refs, 'bridges': bridges, 'pairs': pairs,
            'new_losses': 2, 'reused_losses': 3, 'signed_response_pairs': 2}
