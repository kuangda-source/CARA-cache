"""Distinct point20 full14 specification; never reuse original M1 authority."""
from .cara_fast_spec_r1 import digest, policy_from_mask, profile_from
from .cara_read_write_plan_r1 import build as original_point8_design


def build(parent):
    card=original_point8_design(parent)
    profile=profile_from(card['profile'])
    uniform=card['roles']['UNIFORM19_C']['policy']
    eligible=[t for t in range(profile.horizon//2+1,profile.horizon)
              if uniform['actions'][t-1:t+1]==['C','C']]
    if not eligible or eligible[0]!=20:
        raise ValueError('Original-grid first post-midpoint C/C point20 required')
    dense=[t for t,a in enumerate(uniform['actions'],1) if a=='D']
    roles={name:role for name,role in card['roles'].items() if name!='D8_CONTROL'}
    roles['D20_CONTROL']=dict(kind='policy',policy=policy_from_mask(profile,sorted(dense+[20])),physical_pairs=36)
    # Retain the original counterbalanced seven-role order with an explicit
    # D20 control identity. All native/control/corner outputs are new here.
    roles={('D20_CONTROL' if name=='D8_CONTROL' else name):roles['D20_CONTROL' if name=='D8_CONTROL' else name]
           for name in card['roles']}
    for slot in card['physical_matrix']:
        if slot['role']=='D8_CONTROL':
            slot['role']='D20_CONTROL'
            slot['id']=slot['id'].replace('D8_CONTROL','D20_CONTROL')
    card.update(schema='CARA_SOURCE_LIFECYCLE_P0_POINT20_FULL14_R1',roles=roles,target_update=20,
        run_id='cara-source-lifecycle-P0-point20-full14-r1-20261101',
        state='DRAFT_SCOPE_CPU_NOT_WHOLE_ENTRY_OR_GPU_AUTHORIZATION',
        execution='new point20 original guarded requests; point8 original acceptance reused separately',
        point_rule='first_C_C_after_actual_update_midpoint',
        original_point8_complete_ref='reports/cara_read_write_complete_acceptance_r1_20261101.json',
        original_point8_new_scoring=0,original_point8_new_GPU_paths=0,
        predicted_new_source_C_consumers=[21],predicted_source_replaced_after_update=23,
        consumer_predictions_are_actual_results=False,read_write_diagnostic_only=True,
        cross_point_fresh_Native_full93_RGB_identity_check_required=True)
    card['counts'].pop('independent_D8_controls')
    card['counts']['independent_D20_controls']=2
    card['scope_sha256']=digest({k:v for k,v in card.items() if k!='scope_sha256'})
    return card


def validate(card,parent):
    if card!=build(parent):
        raise ValueError('Exact new point20 scope; original M1 scope and authority are not reusable')
    return profile_from(card['profile'])


def execution_scope(parent):
    """Close the scope draft without changing its requests or scientific design."""
    card = build(parent)
    card.update(schema='CARA_SOURCE_LIFECYCLE_P0_POINT20_FULL14_EXECUTION_SCOPE_R1',
                state='CPU_PREPARATION_NOT_GPU_AUTHORIZATION')
    card['scope_sha256'] = digest({k:v for k,v in card.items() if k != 'scope_sha256'})
    return card
