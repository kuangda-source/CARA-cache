"""Prospective seven-role UniPC cards, reusing accepted artifacts without rescoring."""
import copy
import math

from .cara_fast_spec_r1 import digest, policy_from_mask, profile_from
from .cara_s_uniform_endpoint_plan_r1 import require

NEW_ROLES = ('SU19_BR_DIAG_C', 'SU19_CFG_C', 'BUDGET_SEARCH19_C', 'F19_RISKSWAP_C')
REUSED_ROLES = ('F19_C', 'UNIFORM19_C', 'F19_A1')


def build(base, old_proposal, diagnostic, accepted, frozen, *, same_batch_f19):
    require(base['scope_sha256'] == old_proposal['parent_B36_scope_sha256'], 'B36 parent differs')
    require(accepted['complete_search_accepted'] and accepted['scientific_freeze_written']
            and not accepted['CPU_fixture_only'] and accepted['complete_physical_paths'] == 112
            and accepted['complete_two_FIT_queries'] == 51, 'Original complete112/51 acceptance required')
    for key in ('launch_id', 'run_id', 'scope_sha256', 'source_revision', 'selected', 'policy',
                'collection_sha256', 'billing_sha256', 'actual_GPUh'):
        require(accepted[key] == frozen[key], 'Original accepted freeze differs: ' + key)
    choices = diagnostic['origins']['F19_C']['choices']
    require(diagnostic['original_F19_reproduced_exact'] and not diagnostic['endpoint_results_used']
            and len({c['policy_fingerprint'] for c in choices.values()}) == 1,
            'Original FIT-only F19 common swap required')
    choice = choices['CFG']
    require((choice['remove'], choice['add']) == (21, 35), 'Original F19 swap differs')
    profile = profile_from(base['profile'])
    policies = copy.deepcopy(old_proposal['new_policies'])
    policies['BUDGET_SEARCH19_C'] = policy_from_mask(profile, accepted['selected']['dense'])
    require(policies['BUDGET_SEARCH19_C'] == frozen['policy'], 'Budget policy compilation differs')
    policies['F19_RISKSWAP_C'] = policy_from_mask(profile, choice['dense'])
    require(policies['F19_RISKSWAP_C']['fingerprint'] == choice['policy_fingerprint'], 'Swap identity differs')
    require(len({p['fingerprint'] for p in policies.values()}) == 4, 'New roles must be distinct')
    require(all(p['actions'].count('D') == 19 and len(p['actions']) == 36 for p in policies.values()),
            'All new roles require the original19D/36-update contract')
    roles = {r: copy.deepcopy(base['roles'][r]) for r in ('NATIVE35', 'ALLD') + REUSED_ROLES}
    roles.update({r: dict(kind='policy', requested_steps=35, policy=p) for r, p in policies.items()})
    members = base['FIT'] + base['CHECK']
    timing_roles = ('NATIVE35', 'F19_A1') + NEW_ROLES + (('F19_C',) if same_batch_f19 else ())
    repeats = NEW_ROLES + (('F19_C',) if same_batch_f19 else ())
    physical = []
    count = 46 if same_batch_f19 else 39

    def add(section, member, role, clean=False):
        physical.append(dict(id=f'E1_{count}_{len(physical)+1:03d}', phase='B', section='B_' + section,
            purpose=section, member=member, role=role, seed=0, timing_enabled=True,
            audit_enabled=False, eligible_clean_time=clean))

    for role in timing_roles:
        add('WARM', members[0], role)
    add('ALLD_EQUIVALENCE', members[0], 'ALLD')
    for i, member in enumerate(members):
        for role in timing_roles[i:] + timing_roles[:i]:
            add('FORMAL' if role in NEW_ROLES else 'REPLAY_CONTROL', member, role, True)
    for i, member in enumerate(base['CHECK']):
        for role in repeats[::1 if i == 0 else -1]:
            add('REPEAT', member, role, True)
    formal = [copy.deepcopy(r) for r in old_proposal['formal_matrix'] if r['role'] in REUSED_ROLES]
    for member in members:
        for role in NEW_ROLES:
            slot = next(s for s in physical if (s['purpose'], s['member'], s['role']) == ('FORMAL', member, role))
            formal.append(dict(member=member, role=role, mode='GENERATE_AND_SCORE',
                               physical_slot_id=slot['id'], seed=0))
    controls = copy.deepcopy(old_proposal['identity_controls'])
    if same_batch_f19:
        for row in formal:
            if row['role'] == 'F19_C':
                controls.append(dict(kind='FRESH_VS_ORIGINAL_DECODED_RGB', member=row['member'], role='F19_C',
                    original_score_id=row['score_id'], original_decoded_RGB_sha256=row['decoded_RGB_sha256'][0]))
    card = copy.deepcopy(base)
    card.pop('scope_sha256')
    card.update(schema='CARA_ENDPOINT7_PROSPECTIVE_REQUEST_CARD_R1', roles=roles,
        physical_matrix=physical, formal_matrix=formal, scientific_roles=list(REUSED_ROLES + NEW_ROLES),
        reference_sources=copy.deepcopy(old_proposal['reference_sources']), identity_controls=controls,
        original_B36_scope_sha256=base['scope_sha256'], original_budget_freeze_sha256=accepted['freeze_sha256'],
        same_batch_F19=same_batch_f19, CPU_fixture_only=False, GPU_authorized=False,
        GPU_dispatch_ready=False, endpoint_scope_selected_by_user=False,
        role_aliases={'SU19_BR_C': 'SU19_BR_DIAG_C', 'SU19_DIAG_C': 'SU19_BR_DIAG_C',
                     'F19_S_BR_C': 'F19_RISKSWAP_C', 'F19_S_DIAG_C': 'F19_RISKSWAP_C', 'F19_S_CFG_C': 'F19_RISKSWAP_C'},
        counts=dict(physical_paths=count, logical_quality_positions=28, reused_scores=12, new_scores=16,
                    warm=len(timing_roles), allD=1, formal_new=16,
                    replay_controls=12 if same_batch_f19 else 8, repeats=len(repeats)*2),
        new_GPU_submissions=0, ledger_written=False)
    card['scope_sha256'] = digest(card)
    validate(card)
    return card


