"""Verify full native-tail traces, repeats, shared pre69 state and byte bridges."""
from pathlib import Path

from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256
from .rv0_native_tail_scope import LABELS, ENCODED, label_case
from .rv0_placement_v2_evaluation import TRACE, PIPELINE

TAIL_POLICY = 'FIXED_REGISTERED_SWAP_THROUGH68_NATIVE_OWN_STATE69_70_ORIGINAL_RESET71_72'
CORE_DONE = 'NATIVE_TAIL_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT'
ROW_DONE = 'NATIVE_TAIL_ALL10_REPEATS_ACTIONS_AND6_DECODE_BRIDGES_PASS_NOT_QUALITY'


def verify_native_tail_row(row, scene, deep_count):
    mask = tuple(scene['parent_action_mask'])
    if (type(deep_count) is not int or deep_count <= 0 or row['sample_name'] != scene['scene']
            or row['prepare_calls'] != 1 or row['flags_before'] != row['flags_after']
            or row['sample_return_sha256'] != row['final_latent_sha256']
            or [e['stage'] for e in row['pipeline']] != PIPELINE
            or any(len(row[k]) != (36 if k == 'solver_outputs' else 72) for k in TRACE)
            or any(d not in (0, deep_count) for d in row['deep'])
            or tuple('C' if d == 0 else 'D' for d in row['deep']) != mask):
        raise ValueError('Native-tail full parent identity/mask/pipeline differs')
    by = {c['label']: c for c in row['children']}
    if list(by) != LABELS or len(row['children']) != 10:
        raise ValueError('All ten ordered native-tail suffixes required')
    off = by['OFF1']
    if (any(off[k] != row[k][22 if k == 'solver_outputs' else 44:] for k in TRACE)
            or off['final_latent_sha256'] != row['final_latent_sha256']
            or off['record']['final_state_components'] != row['final_components']
            or off['pre69_state_components'] != row['pre69_state_components']):
        raise ValueError('Original adaptive OFF full continuation differs from parent')
    repeats = [('OFF1', 'OFF2')]+[(m+n+'_first', m+n+'_second')
        for n in ('46', '61') for m in ('FIXED', 'TAIL')]
    for first, second in repeats:
        a, b = by[first], by[second]
        if (any(a[k] != b[k] for k in TRACE+['final_latent_sha256',
                'pre69_state_components', 'pre69_router_history'])
                or a['record']['final_state_components'] != b['record']['final_state_components']
                or a['record']['action_report'] != b['record']['action_report']):
            raise ValueError('Native-tail repeat/order raw state/actions differ')
    for label, child in by.items():
        report = child['record']['action_report']; record = child['record']
        case = label_case(label, scene['cases'])
        swap = () if case is None else tuple(case['swap_calls'])
        fixed = FixedMaskPlan(mask, swap).action_mask()
        responsive = label.startswith('TAIL')
        actual = report['actual_actions']; events = report['suffix_events']
        if (child['swap_calls'] != list(swap) or child['native_tail'] is not responsive
                or child['status'] != 'COMPLETE_NATIVE_TAIL_SUFFIX_NOT_RV_LABEL'
                or record['parent_restored'] is not True or record['counterfactual_label'] is not False
                or record['completed_updates'] != 22 or record['planned_remaining_updates'] != 14
                or record['final_latent_sha256'] != child['final_latent_sha256']
                or any(len(child[k]) != (14 if k == 'solver_outputs' else 28) for k in TRACE)
                or len(actual) != 72 or actual[:68] != list(fixed[:68]) or actual[70:] != ['D', 'D']
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
            raise ValueError('Native-tail full actions/counts/reset/restoration differ')
        if responsive:
            if (report['remaining_policy'] != TAIL_POLICY or report['quota_matched_per_CFG'] is not False
                    or report['responsive_calls_only'] != [69, 70] or report['fixed_actions'] != list(fixed)
                    or report['fixed_mask_sha256'] != mask_sha256(fixed)
                    or report['actual_mask_sha256'] != mask_sha256(actual)
                    or report['plan']['swap_calls'] != list(swap) and tuple(report['plan']['swap_calls']) != swap
                    or report['current_truth_used_for_decision'] is not False):
                raise ValueError('Native-tail variable quota policy/report differs')
            changes = []
            for e in events[-4:-2]:
                if (e.get('native_tail_response') is not True or e['paid_probe'] is not True
                        or e['actual_action'] != ('C' if e['native_skip'] else 'D')
                        or e['actual_native_override'] is not False
                        or e['fixed_counterfactual_action'] != fixed[e['call']-1]
                        or e['tail_response_changes_fixed_action'] != (e['actual_action'] != fixed[e['call']-1])):
                    raise ValueError('Native tail must use the actual paid own-state proposal')
                if e['tail_response_changes_fixed_action']:
                    changes.append(e['call'])
            if report['tail_action_changes'] != changes:
                raise ValueError('Native-tail changed-action report differs')
        elif label.startswith('FIXED'):
            if (actual != list(fixed) or report['quota_matched_per_CFG'] is not True
                    or report['per_CFG_full_counts'] != list(cfg_full_counts(mask))
                    or report['remaining_policy'] != 'OFFLINE_FIXED_PARENT_MASK_WITH_OPTIONAL_TWO_POSITION_SWAP'):
                raise ValueError('Unchanged R2 fixed mask/quota required')
        elif (report['remaining_policy'] != 'ORIGINAL_WC_ADAPTIVE'
                or report['quota_matched_per_CFG'] is not False or actual != list(mask)):
            raise ValueError('OFF must be the original adaptive parent continuation')
        if case:
            if tuple(report['plan']['parent_mask']) != mask or tuple(report['plan']['swap_calls']) != swap:
                raise ValueError('Immutable registered swap plan differs')
            for e in events:
                if e['actual_action'] == 'C' or e['call'] in swap:
                    if not e['paid_probe'] or not 1 <= e['age_solver_steps'] <= 33:
                        raise ValueError('Native-tail own-CFG legal cache age/paid probe missing')
                if e['paid_probe'] and e['actual_native_override'] != ((e['actual_action'] == 'C') != bool(e['native_skip'])):
                    raise ValueError('Paid-probe native/executed evidence inconsistent')
            n, m = swap
            if (child['inputs'][:n-44] != off['inputs'][:n-44]
                    or [i+45 for i, (a, b) in enumerate(zip(off['deep'][:24], child['deep'][:24])) if a != b] != [n, m]):
                raise ValueError('Registered joint swap changed extra actions or its first actual input')
    for name in ('46', '61'):
        a, b = by['FIXED'+name+'_first'], by['TAIL'+name+'_first']
        if (a['inputs'][:25] != b['inputs'][:25]
                or any(a[k][:12 if k == 'solver_outputs' else 24] != b[k][:12 if k == 'solver_outputs' else 24]
                       for k in TRACE if k != 'inputs')
                or a['pre69_state_components'] != b['pre69_state_components']
                or a['pre69_router_history'] != b['pre69_router_history']):
            raise ValueError('FIXED/TAIL actual latent/cache/RNG/solver state before69 differs')
    decoded = {c['label']: c for c in row['decoded_children']}
    if list(decoded) != ENCODED or len(row['decoded_children']) != 5:
        raise ValueError('All five child encodings plus parent required')
    for label, child in decoded.items():
        if (child['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                or child['flags_before'] != child['flags_after']
                or [e['stage'] for e in child['pipeline']] != PIPELINE):
            raise ValueError('Native-tail original decode/guardrail/write pipeline incomplete')
        if label == 'OFF1' and (child['pipeline'] != row['pipeline']
                or child['artifact']['sha256'] != row['artifact']['sha256']):
            raise ValueError('OFF encoded parent bridge differs')


def audit_trajectories(receipt, config, deep_count):
    if (receipt['planned_parent_phases'], receipt['planned_suffix_controls'],
            receipt['planned_encoded_outputs'], len(receipt['requests'])) != (1, 10, 6, 1):
        raise ValueError('Complete native-tail denominator differs')
    row = receipt['requests'][0]
    if row['status'] != ROW_DONE:
        raise ValueError('Complete native-tail row required')
    verify_native_tail_row(row, config['scope']['scenes'][0], deep_count)
    return {'parents': 1, 'complete_suffixes': 10, 'new_outputs': 6, 'tail_pairs': 2,
            'responsive_counts_may_change': True, 'equal_runtime': False, 'RV_labels': False}


def evaluation_plan(receipt, config):
    if (receipt['status'] != CORE_DONE or receipt['CUDA_initialized'] is not True
            or receipt['toy_fixture'] is not False or receipt['complete_video'] is not True
            or receipt['scope'] != config or receipt['run_card'] != config['card']):
        raise ValueError('Actual complete native-tail GPU receipt/config required')
    row = receipt['requests'][0]; scene = row['sample_name']
    reference = config['references'][scene]
    if (row['historical_WC_encoded_bridge_pass'] is not True
            or row['historical_R2_FIXED_encoded_bridges_pass'] is not True
            or row['context'][1:] != reference['model_and_condition_context']):
        raise ValueError('Historical WC and R2 FIXED byte/provenance bridges required')
    decoded = {c['label']: c['artifact'] for c in row['decoded_children']}
    files = [row['artifact']]+[decoded[label] for label in ENCODED]
    refs = [reference[k] for k in ('Native35', 'official_WC', 'R2_FIXED46', 'R2_FIXED61')]
    bridges = [(row['artifact'], reference['official_WC']), (decoded['OFF1'], row['artifact'])]
    bridges += [(decoded['FIXED'+n+'_first'], reference['R2_FIXED'+n]) for n in ('46', '61')]
    if any(a['sha256'] != b['sha256'] for a, b in bridges):
        raise ValueError('Native-tail current/historical encoded byte bridge differs')
    root = (Path(config['expected_project_root'])/'outputs'/config['run_id']/'diagnostic').resolve()
    paths = [Path(f['path']).resolve(strict=True) for f in files+refs]
    if len(set(paths)) != 10 or any(not p.is_relative_to(root) for p in paths[:6]):
        raise ValueError('All6 new plus4 historical files must be distinct in their frozen roots')
    pairs = [{'scene': scene, 'label': 'TAIL'+n+'_first', 'CFG_slot': label_case('TAIL'+n+'_first')['CFG_slot'],
        'reference': reference['Native35'], 'candidate': decoded['TAIL'+n+'_first']} for n in ('46', '61')]
    return {'files': files, 'references': refs, 'bridges': bridges, 'pairs': pairs,
            'new_losses': 2, 'reused_losses': 3, 'signed_tail_pairs': 2}
