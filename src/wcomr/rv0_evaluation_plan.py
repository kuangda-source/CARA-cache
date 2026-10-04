"""Complete18-output/eight-C-D Native-relative evaluation plan, no Torch."""
from pathlib import Path

MODES = ['NATIVE_ORIGINAL', 'CACHE_OFF_NATIVE_PATH',
         'WC_ORIGINAL_ROUTER_ABSENT', 'WC_ROUTER_OFF_WITH_SHADOWS']
CHILDREN = ['0_OFF1', '0_C_first', '0_D_first', '1_C_first', '1_D_first']


def evaluation_plan(receipt, config, *, real_GPU_required=True):
    if receipt['status'] != 'FULL_CAUSAL_CORE_COMPLETE_REQUIRES_INDEPENDENT_REAL_GPU_AUDIT':
        raise ValueError('Complete original causal batch required before scoring')
    if real_GPU_required and (receipt.get('CUDA_initialized') is not True
            or receipt.get('toy_fixture') is not False or receipt.get('complete_video') is not True
            or receipt.get('run_card') != config['card'] or receipt.get('scope') != config):
        raise ValueError('Actual selected full GPU batch and bound config required')
    if (receipt['planned_parent_phases'], receipt['planned_suffix_controls'], receipt['planned_encoded_outputs']) != (8, 24, 18):
        raise ValueError('Full causal denominator changed')
    if [r['sample_name'] for r in receipt['requests']] != config['sample_names']:
        raise ValueError('Both paired scene identities required')
    files, pairs, bridges = [], [], []
    for request in receipt['requests']:
        if request['Native_compatibility'] is not True or request['router_OFF_equal'] is not True:
            raise ValueError('Parent Native/cache-off or WC/OFF controls failed')
        if [row['mode'] for row in request['parents']] != MODES:
            raise ValueError('All four original parent modes required')
        for row in request['parents']:
            if row['status'] != 'FULL_PARENT_AND_PLANNED_CONTROLS_COMPLETE':
                raise ValueError('Parent pipeline incomplete')
            files.append(row['artifact'])
        native = request['parents'][0]['artifact']
        off = request['parents'][-1]
        by = {row['label']: row for row in off['decoded_children']}
        if list(by) != CHILDREN or len(off['children']) != 12:
            raise ValueError('Complete branch/control decode outputs required')
        for label in CHILDREN:
            child = by[label]
            if child['status'] != 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE':
                raise ValueError('Decoded child incomplete or guardrail refused')
            files.append(child['artifact'])
        if by['0_OFF1']['artifact']['sha256'] != off['artifact']['sha256']:
            raise ValueError('Encoded OFF bridge differs from full parent')
        bridges.append({'scene': request['sample_name'], 'reference': off['artifact'],
                        'candidate': by['0_OFF1']['artifact'], 'required_identical': True})
        for slot in (0, 1):
            for action in ['C', 'D']:
                pairs.append({'scene': request['sample_name'], 'CFG_slot': slot, 'action': action,
                              'reference': native, 'candidate': by[f'{slot}_{action}_first']['artifact']})
    if len(files) != 18 or len(pairs) != 8 or len(bridges) != 2:
        raise ValueError('Full video fidelity evaluation scope incomplete')
    if len({str(Path(f['path']).resolve()) for f in files}) != 18:
        raise ValueError('Duplicate output paths changed denominators')
    return {'files': files, 'pairs': pairs, 'bridges': bridges, 'formal_RV_training_labels': False,
            'budget_matched': False, 'physics_or_quality_noninferiority': False}