def validate(card):
    require(card['scope_sha256'] == digest({k: v for k, v in card.items() if k != 'scope_sha256'}), 'Altered E1 card')
    rows = card['physical_matrix']
    count = 46 if card['same_batch_F19'] else 39
    require(len(rows) == len({r['id'] for r in rows}) == count, 'Incomplete E1 physical denominator')
    require(len(card['formal_matrix']) == 28 and set(card['scientific_roles']) == set(REUSED_ROLES + NEW_ROLES),
            'Seven complete logical roles required')
    require(set(r['member'] for r in rows) == set(card['FIT'] + card['CHECK']) and all(r['seed'] == 0 for r in rows),
            'Only original four CAL seed0 permitted')
    require(all(not r['audit_enabled'] for r in rows), 'Diagnostic copies cannot enter clean timing')
    for role in REUSED_ROLES + NEW_ROLES:
        require(card['roles'][role]['policy']['actions'].count('D') == 19, 'Wrong D budget')


def quote(card, slowest_native_seconds):
    validate(card)
    paths = len(card['physical_matrix'])
    components = dict(generation_at_slowest_old_Native=paths*slowest_native_seconds,
        artifact_copy_save_hash=paths*60, producer_readback=1800,
        admission_and_model_load=1800, stop_and_release=600)
    forecast = sum(components.values())/3600
    hard = math.ceil(forecast*1.15*4)/4
    return dict(status='COMPLETE_SCOPE_ENGINEERING_QUOTE_NOT_FRESH_ADMISSION', scope_sha256=card['scope_sha256'],
        physical_paths=paths, host='two_card', components_seconds=components, forecast_GPUh=forecast,
        proposed_hard_GPUh=hard, hard_limit_rule='15% above forecast, rounded up to0.25GPUh',
        margin_seconds=hard*3600-sum(components.values()), slowest_original_Native_request_seconds=slowest_native_seconds,
        all_native_proxy_is_proven_bound=False, actual_new_policy_timing_measured=False,
        postrelease_CPU=dict(new_pairs=16, reused_pairs=12, threads=2, memory_GiB=8,
                             wall_limit_hours=2, max_vCPUh=4, GPUh=0),
        storage=dict(private_quota_GiB=64, minimum_filesystem_free_GiB=80, low_water_GiB=8,
                     decoded_float32_RGB_one_at_a_time_GiB=3*93*432*768*4/2**30,
                     bulk_preencode_RGB_persistence=False),
        stop_release_margin_seconds=600, temperature_stop_C=90, GPU_authorized=False,
        fresh_ledger_checked=False, fresh_resources_checked=False, GPU_dispatch_ready=False)
