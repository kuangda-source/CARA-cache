"""Raw complete placement trajectories and Native-relative scoring, no Torch."""
from pathlib import Path

from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256
from .rv0_placement_scope import LABELS, ENCODED, validate_scope

TRACE = ['inputs', 'outputs', 'deep', 'banks', 'solver_outputs']
PIPELINE = ['decode_input', 'decode_output', 'guardrail_input', 'guardrail_output', 'save_input']


def validate_frozen_scope(scope):
    candidates = []
    for row in scope['scenes']:
        for swap in row['swaps']:
            candidates.append({'sample': row['scene'], 'cfg_slot': swap['CFG_slot'],
                'from_cache_call_n': swap['calls'][0], 'donor_full_call_m': swap['calls'][1],
                'parent_mask': row['parent_action_mask'],
                'parent_full_CFG_counts': row['parent_full_counts_per_CFG'],
                'selection_reads_video_score_or_local_error': False})
    return validate_scope(scope, candidates)


def validate_fixture_scope(scope):
    """Only the declared CPU Toy caller may use these non-scientific pairs."""
    if (scope.get('CPU_TOY_fixture') is not True or len(scope['scenes']) != 2
            or scope['maximum_age_solver_steps'] != 33):
        raise ValueError('Explicit two-scene CPU Toy placement scope required')
    for row in scope['scenes']:
        mask = tuple(row['parent_action_mask'])
        FixedMaskPlan(mask).validate()
        if (len(row['swaps']) != 2 or row['parent_full_counts_per_CFG'] != list(cfg_full_counts(mask))
                or row['parent_mask_sha256'] != mask_sha256(mask)):
            raise ValueError('CPU Toy parent mask/quotas differ')
        for slot, swap in enumerate(row['swaps']):
            if swap['CFG_slot'] != slot or (swap['calls'][0]-1) % 2 != slot:
                raise ValueError('CPU Toy separate CFG swap differs')
            FixedMaskPlan(mask, tuple(swap['calls'])).validate()


