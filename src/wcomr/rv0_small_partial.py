"""Read-only completed-row analysis after incomplete small-card termination.

The original 2/12/8 card remains incomplete. Completed rows use exactly the
strict per-row rules of the frozen full audit; missing rows remain in the
original two-scene denominator. No GPU runner or acceptance scope is changed.
"""
from pathlib import Path
from .rv0_small_evaluation import TRACE, PIPELINE, LABELS


def partial_plan(receipt, config):
    if ((receipt['planned_parent_phases'], receipt['planned_suffix_controls'], receipt['planned_encoded_outputs']) != (2, 12, 8)
            or receipt['run_card'] != config['card'] or receipt['scope'] != config
            or receipt['CUDA_initialized'] is not True or receipt['toy_fixture'] is not False
            or receipt['wc_settings'] != config['historical_wc_settings']):
        raise ValueError('Original real GPU two-scene denominator/provenance required')
    if len(receipt['requests']) > 2 or [r['sample_name'] for r in receipt['requests']] != config['sample_names'][:len(receipt['requests'])]:
        raise ValueError('Original scene order/denominator changed')
    files, references, pairs, matrix, costs = [], [], [], [], []
    for slot, scene in enumerate(config['sample_names']):
        row = receipt['requests'][slot] if slot < len(receipt['requests']) else None
        completed = row is not None and row['status'] == 'SMALL_SELECTED_CD_ALL_REPEATS_AND_DECODE_BRIDGE_PASS_NOT_QUALITY'
        entry = {'scene': scene, 'CFG_slot': slot, 'target_call': 45+slot,
                 'status': 'COMPLETE_ROW_PENDING_METRIC' if completed else 'UNFINISHED_OR_TECH_BLOCKED',
                 'planned_suffixes': 6, 'planned_new_outputs': 4,
                 'observed_completed_suffixes': sum(c['status'] == 'COMPLETE_SUFFIX_NOT_RV_LABEL' for c in row['children']) if row else 0,
                 'observed_parent_CFG_calls': len(row['inputs']) if row else 0}
        matrix.append(entry)
        if not completed:
            continue
        validate_complete_row(row, slot, 26)
        reference = config['references'][scene]
        if (row['historical_WC_encoded_bridge_pass'] is not True
                or row['context'] != [config['run_id']+':'+scene, *reference['model_and_condition_context']]
                or row['artifact']['sha256'] != reference['official_WC']['sha256']):
            raise ValueError('Completed row historical Native/WC source bridge differs')
        decoded = {d['label']: d for d in row['decoded_children']}
        row_files = [row['artifact'], *[decoded[n]['artifact'] for n in ['OFF1', 'C_first', 'D_first']]]
        root = Path(config['expected_project_root'])/'outputs'/config['run_id']/'diagnostic'
        if any(not Path(f['path']).is_relative_to(root) for f in row_files):
            raise ValueError('Completed row artifacts outside original output identity')
        files.extend(row_files); references.append(reference['Native35'])
        pairs.extend({'scene': scene, 'CFG_slot': slot, 'target_call': 45+slot, 'action': action,
                      'reference': reference['Native35'], 'candidate': decoded[action+'_first']['artifact']}
                     for action in ['C', 'D'])
        costs.append({'scene': scene, 'inclusive_parent_with_controls_wall_seconds': row['inclusive_parent_wall_seconds'],
                      'suffixes': [{'label': c['label'], 'full_calls_per_CFG': [sum(v > 0 for v in c['deep'][s::2]) for s in [0, 1]],
                                    'control_wall_seconds': c['record']['control_wall_seconds']} for c in row['children']]})
    if len({f['path'] for f in files+references}) != len(files+references):
        raise ValueError('Completed row artifact paths are not distinct')
    return {'original_denominator': {'parents': 2, 'suffixes': 12, 'new_outputs': 8, 'Native_relative_losses': 4, 'signed_diagnostics': 2},
            'matrix': matrix, 'files': files, 'references': references, 'pairs': pairs, 'costs': costs,
            'full_card_accepted': False, 'formal_RV_training_labels': False, 'budget_matched': False}


