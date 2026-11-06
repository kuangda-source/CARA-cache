"""Complete prospective M1 scope; deterministic design, no experiment authority."""
import copy

from .cara_fast_spec_r1 import digest, policy_from_mask, profile_from, uniform_mask
from .cara_read_write_identity_r1 import for_card


def build(parent):
    profile = profile_from(parent['profile'])
    dense, _ = uniform_mask(parent['schedule'], profile, 19)
    if dense != [1, 2, 3, 4, 5, 6, 7, 16, 19, 22, 23, 24, 25, 26, 27, 28, 29, 31, 36]:
        raise ValueError('Original full36 sigma-coverage initialization required')
    members = parent['FIT']
    if members != ['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199']:
        raise ValueError('Only the two old FIT inputs belong to this pilot')
    policy = policy_from_mask(profile, dense)
    roles = dict(NATIVE35=dict(kind='native', physical_pairs=36),
                 UNIFORM19_C=dict(kind='policy', policy=policy, physical_pairs=36),
                 D8_CONTROL=dict(kind='policy', policy=policy_from_mask(profile, sorted(dense+[8])), physical_pairs=36))
    for corner in ('00', '10', '01', '11'):
        roles['RW'+corner] = dict(kind='point', policy=policy, corner=corner, physical_pairs=37)
    order = list(roles)
    slots = [dict(id=f'FIT{i}_{role}', phase='B', section='B_MAIN', member=member, role=role,
                  seed=0, timing_enabled=True, audit_enabled=False, eligible_clean_time=False)
             for i, member in enumerate(members)
             for role in (order if i == 0 else order[::-1])]
    result = dict(schema='CARA_READ_WRITE_M1_FULL14_PROSPECTIVE_CARD_R2',
        state='CPU_PREPARATION_NOT_GPU_AUTHORIZATION', host='two_card',
        profile=copy.deepcopy(parent['profile']), schedule=copy.deepcopy(parent['schedule']),
        inputs=[copy.deepcopy(row) for row in parent['inputs'] if row['name'] in members],
        settings=copy.deepcopy(parent['roles']['ALLD']['settings']),
        FIT=list(members), CHECK=[], roles=roles, physical_matrix=slots,
        counts=dict(full_requests=14, scientific_four_corner_outputs=8,
                    independent_Uniform_controls=2, independent_D8_controls=2, fresh_Native_references=2,
                    logical_solver_updates=504, physical_model_pairs=512, physical_CFG_branch_calls=1024),
        target_update=8, execution='repeat exact prefix per corner; pay both current actions; original full guarded request',
        reference_reuse=False, shared_prefix_optimization_used=False,
        diagnostic_timing_only=True, GPU_authorized=False, GPU_dispatch_ready=False,
        GPU_submissions=0, ledger_written=False, scientific_method_established=False)
    result['scope_sha256'] = digest(result)
    return result


def validate(card):
    identity = for_card(card)
    if digest({k: v for k, v in card.items() if k != 'scope_sha256'}) != card['scope_sha256']:
        raise ValueError('Read/write scope changed')
    if (len(card['physical_matrix']) != 14 or len(card['inputs']) != 2 or card['CHECK']
            or card['counts']['physical_model_pairs'] != 512 or len(card['FIT']) != 2
            or set(card['roles']) != {'NATIVE35', 'UNIFORM19_C', identity.dense_control,
                                     'RW00', 'RW10', 'RW01', 'RW11'}):
        raise ValueError('Complete prospective14-path scope required')
    for member in card['FIT']:
        slots = [s for s in card['physical_matrix'] if s['member'] == member]
        if len(slots) != 7 or {s['role'] for s in slots} != set(card['roles']):
            raise ValueError('All seven outputs per old FIT are required')
    return profile_from(card['profile'])
