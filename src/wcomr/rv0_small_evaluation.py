"""Independent raw small C/D trajectory and four-pair scoring plan, no Torch."""
from pathlib import Path

TRACE = ['inputs', 'outputs', 'deep', 'banks', 'solver_outputs']
PIPELINE = ['decode_input', 'decode_output', 'guardrail_input', 'guardrail_output', 'save_input']
LABELS = ['OFF1', 'OFF2', 'C_first', 'D_second', 'D_first', 'C_second']


def audit_trajectories(receipt, deep_count):
    if type(deep_count) is not int or deep_count <= 0:
        raise ValueError('Small actual deep count required')
    if (receipt['planned_parent_phases'], receipt['planned_suffix_controls'], receipt['planned_encoded_outputs']) != (2, 12, 8):
        raise ValueError('Small original scope denominator differs')
    if len(receipt['requests']) != 2:
        raise ValueError('Both small requests required')
    for slot, row in enumerate(receipt['requests']):
        if (row['status'] != 'SMALL_SELECTED_CD_ALL_REPEATS_AND_DECODE_BRIDGE_PASS_NOT_QUALITY'
                or row['slot'] != slot or row['target_call'] != 45+slot
                or row['prepare_calls'] != 1 or row['flags_before'] != row['flags_after']
                or row['final_latent_sha256'] != row['sample_return_sha256']
                or [e['stage'] for e in row['pipeline']] != PIPELINE):
            raise ValueError('Small completed parent/pipeline identity differs')
        if any(len(row[k]) != (36 if k == 'solver_outputs' else 72) for k in TRACE):
            raise ValueError('Small full parent trajectory incomplete')
        by = {c['label']: c for c in row['children']}
        if list(by) != LABELS or len(row['children']) != 6:
            raise ValueError('All six unique small suffix controls required')
        off = by['OFF1']
        if any(off[k] != row[k][22 if k == 'solver_outputs' else 44:] for k in TRACE):
            raise ValueError('Small OFF complete continuation differs')
        if (off['final_latent_sha256'] != row['final_latent_sha256']
                or off['record']['final_state_components'] != row['final_components']):
            raise ValueError('Small OFF final state differs')
        for first, second in [('OFF1', 'OFF2'), ('C_first', 'C_second'), ('D_first', 'D_second')]:
            a, b = by[first], by[second]
            if (any(a[k] != b[k] for k in TRACE+['final_latent_sha256'])
                    or a['record']['final_state_components'] != b['record']['final_state_components']):
                raise ValueError('Small repeat/order trajectory or final state differs')
        c, d = by['C_first'], by['D_first']
        if c['inputs'][:slot+1] != d['inputs'][:slot+1] or c['deep'][slot] != 0 or d['deep'][slot] != deep_count:
            raise ValueError('Small same-input C/D deep execution differs')
        for label, child in by.items():
            record = child['record']; report = record['action_report']; events = report['suffix_events']
            action = child['action']
            if (child['slot'] != slot or action != ('OFF' if label.startswith('OFF') else label[0])
                    or child['status'] != 'COMPLETE_SUFFIX_NOT_RV_LABEL' or record['parent_restored'] is not True
                    or record['counterfactual_label'] is not False or report['budget_matched'] is not False
                    or report['RV_label'] is not False or record['completed_updates'] != 22
                    or record['planned_remaining_updates'] != 14 or record['final_latent_sha256'] != child['final_latent_sha256']
                    or any(len(child[k]) != (14 if k == 'solver_outputs' else 28) for k in TRACE)
                    or [e['call'] for e in events] != list(range(45, 73))
                    or [e['cfg_slot'] for e in events] != [n % 2 for n in range(28)]
                    or any(e['current_deep_truth_used'] for e in events)
                    or report['remaining_policy'] != 'ORIGINAL_WC_ADAPTIVE'
                    or any(n not in (0, deep_count) for n in child['deep'])
                    or (report['plan']['target_call'], report['plan']['cfg_slot']) != (45+slot, slot)
                    or report['plan']['action'] != action
                    or report['decision_interventions'] != int(action != 'OFF')
                    or ['C' if n == 0 else 'D' for n in child['deep']] != [e['actual_action'] for e in events]):
                raise ValueError('Small full suffix action/source/restoration coverage differs')
            if action != 'OFF':
                target = events[slot]
                history = target['true_full_history'][slot]
                if (not target['paid_probe'] or target['requested'] != target['actual_action'] or target['actual_action'] != action
                        or not 1 <= target['age_solver_steps'] <= 32 or len(history) != 2
                        or (history[-1] == 23) != (action == 'D')
                        or action == 'C' and not all(n < 23 for n in history)):
                    raise ValueError('Small current paid probe/past own-CFG full history differs')
        decoded = {c['label']: c for c in row['decoded_children']}
        if list(decoded) != ['OFF1', 'C_first', 'D_first'] or len(row['decoded_children']) != 3:
            raise ValueError('Small complete distinct child encoding denominator differs')
        for child in decoded.values():
            if (child['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                    or child['flags_before'] != child['flags_after']
                    or [e['stage'] for e in child['pipeline']] != PIPELINE):
                raise ValueError('Small child source-derived full pipeline incomplete')
        if decoded['OFF1']['pipeline'] != row['pipeline'] or decoded['OFF1']['artifact']['sha256'] != row['artifact']['sha256']:
            raise ValueError('Small source-derived OFF video bridge differs')
    return {'parents': 2, 'complete_suffixes': 12, 'new_outputs': 8,
            'C_deep': 0, 'D_deep': deep_count, 'formal_RV_training_labels': False}


def evaluation_plan(receipt, config, *, real_GPU_required=True):
    if receipt['status'] != 'SMALL_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT':
        raise ValueError('Complete small core required before scoring')
    if real_GPU_required and (receipt.get('CUDA_initialized') is not True
            or receipt.get('toy_fixture') is not False or receipt.get('complete_video') is not True
            or receipt.get('run_card') != config['card'] or receipt.get('scope') != config):
        raise ValueError('Actual small selected GPU batch/config required')
    if real_GPU_required and receipt.get('wc_settings') != config['historical_wc_settings']:
        raise ValueError('Current GPU official WC settings differ from historical reference')
    if [r['sample_name'] for r in receipt['requests']] != config['sample_names']:
        raise ValueError('Both frozen small scene identities required')
    files, references, pairs, bridges = [], [], [], []
    for row in receipt['requests']:
        reference = config['references'][row['sample_name']]
        if (row['historical_WC_encoded_bridge_pass'] is not True
                or row['context'][1:] != reference['model_and_condition_context']
                or row['artifact']['sha256'] != reference['official_WC']['sha256']):
            raise ValueError('Strict current GPU WC/historical reference bridge required')
        files.append(row['artifact']); references.append(reference['Native35'])
        decoded = {c['label']: c for c in row['decoded_children']}
        for label in ['OFF1', 'C_first', 'D_first']:
            child = decoded[label]
            if child['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE':
                raise ValueError('Small decoded child incomplete')
            files.append(child['artifact'])
        bridges.append({'scene': row['sample_name'], 'reference': row['artifact'], 'candidate': decoded['OFF1']['artifact']})
        for action in ('C', 'D'):
            pairs.append({'scene': row['sample_name'], 'CFG_slot': row['slot'], 'target_call': row['target_call'],
                'action': action, 'reference': reference['Native35'], 'candidate': decoded[action+'_first']['artifact']})
    if (len(files), len(references), len(pairs), len(bridges)) != (8, 2, 4, 2):
        raise ValueError('Small new-output/reference/evaluation denominator differs')
    if len({str(Path(f['path']).resolve()) for f in files+references}) != 10:
        raise ValueError('Small new/reference file paths must remain distinct')
    if real_GPU_required:
        root = Path(config['expected_project_root'])/'outputs'/config['run_id']/'diagnostic'
        for item in files:
            if not Path(item['path']).resolve().is_relative_to(root):
                raise ValueError('New small GPU artifacts must use their independent output identity')
    return {'files': files, 'references': references, 'pairs': pairs, 'bridges': bridges,
            'formal_RV_training_labels': False, 'budget_matched': False, 'physics_or_quality_acceptance': False}