def validate_complete_row(row, slot, deep_count):
    if row['status'] != 'SMALL_SELECTED_CD_ALL_REPEATS_AND_DECODE_BRIDGE_PASS_NOT_QUALITY' or row['slot'] != slot or row['target_call'] != 45 + slot or (row['prepare_calls'] != 1) or (row['flags_before'] != row['flags_after']) or (row['final_latent_sha256'] != row['sample_return_sha256']) or ([e['stage'] for e in row['pipeline']] != PIPELINE):
        raise ValueError('Small completed parent/pipeline identity differs')
    if any((len(row[k]) != (36 if k == 'solver_outputs' else 72) for k in TRACE)):
        raise ValueError('Small full parent trajectory incomplete')
    by = {c['label']: c for c in row['children']}
    if list(by) != LABELS or len(row['children']) != 6:
        raise ValueError('All six unique small suffix controls required')
    off = by['OFF1']
    if any((off[k] != row[k][22 if k == 'solver_outputs' else 44:] for k in TRACE)):
        raise ValueError('Small OFF complete continuation differs')
    if off['final_latent_sha256'] != row['final_latent_sha256'] or off['record']['final_state_components'] != row['final_components']:
        raise ValueError('Small OFF final state differs')
    for (first, second) in [('OFF1', 'OFF2'), ('C_first', 'C_second'), ('D_first', 'D_second')]:
        (a, b) = (by[first], by[second])
        if any((a[k] != b[k] for k in TRACE + ['final_latent_sha256'])) or a['record']['final_state_components'] != b['record']['final_state_components']:
            raise ValueError('Small repeat/order trajectory or final state differs')
    (c, d) = (by['C_first'], by['D_first'])
    if c['inputs'][:slot + 1] != d['inputs'][:slot + 1] or c['deep'][slot] != 0 or d['deep'][slot] != deep_count:
        raise ValueError('Small same-input C/D deep execution differs')
    for (label, child) in by.items():
        record = child['record']
        report = record['action_report']
        events = report['suffix_events']
        action = child['action']
        if child['slot'] != slot or action != ('OFF' if label.startswith('OFF') else label[0]) or child['status'] != 'COMPLETE_SUFFIX_NOT_RV_LABEL' or (record['parent_restored'] is not True) or (record['counterfactual_label'] is not False) or (report['budget_matched'] is not False) or (report['RV_label'] is not False) or (record['completed_updates'] != 22) or (record['planned_remaining_updates'] != 14) or (record['final_latent_sha256'] != child['final_latent_sha256']) or any((len(child[k]) != (14 if k == 'solver_outputs' else 28) for k in TRACE)) or ([e['call'] for e in events] != list(range(45, 73))) or ([e['cfg_slot'] for e in events] != [n % 2 for n in range(28)]) or any((e['current_deep_truth_used'] for e in events)) or (report['remaining_policy'] != 'ORIGINAL_WC_ADAPTIVE') or any((n not in (0, deep_count) for n in child['deep'])) or ((report['plan']['target_call'], report['plan']['cfg_slot']) != (45 + slot, slot)) or (report['plan']['action'] != action) or (report['decision_interventions'] != int(action != 'OFF')) or (['C' if n == 0 else 'D' for n in child['deep']] != [e['actual_action'] for e in events]):
            raise ValueError('Small full suffix action/source/restoration coverage differs')
        if action != 'OFF':
            target = events[slot]
            history = target['true_full_history'][slot]
            if not target['paid_probe'] or target['requested'] != target['actual_action'] or target['actual_action'] != action or (not 1 <= target['age_solver_steps'] <= 32) or (len(history) != 2) or ((history[-1] == 23) != (action == 'D')) or (action == 'C' and (not all((n < 23 for n in history)))):
                raise ValueError('Small current paid probe/past own-CFG full history differs')
    decoded = {c['label']: c for c in row['decoded_children']}
    if list(decoded) != ['OFF1', 'C_first', 'D_first'] or len(row['decoded_children']) != 3:
        raise ValueError('Small complete distinct child encoding denominator differs')
    for child in decoded.values():
        if child['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE' or child['flags_before'] != child['flags_after'] or [e['stage'] for e in child['pipeline']] != PIPELINE:
            raise ValueError('Small child source-derived full pipeline incomplete')
    if decoded['OFF1']['pipeline'] != row['pipeline'] or decoded['OFF1']['artifact']['sha256'] != row['artifact']['sha256']:
        raise ValueError('Small source-derived OFF video bridge differs')
    return {"status": "COMPLETE_ROW_STRICT_TRAJECTORY_PASS_NOT_CARD", "slot": slot}
