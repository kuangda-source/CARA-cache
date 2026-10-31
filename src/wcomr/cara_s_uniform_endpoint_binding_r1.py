"""Read an existing complete budget freeze and prepare endpoint slot bindings.

This is a CPU preparation component, not a runner or execution authorization.
It never creates a calibration freeze and never opens partial search results.
"""
import copy
from pathlib import Path

from . import cara_budget_complete_r1 as complete
from .cara_budget_search_journal_r1 import read_record
from .cara_fast_spec_r1 import digest, policy_from_mask, profile_from
from .cara_s_uniform_endpoint_plan_r1 import BUDGET_ROLE, NEW_ROLES, require, validate
from .gpu_budget_pool_v2 import sha
from .policy_price_terminal_r1 import record


def bind_existing_freeze(proposal, project, stage, capture, expected_launch_sha256,
                         settlement, freeze_receipt, *, cpu_validation=False):
    """Reaccept all original artifacts before binding the already frozen policy."""
    validate(proposal)
    require('budget_comparator' in proposal, 'Complete joint comparison required')
    require(proposal['scope_sha256'] == digest({k: v for k, v in proposal.items()
                                               if k != 'scope_sha256'}),
            'Original proposal digest differs')
    require(proposal.get('CPU_fixture_only', False) is cpu_validation,
            'CPU proposal cannot enter production binding')
    expected = proposal['budget_comparator']
    launch = record(capture, 'launch')
    require(all(launch[key] == expected['original_' + key]
                for key in ('launch_id', 'run_id', 'source_revision', 'scope_sha256'))
            and launch['host'] == proposal['host'] == 'two_card'
            and launch['gpu_uuid'] == proposal['gpu_uuid']
            and launch['billed_limit_GPUh'] == expected['calibration_hard_GPUh'] == 14,
            'Only the original two-card single14 calibration may supply this policy')
    # The original reader checks release and unique settlement BEFORE any science.
    accepted = complete.accept(project, stage, capture, expected_launch_sha256,
                               settlement, cpu_validation=cpu_validation)
    require(all(freeze_receipt.get(k) == v for k, v in accepted.items()
                if k != 'scientific_freeze_written')
            and freeze_receipt.get('scientific_freeze_written') is (not cpu_validation)
            and freeze_receipt.get('CPU_fixture_freeze_written') is cpu_validation,
            'Original complete once-freeze receipt required')
    name = 'CPU-calibration-frozen-mask.json' if cpu_validation else 'calibration-frozen-mask.json'
    path = Path(project) / 'outputs' / accepted['run_id'] / name
    require(freeze_receipt['freeze_path'] == str(path), 'Original freeze path differs')
    frozen = read_record(path)
    require(sha(path) == freeze_receipt['freeze_sha256'], 'Original freeze hash differs')
    fields = ('launch_id', 'run_id', 'scope_sha256', 'source_revision', 'launch_sha256',
              'context_sha256', 'collection_sha256', 'reader_sha256', 'billing_sha256',
              'actual_GPUh', 'complete_physical_paths', 'complete_two_FIT_queries',
              'selected', 'policy', 'selection_scope', 'CPU_fixture_only')
    expected_freeze = {k: accepted[k] for k in fields}
    expected_freeze.update(schema='CARA_BUDGET_COMPLETE_MASK_FREEZE_R1', new_GPU_authority=False)
    require(frozen == expected_freeze, 'Existing freeze differs from complete original acceptance')
    # Recompile on the endpoint grid; a matching action count alone is insufficient.
    policy = policy_from_mask(profile_from(proposal['profile']), accepted['selected']['dense'])
    require(policy == accepted['policy']
            and policy['fingerprint'] == accepted['selected']['policy_fingerprint']
            and len(policy['actions']) == 36 and policy['actions'].count('D') == 19
            and policy['actions'][23] == 'D', 'Frozen budget policy is not the same protected19D endpoint policy')
    result = map_physical_slots(proposal, policy)
    result.update(schema='CARA_SU19_BUDGET_ENDPOINT_BINDING_PREPARATION_R1',
                  status='CPU_FIXTURE_BINDING_ONLY' if cpu_validation else 'FROZEN_POLICY_BOUND_WHOLE_CPU_PENDING',
                  proposal_scope_sha256=proposal['scope_sha256'],
                  original_calibration=expected_freeze,
                  original_freeze_path=str(path), original_freeze_sha256=sha(path),
                  CPU_fixture_only=cpu_validation, whole_card_CPU_accepted=False,
                  selected_policy_affected_CPU_accepted=False, GPU_authorized=False,
                  GPU_dispatch_ready=False, GPU_submissions=0, ledger_written=False,
                  scientific_freeze_written=False, new_freeze_created=False,
                  original_scores_recomputed=False)
    result['binding_sha256'] = digest(result)
    return result


def map_physical_slots(proposal, budget_policy):
    """Map logical roles onto complete, identical-policy physical classes.

    Equality includes every compiled policy field. Only the two new SU19 roles
    already have fresh paths that may replace budget paths. Historical artifacts
    cannot replace the budget role's fresh timing allocation.
    """
    if proposal.get("endpoint7"):
        from .cara_endpoint7_binding_r1 import mapping
        return mapping(proposal, budget_policy)
    representative = next((role for role in NEW_ROLES
                           if proposal['new_policies'][role] == budget_policy), BUDGET_ROLE)
    roles = {BUDGET_ROLE: representative}
    by_key = {(p['section'], p['member'], p['role'], p['seed']): p['id']
              for p in proposal['physical_matrix']}
    aliases = {}
    physical = []
    for slot in proposal['physical_matrix']:
        target = roles.get(slot['role'], slot['role'])
        canonical = by_key[(slot['section'], slot['member'], target, slot['seed'])]
        aliases[slot['id']] = canonical
        if canonical == slot['id']:
            physical.append(copy.deepcopy(slot))
    formal = copy.deepcopy(proposal['formal_matrix'])
    for row in formal:
        if row['mode'] == 'GENERATE_AND_SCORE':
            target = roles.get(row['role'], row['role'])
            row['physical_slot_id'] = by_key[('FORMAL', row['member'], target, 0)]
            row['metric_alias_of_role'] = target if target != row['role'] else None
            row['counts_as_independent_sample_from_alias'] = False
    ids = {p['id'] for p in physical}
    require(set(aliases.values()) == ids and len(formal) == 24
            and len(ids) == len(physical) == (32 if representative == BUDGET_ROLE else 25),
            'Complete deterministic physical equivalence mapping required')
    return dict(budget_policy=copy.deepcopy(budget_policy), budget_role_representative=representative,
                proposal_slot_aliases=aliases, physical_matrix=physical, formal_matrix=formal,
                identity_controls=copy.deepcopy(proposal['identity_controls']),
                counts=dict(logical_quality_positions=24, reused_metric_positions=12,
                            new_logical_quality_positions=12, new_GPU_paths=len(physical),
                            unique_new_scoring_pairs=len({r['physical_slot_id'] for r in formal
                                                         if r['mode'] == 'GENERATE_AND_SCORE'}),
                            clean_timing_samples=sum(p['eligible_clean_time'] for p in physical)),
                final_quote_must_use_unique_physical_paths=True)
