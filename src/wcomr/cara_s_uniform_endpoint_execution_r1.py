"""Complete endpoint collection using the unchanged production request routes.

Dispatch/admission and postrelease scientific acceptance are separate boundaries.
Existing collections are inspected without invoking an execution callback.
"""
import copy
from pathlib import Path

from .cara_budget_search_journal_r1 import read_record
from .cara_fast_spec_r1 import digest
from .cara_s_uniform_endpoint_binding_r1 import map_physical_slots
from .cara_s_uniform_endpoint_plan_r1 import BUDGET_ROLE, require, validate
from .gpu_budget_pool_v2 import sha


def request_card(proposal, bound, base):
    validate(proposal)
    require(proposal['scope_sha256'] == digest({k: v for k, v in proposal.items() if k != 'scope_sha256'})
            and bound['proposal_scope_sha256'] == proposal['scope_sha256']
            and bound['binding_sha256'] == digest({k: v for k, v in bound.items() if k != 'binding_sha256'})
            and base['scope_sha256'] == proposal['parent_B36_scope_sha256'],
            'Exact proposal, binding and original B36 parent required')
    mapped = map_physical_slots(proposal, bound['budget_policy'])
    require(all(bound[k] == v for k, v in mapped.items()), 'Bound physical equivalence mapping differs')
    card = copy.deepcopy(base)
    card.pop('scope_sha256')
    roles = {name: copy.deepcopy(base['roles'][name]) for name in ('NATIVE35', 'F19_A1', 'ALLD')}
    for role, policy in {**proposal['new_policies'], BUDGET_ROLE: bound['budget_policy']}.items():
        roles[role] = dict(kind='policy', requested_steps=35, policy=copy.deepcopy(policy))
    if proposal.get('endpoint7'):
        roles['F19_C'] = copy.deepcopy(base['roles']['F19_C'])
        card['endpoint7'] = True
    slots = [dict(s, phase='B', section='B_' + s['section'], purpose=s['section'])
             for s in mapped['physical_matrix']]
    card.update(schema='CARA_SU19_BUDGET_ENDPOINT_REQUEST_CARD_R1', roles=roles,
                physical_matrix=slots, formal_matrix=copy.deepcopy(mapped['formal_matrix']),
                endpoint_proposal_sha256=proposal['scope_sha256'],
                endpoint_binding_sha256=bound['binding_sha256'],
                original_budget_freeze_sha256=bound['original_freeze_sha256'],
                CPU_fixture_only=bound['CPU_fixture_only'], GPU_dispatch_ready=False)
    card['scope_sha256'] = digest(card)
    return card


def make_requests(card, bound, *, cpu_validation=False, production_context=None, **kwargs):
    from .cara_fast_requests_r2 import Requests
    require(card['endpoint_binding_sha256'] == bound['binding_sha256']
            and card['CPU_fixture_only'] is cpu_validation
            and bound['CPU_fixture_only'] is cpu_validation,
            'Original endpoint binding and CPU/production mode required')
    if not cpu_validation:
        context = production_context or {}
        require(bound['status'] == 'FROZEN_POLICY_BOUND_WHOLE_CPU_PENDING'
                and bound['original_calibration']['CPU_fixture_only'] is False
                and context.get('phase') == 'ENDPOINT'
                and context.get('physical_paths') == len(card['physical_matrix'])
                and context.get('endpoint_binding_sha256') == bound['binding_sha256']
                and context.get('new_endpoint_authorization') is True
                and context.get('original_budget_freeze_sha256') == bound['original_freeze_sha256'],
                'Separate complete endpoint admission required')
    # Requests' B guard consumes the prior released calibration, not an A32 rewrite.
    frozen = dict(scope_sha256=card['scope_sha256'], phase_A_GPU_released=True, selected={})
    return Requests(card=card, frozen=frozen, cpu_validation=cpu_validation,
                    production_context=production_context, **kwargs)


