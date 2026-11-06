"""Complete prospective P1 identities; no GPU authorization or dispatch."""
import copy

from .cara_budget_search_r1 import SearchConfig
from .cara_fast_spec_r1 import digest, profile_from, policy_from_mask, uniform_mask
from .cara_source_lifecycle_design_r1 import calibration_design
from .cara_source_lifecycle_estimation_r1 import FAMILIES

SEARCH_CONFIG = SearchConfig(42, 12, sa_iterations=6, hc_iterations=1, hc_neighbors=5)
BASELINES = ('NATIVE35', 'UNIFORM19_C', 'UNIFORM22_C', 'F19_C', 'F19_A1', 'BUDGET_SEARCH19_C')


def build(parent, design):
    profile = profile_from(parent['profile'])
    if (digest({k: v for k, v in parent.items() if k != 'scope_sha256'}) != parent['scope_sha256']
            or design != calibration_design(parent['schedule'], profile, parent['FIT'])):
        raise ValueError('Exact original E1 source roles, legal grid and fixed64 design required')
    roles = {name: copy.deepcopy(parent['roles'][name]) for name in BASELINES if name != 'UNIFORM22_C'}
    mask, _ = uniform_mask(parent['schedule'], profile, 22)
    roles['UNIFORM22_C'] = dict(kind='policy', requested_steps=35, policy=policy_from_mask(profile, mask))
    controls = [dict(id='warm-Native', kind='native', member=parent['FIT'][0], timing='DIAGNOSTIC'),
                dict(id='warm-Uniform19', kind='policy', role='UNIFORM19_C',
                     member=parent['FIT'][0], timing='DIAGNOSTIC')]
    for i, member in enumerate(parent['FIT']+parent['CHECK']):
        controls.append(dict(id=f'control-allD-{i}', kind='allD', member=member, timing='DIAGNOSTIC',
                             compare_to='NATIVE35', compare_scope='FULL_LATENT_AND_PRE_ENCODE_RGB'))
    for i, member in enumerate(parent['FIT']):
        for role in ('NATIVE35', 'UNIFORM19_C'):
            controls.append(dict(id=f'control-OFF-{role}-{i}', kind=roles[role]['kind'], role=role,
                member=member, timing='OFF', compare_to=role, compare_scope='FULL_LATENT_AND_PRE_ENCODE_RGB'))
        for budget in (19, 22):
            source = next(p for p in design['parents'] if p['D'] == budget and p['rule'] == 'SIGMA_FARTHEST')
            controls.append(dict(id=f'control-parent-K{budget}-{i}', kind='policy', member=member,
                policy=copy.deepcopy(source['policy']), timing='DIAGNOSTIC',
                compare_parent=source['id'], compare_scope='FULL_LATENT_AND_PRE_ENCODE_RGB'))
    if len(controls) != 14:
        raise ValueError('Whole P1 controls must stay explicit')
    card = dict(schema='CARA_SOURCE_LIFECYCLE_P1_WHOLE_SCOPE_R1',
        state='PRODUCTION_COMBINATION_PREPARATION_NO_GPU_AUTHORITY',
        scientific_parent_scope_sha256=parent['scope_sha256'], design_scope_sha256=design['scope_sha256'],
        profile=copy.deepcopy(parent['profile']), schedule=copy.deepcopy(parent['schedule']),
        inputs=copy.deepcopy(parent['inputs']), FIT=list(parent['FIT']), CHECK=list(parent['CHECK']),
        roles=roles, settings=copy.deepcopy(parent['roles']['ALLD']['settings']),
        families=list(FAMILIES), D_budgets=[19, 22], top_k=3, calibration_design=copy.deepcopy(design),
        search_config=dict(vars(SEARCH_CONFIG)), baseline_roles=list(BASELINES), controls=controls,
        semantic_positions=dict(source_parents=8, fresh_baselines=24, candidate_FIT_max=36,
            selected_candidate_CHECK=12, search_FIT_max=48, selected_search_CHECK=4, controls=14),
        physical_paths_upper=146, original132_path_draft_omitted_controls=14,
        candidate_aliases='same_full_policy_input_seed_and_clean_class_only; retain_every_semantic_position',
        search_not_reached_positions='retain_budget_stop_not_reached_denominator',
        scalar_pairs=352, other_pairs_per_request=36,
        internal_scoring='complete_two_FIT_all93_fixed_Fidelity_v2; CPU_GPU_hidden',
        final_scientific_acceptance='whole_original_terminal_release_unique_settlement_then_reuse_sealed_metrics',
        old_CHECK_exposed=True, old_search_RGB_MSE_freeze_unchanged=True,
        final_and_reserve_accessed=False, GPU_authorized=False, GPU_dispatch_ready=False,
        whole_quote_ready=False, GPU_submissions=0, ledger_written=False)
    card['scope_sha256'] = digest(card)
    return card


def validate(card):
    if (card['schema'] != 'CARA_SOURCE_LIFECYCLE_P1_WHOLE_SCOPE_R1'
            or digest({k: v for k, v in card.items() if k != 'scope_sha256'}) != card['scope_sha256']
            or card['physical_paths_upper'] != 146 or card['original132_path_draft_omitted_controls'] != 14
            or card['families'] != list(FAMILIES) or card['D_budgets'] != [19, 22]
            or card['top_k'] != 3 or card['search_config'] != vars(SEARCH_CONFIG)
            or card['final_and_reserve_accessed'] is not False):
        raise ValueError('Exact prospective complete P1 scope required')
    return profile_from(card['profile'])