def verify_placement_row(row, scene, deep_count):
    if type(deep_count) is not int or deep_count <= 0:
        raise ValueError('Actual positive deep block count required')
    mask = tuple(scene['parent_action_mask'])
    if (row['sample_name'] != scene['scene'] or row['prepare_calls'] != 1
            or row['flags_before'] != row['flags_after']
            or row['sample_return_sha256'] != row['final_latent_sha256']
            or [e['stage'] for e in row['pipeline']] != PIPELINE
            or any(len(row[k]) != (36 if k == 'solver_outputs' else 72) for k in TRACE)
            or any(d not in (0, deep_count) for d in row['deep'])
            or tuple('C' if d == 0 else 'D' for d in row['deep']) != mask):
        raise ValueError('Placement full parent identity/mask/pipeline differs')
    by = {c['label']: c for c in row['children']}
    if list(by) != LABELS or len(row['children']) != 8:
        raise ValueError('All eight ordered placement suffix controls required')
    for label in ('OFF1', 'BASE1'):
        child = by[label]
        if (any(child[k] != row[k][22 if k == 'solver_outputs' else 44:] for k in TRACE)
                or child['final_latent_sha256'] != row['final_latent_sha256']
                or child['record']['final_state_components'] != row['final_components']):
            raise ValueError('Placement OFF/fixed BASE complete parent continuation differs')
    for first, second in [('OFF1', 'OFF2'), ('BASE1', 'BASE2'),
                          ('SWAP0_first', 'SWAP0_second'), ('SWAP1_first', 'SWAP1_second')]:
        a, b = by[first], by[second]
        if (any(a[k] != b[k] for k in TRACE+['final_latent_sha256'])
                or a['record']['final_state_components'] != b['record']['final_state_components']
                or a['record']['action_report'] != b['record']['action_report']):
            raise ValueError('Placement repeat/order full trajectory/state/action differs')
    for label, child in by.items():
        record, report = child['record'], child['record']['action_report']
        events = report['suffix_events']
        swap = () if label.startswith(('OFF', 'BASE')) else tuple(scene['swaps'][int(label[4])]['calls'])
        expected = FixedMaskPlan(mask, swap).action_mask()
        if (child['swap_calls'] != list(swap) or child['status'] != 'COMPLETE_PLACEMENT_SUFFIX_NOT_RV_LABEL'
                or record['parent_restored'] is not True or record['counterfactual_label'] is not False
                or record['completed_updates'] != 22 or record['planned_remaining_updates'] != 14
                or record['final_latent_sha256'] != child['final_latent_sha256']
                or any(len(child[k]) != (14 if k == 'solver_outputs' else 28) for k in TRACE)
                or [e['call'] for e in events] != list(range(45, 73))
                or [e['cfg_slot'] for e in events] != [n % 2 for n in range(28)]
                or any(e['current_deep_truth_used'] for e in events)
                or any(d not in (0, deep_count) for d in child['deep'])
                or report['actual_actions'] != list(expected)
                or ['C' if d == 0 else 'D' for d in child['deep']] != list(expected[44:])
                or [e['actual_action'] for e in events] != list(expected[44:])
                or report['per_CFG_full_counts'] != list(cfg_full_counts(mask))
                or report['equal_runtime'] is not False or report['online_policy'] is not False
                or report['single_step_RV_label'] is not False):
            raise ValueError('Placement complete suffix actions/quota/restoration differ')
        if label.startswith('OFF'):
            if report['remaining_policy'] != 'ORIGINAL_WC_ADAPTIVE' or report['quota_matched_per_CFG'] is not False:
                raise ValueError('OFF must remain original adaptive, without a forced quota')
        else:
            if (report['remaining_policy'] != 'OFFLINE_FIXED_PARENT_MASK_WITH_OPTIONAL_TWO_POSITION_SWAP'
                    or report['quota_matched_per_CFG'] is not True or report['planned_action_changes'] != len(swap)
                    or tuple(report['plan']['parent_mask']) != mask or tuple(report['plan']['swap_calls']) != swap
                    or report['plan']['maximum_age_solver_steps'] != 33
                    or report['actual_mask_sha256'] != mask_sha256(expected)
                    or report['parent_mask_sha256'] != mask_sha256(mask)
                    or report['current_truth_used_for_decision'] is not False
                    or any(e.get('actual_native_override') for e in events[-4:])):
                raise ValueError('Fixed placement plan/protected own-state decisions differ')
            for e in events:
                if e['actual_action'] == 'C' or e['call'] in swap:
                    if not e['paid_probe'] or not 1 <= e['age_solver_steps'] <= 33:
                        raise ValueError('Fixed placement paid probe/source age differs')
        if swap:
            n, m = swap
            base = by['BASE1']
            if (child['inputs'][:n-44] != base['inputs'][:n-44]
                    or [i+45 for i, (a, b) in enumerate(zip(base['deep'], child['deep'])) if a != b] != [n, m]
                    or child['deep'][n-45] != deep_count or child['deep'][m-45] != 0):
                raise ValueError('Swap must change exactly two actions from identical first input')
    decoded = {c['label']: c for c in row['decoded_children']}
    if list(decoded) != ENCODED or len(row['decoded_children']) != 4:
        raise ValueError('Four distinct child encodings required')
    for label, child in decoded.items():
        if (child['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                or child['flags_before'] != child['flags_after']
                or [e['stage'] for e in child['pipeline']] != PIPELINE):
            raise ValueError('Placement child original pipeline incomplete')
        if label in ('OFF1', 'BASE1') and (child['pipeline'] != row['pipeline']
                or child['artifact']['sha256'] != row['artifact']['sha256']):
            raise ValueError('Placement OFF/BASE parent encoded bridge differs')


def audit_trajectories(receipt, config, deep_count):
    if (receipt['planned_parent_phases'], receipt['planned_suffix_controls'], receipt['planned_encoded_outputs']) != (2, 16, 10):
        raise ValueError('Original full placement denominator differs')
    if len(receipt['requests']) != 2:
        raise ValueError('Both complete placement parents required')
    for row, scene in zip(receipt['requests'], config['scope']['scenes']):
        if row['status'] != 'PLACEMENT_ALL_REPEATS_QUOTAS_AND_DECODE_BRIDGES_PASS_NOT_QUALITY':
            raise ValueError('Complete placement row required')
        verify_placement_row(row, scene, deep_count)
    return {'parents': 2, 'complete_suffixes': 16, 'new_outputs': 10, 'swap_pairs': 4,
            'per_CFG_quota_matched': True, 'equal_runtime': False, 'formal_RV_training_labels': False}


def evaluation_plan(receipt, config, *, real_GPU_required=True):
    if receipt['status'] != 'PLACEMENT_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT':
        raise ValueError('Complete full placement core required before scoring')
    if len(receipt['requests']) != 2 or len(config['scope']['scenes']) != 2:
        raise ValueError('Both complete placement scenes required for scoring')
    if real_GPU_required:
        validate_frozen_scope(config['scope'])
        if (receipt.get('CUDA_initialized') is not True or receipt.get('toy_fixture') is not False
                or receipt.get('complete_video') is not True or receipt.get('run_card') != config['scope']['card']
                or receipt.get('scope') != config or receipt.get('wc_settings') != config['historical_wc_settings']):
            raise ValueError('Actual frozen placement GPU/config required')
    files, references, pairs, bridges = [], [], [], []
    root = (Path(config['expected_project_root'])/'outputs'/config['scope']['run_id']/'diagnostic').resolve()
    for row, scene in zip(receipt['requests'], config['scope']['scenes']):
        reference = config['references'][scene['scene']]
        if (row['sample_name'] != scene['scene'] or row['historical_WC_encoded_bridge_pass'] is not True
                or row['context'][1:] != reference['model_and_condition_context']
                or row['artifact']['sha256'] != reference['official_WC']['sha256']):
            raise ValueError('Strict placement historical Native/current WC bridge required')
        files.append(row['artifact']); references.append(reference['Native35'])
        decoded = {c['label']: c for c in row['decoded_children']}
        if list(decoded) != ENCODED or len(row['decoded_children']) != 4:
            raise ValueError('Four complete distinct placement child encodings required for scoring')
        for label in ENCODED:
            if decoded[label]['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE':
                raise ValueError('Placement decoded scoring child incomplete')
            files.append(decoded[label]['artifact'])
        for label in ('OFF1', 'BASE1'):
            bridges.append({'scene': row['sample_name'], 'reference': row['artifact'], 'candidate': decoded[label]['artifact']})
        for label in ('BASE1', 'SWAP0_first', 'SWAP1_first'):
            pairs.append({'scene': row['sample_name'], 'label': label,
                'CFG_slot': None if label == 'BASE1' else int(label[4]),
                'reference': reference['Native35'], 'candidate': decoded[label]['artifact']})
    if (len(files), len(references), len(pairs), len(bridges)) != (10, 2, 6, 4):
        raise ValueError('Complete placement scoring denominator differs')
    paths = [Path(f['path']).resolve(strict=True) for f in files+references]
    if len(set(paths)) != 12 or real_GPU_required and any(not p.is_relative_to(root) for p in paths[:10]):
        raise ValueError('Placement artifacts must be distinct within their canonical independent root')
    return {'files': files, 'references': references, 'pairs': pairs, 'bridges': bridges,
            'signed_swap_diagnostics': 4, 'per_CFG_quota_matched': True, 'equal_runtime': False,
            'formal_RV_training_labels': False, 'physics_or_quality_acceptance': False}
