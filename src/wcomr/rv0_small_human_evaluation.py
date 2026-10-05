"""Human-only strict trajectories and two Native-relative full-video losses."""
from pathlib import Path
from .rv0_small_partial import validate_complete_row


def audit_trajectories(receipt, deep_count):
    if type(deep_count) is not int or deep_count <= 0:
        raise ValueError('Human actual deep count required')
    if (receipt['planned_parent_phases'], receipt['planned_suffix_controls'], receipt['planned_encoded_outputs']) != (1, 6, 4):
        raise ValueError('Human original complement denominator differs')
    if len(receipt['requests']) != 1:
        raise ValueError('Exactly one complete Human request required')
    validate_complete_row(receipt['requests'][0], 1, deep_count)
    return {'parents': 1, 'complete_suffixes': 6, 'new_outputs': 4, 'CFG_slot': 1,
            'C_deep': 0, 'D_deep': deep_count, 'formal_RV_training_labels': False}


def evaluation_plan(receipt, config, *, real_GPU_required=True):
    if receipt['status'] != 'HUMAN_COMPLEMENT_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT':
        raise ValueError('Complete Human core required before scoring')
    if real_GPU_required and (receipt.get('CUDA_initialized') is not True or receipt.get('toy_fixture') is not False
            or receipt.get('complete_video') is not True or receipt.get('run_card') != config['card']
            or receipt.get('scope') != config or receipt.get('wc_settings') != config['historical_wc_settings']):
        raise ValueError('Actual selected Human GPU batch/config/settings required')
    if len(receipt['requests']) != 1 or [r['sample_name'] for r in receipt['requests']] != config['sample_names']:
        raise ValueError('Only the missing Human identity is allowed')
    row = receipt['requests'][0]; reference = config['references'][row['sample_name']]
    if (row['slot'] != 1 or row['target_call'] != 46 or row['historical_WC_encoded_bridge_pass'] is not True
            or row['context'] != [config['run_id']+':'+row['sample_name'], *reference['model_and_condition_context']]
            or row['artifact']['sha256'] != reference['official_WC']['sha256']):
        raise ValueError('Strict Human own-CFG historical Native/WC bridge required')
    decoded = {c['label']: c for c in row['decoded_children']}
    if list(decoded) != ['OFF1', 'C_first', 'D_first'] or len(row['decoded_children']) != 3:
        raise ValueError('All three complete Human child encodes required')
    if any(c['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE' for c in decoded.values()):
        raise ValueError('Human child decode incomplete')
    files = [row['artifact'], *[decoded[n]['artifact'] for n in ['OFF1', 'C_first', 'D_first']]]
    references = [reference['Native35']]
    if len({str(Path(f['path']).resolve()) for f in files+references}) != 5:
        raise ValueError('Human new/reference artifact paths must remain distinct')
    if real_GPU_required:
        root = Path(config['expected_project_root'])/'outputs'/config['run_id']/'diagnostic'
        if any(not Path(f['path']).resolve().is_relative_to(root) for f in files):
            raise ValueError('Human artifacts must use the new independent output identity')
    pairs = [{'scene': row['sample_name'], 'CFG_slot': 1, 'target_call': 46,
              'action': action, 'reference': reference['Native35'], 'candidate': decoded[action+'_first']['artifact']}
             for action in ['C', 'D']]
    return {'files': files, 'references': references, 'pairs': pairs,
            'bridges': [{'scene': row['sample_name'], 'reference': row['artifact'], 'candidate': decoded['OFF1']['artifact']}],
            'original_failed_card_denominator': [2, 12, 8, 2],
            'formal_RV_training_labels': False, 'budget_matched': False, 'physics_or_quality_acceptance': False}