def check_collection(card, state, *, cpu_validation):
    require(state['phase'] == 'B' and state['scope_sha256'] == card['scope_sha256']
            and [r['slot'] for r in state['rows']] == card['physical_matrix'],
            'Complete ordered endpoint denominator required')
    require(state['status'] == 'TERMINAL' and all(r['status'] == 'COMPLETE' for r in state['rows']),
            'Incomplete endpoint collection; no scientific acceptance or replay')
    for row in state['rows']:
        slot, result = row['slot'], row['result']
        require(result['slot_id'] == slot['id'] and result['role'] == result['concrete_role'] == slot['role']
                and result['scope_sha256'] == card['scope_sha256'] and result['CPU_fixture'] is cpu_validation
                and result['solver_steps'] == result['guided_pairs'] == 36
                and result['audit_enabled'] is False
                and all(result[k] == 0 for k in ('in_timing_guided_copies', 'in_timing_hashes', 'research_checkpoints'))
                and 0 < result['T_DD'] <= result['T_request'], 'Complete clean route identity differs')
        policy = card['roles'][slot['role']].get('policy')
        if policy:
            require([h['actual'] for h in result['semantic_history']] == policy['actions']
                    and all(h['fallback_reason'] is None for h in result['semantic_history']),
                    'Original policy actions or fallback differs')
    return digest(state)


def execute(adapter, output, *, before_request, save):
    from .wc_time_collection_r1 import collect_phase
    if adapter.card.get('schema') == 'CARA_ENDPOINT7_PROSPECTIVE_REQUEST_CARD_R1':
        from .cara_endpoint7_plan_r1 import validate as validate_seven
        validate_seven(adapter.card)
        require(adapter.cpu_validation and adapter.card['CPU_fixture_only'],
                'Seven-role collection is CPU preparation only; production lifecycle is not yet bound')
        allowed_counts = (39, 46)
    elif adapter.card.get('endpoint7'):
        require(adapter.card['schema'] == 'CARA_SU19_BUDGET_ENDPOINT_REQUEST_CARD_R1'
                and len(adapter.card['formal_matrix']) == 28
                and adapter.card['scope_sha256'] == digest({k: v for k, v in adapter.card.items() if k != 'scope_sha256'}),
                'Bound seven-role request card required')
        allowed_counts = (46,)
    else:
        allowed_counts = (25, 32)
    require(not adapter.seen and len(adapter.card['physical_matrix']) in allowed_counts,
            'Fresh complete endpoint adapter required; never resume execution')

    class Checked:
        def __getattr__(self, name):
            return getattr(adapter, name)

        def __call__(self, slot, path):
            result = adapter(slot, path)
            require(result['status'] == 'COMPLETE', 'Endpoint request failed: ' + result['status'])
            video = Path(result['video_path'])
            require(video.is_file() and not video.is_symlink(), 'Original endpoint output required')
            result['endpoint_video_artifact'] = dict(path=str(video), sha256=sha(video), bytes=video.stat().st_size)
            return result

    def no_diagnostics(rows):
        raise ValueError('Endpoint cannot execute old calibration diagnostics')

    state = collect_phase(Checked(), 'B', output, before_request=before_request,
                          save=save, after_diagnostics=no_diagnostics)
    check_collection(adapter.card, state, cpu_validation=adapter.cpu_validation)
    return state


def inspect_original(card, path, *, cpu_validation):
    """Read-only collection recovery; never resumes or retries an attempted slot."""
    state = read_record(Path(path))
    require(state['scope_sha256'] == card['scope_sha256']
            and [r['slot'] for r in state['rows']] == card['physical_matrix'],
            'Original collection identity differs')
    counts = {name: sum(r['status'] == name for r in state['rows'])
              for name in ('COMPLETE', 'TECH_FAILED', 'RUNNING', 'NOT_REACHED')}
    require(sum(counts.values()) == len(card['physical_matrix']), 'Unknown row state')
    if state['status'] == 'TERMINAL':
        check_collection(card, state, cpu_validation=cpu_validation)
        for row in state['rows']:
            for artifact in (row['tensor_artifact'], row['result']['endpoint_video_artifact']):
                p = Path(artifact['path'])
                require(p.is_file() and not p.is_symlink() and p.stat().st_size == artifact['bytes']
                        and sha(p) == artifact['sha256'], 'Original endpoint artifact changed')
        status = 'ORIGINAL_COMPLETE_COLLECTION_RECOVERED_NOT_SCIENTIFIC_ACCEPTANCE'
    else:
        require(state['status'] in ('RUNNING', 'FAILED_NO_REPLAY'), 'Unknown collection state')
        status = 'ORIGINAL_FAILED_NO_REPLAY' if state['status'] == 'FAILED_NO_REPLAY' else 'ORIGINAL_RUNNING_OR_UNKNOWN_NO_REPLAY'
    return dict(status=status, counts=counts, collection_sha256=sha(path),
                physical_paths=len(card['physical_matrix']), GPU_submissions=0,
                dispatch_allowed=False, scientific_accepted=False, ledger_written=False)
