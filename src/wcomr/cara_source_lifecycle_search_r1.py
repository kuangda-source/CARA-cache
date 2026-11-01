"""Prospective LPIPS search in exactly the V1 19D/22D legal space.

The original RGB-MSE/19D controller and its freeze are unchanged. The caller
owns physical queries, bounded CPU scoring and the measured allocation clock.
This controller consumes only complete two-FIT93-frame queries; it never
reserves a GPU, supplies admission, or interprets a partial query as a score.
"""
import copy
from pathlib import Path
import math
import platform
import random

from .cara_budget_search_r1 import (
    FIT_MEMBERS, PROFILE_FINGERPRINT, SCHEDULE_SHA256, SearchConfig, hc_sample,
)
from .cara_budget_search_journal_r1 import QueryJournal
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest, policy_from_mask, uniform_mask


def legal_swaps(profile, dense, budget):
    if budget not in (19, 22) or len(dense) != budget:
        raise ValueError('Exact registered19D or22D budget required')
    policy_from_mask(profile, dense)
    choices = []
    # In particular, step24 is not an extra protected point. The production
    # grammar, shared with the DP, owns all source-count and age restrictions.
    for remove in sorted(set(dense)-set(profile.protected_dense)):
        for add in sorted(set(range(1, profile.horizon+1))-set(dense)):
            candidate = sorted(set(dense)-{remove} | {add})
            try:
                policy_from_mask(profile, candidate)
            except ValueError:
                continue
            choices.append((remove, add, candidate))
    return choices


def validate_response(request, response, prior_charged, cap_seconds):
    """Check the caller's measured whole-holding-cost boundary and full cohort."""
    if response['request_sha256'] != request['request_sha256']:
        raise ValueError('Response belongs to another original search query')
    before, after = response['charged_before_seconds'], response['charged_after_seconds']
    if (any(type(v) not in (int, float) or not math.isfinite(v) for v in (before, after))
            or not prior_charged <= before <= after or response['cost_cap_seconds'] != cap_seconds):
        raise ValueError('Original monotonic whole-allocation cost charge required')
    if response['status'] == 'NOT_ADMITTED':
        if response['rows'] or response['new_physical_paths'] != 0:
            raise ValueError('A refused query cannot expose partial scores or new physical paths')
        return None, after
    rows = response['rows']
    if (response['status'] != 'COMPLETE' or after > cap_seconds
            or type(response['new_physical_paths']) is not int
            or not 0 <= response['new_physical_paths'] <= 2
            or len(rows) != 2 or {r['member'] for r in rows} != set(FIT_MEMBERS)):
        raise ValueError('Complete query within measured cost cap required')
    for row in rows:
        curve = row['Alex_curve']
        if (row['status'] != 'COMPLETE' or row['candidate_id'] != request['policy']['fingerprint']
                or len(curve) != 93 or any(type(v) not in (int, float)
                    or not math.isfinite(v) or v < 0 for v in curve)):
            raise ValueError('Complete finite93-frame LPIPS for each bound FIT candidate required')
    packet_sha = response['score_packet_sha256']
    if (not isinstance(packet_sha, str) or len(packet_sha) != 64
            or any(c not in '0123456789abcdef' for c in packet_sha)):
        raise ValueError('Bound original complete internal score packet required')
    return math.fsum(math.fsum(r['Alex_curve'])/93/2 for r in rows), after


def search(schedule, profile, budget, config, *, fit_members, context_sha256,
           cap_seconds, evaluate):
    if (tuple(fit_members) != FIT_MEMBERS or digest(schedule) != SCHEDULE_SHA256
            or profile.fingerprint != PROFILE_FINGERPRINT or budget not in (19, 22)
            or not isinstance(config, SearchConfig)
            or config.max_evaluations != 1+config.sa_iterations+config.hc_iterations*config.hc_neighbors
            or min(config.sa_iterations, config.hc_iterations) < 1):
        raise ValueError('Frozen grid/grammar/FIT and complete configured SA+HC quota required')
    if (not isinstance(context_sha256, str) or len(context_sha256) != 64
            or any(c not in '0123456789abcdef' for c in context_sha256)
            or type(cap_seconds) not in (int, float) or not math.isfinite(cap_seconds) or cap_seconds <= 0):
        raise ValueError('Bound context and positive measured calibration-cost cap required')
    rng = random.Random(config.seed)
    current, _ = uniform_mask(schedule, profile, budget)
    best, failure, termination = None, None, None
    queries, charged = [], 0.
    sa_completed = hc_completed = 0

    def assess(dense, phase, iteration):
        nonlocal best, failure, termination, charged
        policy = policy_from_mask(profile, dense)
        request = dict(query_id=len(queries)+1, context_sha256=context_sha256,
            phase=phase, iteration=iteration, FIT_members=list(fit_members), generation_seed=0,
            requested_steps=35, actual_updates=36, D_pair_budget=budget,
            objective='FULL93_INPUT_EQUAL_ALEX_LPIPS', dense=list(dense), policy=policy,
            measured_cost_cap_seconds=cap_seconds)
        request['request_sha256'] = digest(request)
        row = dict(query_id=request['query_id'], phase=phase, iteration=iteration,
            dense=list(dense), policy_fingerprint=policy['fingerprint'],
            request_sha256=request['request_sha256'], status='ATTEMPTED')
        queries.append(row)
        try:
            response = evaluate(copy.deepcopy(request))
            loss, charged = validate_response(request, response, charged, cap_seconds)
            row.update(charged_before_seconds=response['charged_before_seconds'],
                       charged_after_seconds=charged, new_physical_paths=response['new_physical_paths'])
            if loss is None:
                row['status'] = 'NOT_ADMITTED'
                termination = 'MEASURED_COST_ADMISSION_STOP'
                return None
            row.update(status='COMPLETE', input_equal_Alex=loss,
                       score_packet_sha256=response['score_packet_sha256'])
        except Exception as error:
            failure = dict(query_id=request['query_id'], type=type(error).__name__, message=str(error))
            row.update(status='FAILED', failure=failure)
            termination = 'ORIGINAL_QUERY_FAILED_NO_RETRY'
            return None
        key = loss, tuple(dense), request['query_id']
        if best is None or key < (best['input_equal_Alex'], tuple(best['dense']), best['query_id']):
            best = dict(input_equal_Alex=loss, dense=list(dense), policy_fingerprint=policy['fingerprint'],
                        query_id=request['query_id'])
        return loss

    current_loss = assess(current, 'INITIAL', 0)
    temperature = config.temperature_start
    cooling = (config.temperature_end/config.temperature_start)**(1/config.sa_iterations)
    for iteration in range(config.sa_iterations):
        if termination:
            break
        choices = legal_swaps(profile, current, budget)
        if not choices:
            termination = 'NO_LEGAL_SWAPS'
            break
        candidate = rng.choice(choices)[2]
        loss = assess(candidate, 'SA', iteration)
        if termination:
            break
        delta = loss-current_loss
        if delta < 0 or rng.random() < math.exp(-delta/temperature):
            current, current_loss = candidate, loss
        temperature *= cooling
        sa_completed += 1
    if not termination:
        current, current_loss = best['dense'], best['input_equal_Alex']
    for iteration in range(config.hc_iterations):
        if termination:
            break
        choices = legal_swaps(profile, current, budget)
        if not choices:
            termination = 'NO_LEGAL_SWAPS'
            break
        candidates = hc_sample(choices, rng, config.hc_neighbors, config.local_window)
        step_best = None
        for candidate in candidates:
            loss = assess(candidate, 'HC', iteration)
            if termination:
                break
            key = loss, tuple(candidate)
            if step_best is None or key < step_best:
                step_best = key
        if termination:
            break
        if step_best is not None and step_best[0] < current_loss:
            current_loss, mask = step_best
            current = list(mask)
        hc_completed += 1
    if termination is None:
        termination = 'CONFIGURED_SA_HC_FINISHED'
    return dict(schema='CARA_V1_FAIR_LPIPS_SEARCH_R1', objective='FULL93_INPUT_EQUAL_ALEX_LPIPS',
        D_budget=budget, config=vars(config), context_sha256=context_sha256,
        termination=termination, configured_search_finished=termination == 'CONFIGURED_SA_HC_FINISHED',
        best_complete_candidate=best, queries=queries, failure=failure,
        configured_query_limit=config.max_evaluations, requested_queries=len(queries),
        completed_queries=sum(q['status'] == 'COMPLETE' for q in queries),
        SA_iterations_completed=sa_completed, HC_iterations_completed=hc_completed,
        measured_cost_cap_seconds=cap_seconds, measured_charged_seconds=charged,
        complete_physical_terminal_acceptance_required=True, scientific_freeze_written=False,
        GPU_dispatch_ready=False, GPU_submissions=0)


def run_search(directory, schedule, profile, budget, config, *, fit_members, context_sha256,
               cap_seconds, evaluate, create=False, allow_new_queries=False):
    """Recover immutable original query returns without invoking their callbacks."""
    binding = dict(schema='CARA_V1_FAIR_LPIPS_SEARCH_JOURNAL_R1', context_sha256=context_sha256,
        schedule_sha256=digest(schedule), profile_fingerprint=profile.fingerprint,
        FIT_members=list(fit_members), D_budget=budget, config=vars(config),
        measured_cost_cap_seconds=cap_seconds, python_version=platform.python_version(),
        source_sha256={name: file_sha(Path(__file__).parent/name) for name in (
            Path(__file__).name, 'cara_budget_search_journal_r1.py', 'cara_budget_search_r1.py',
            'cara_fast_spec_r1.py', 'policy_generator_r1/interval_grammar.py')})
    with QueryJournal(directory, binding, create=create, allow_new_queries=allow_new_queries) as journal:
        result = search(schedule, profile, budget, config, fit_members=fit_members,
            context_sha256=context_sha256, cap_seconds=cap_seconds,
            evaluate=lambda request: journal.evaluate(request, evaluate))
        if journal.stopped_reason:
            result.update(termination=journal.stopped_reason, configured_search_finished=False)
            result['queries'][-1]['status'] = ('UNKNOWN' if journal.stopped_reason ==
                'ORIGINAL_QUERY_UNKNOWN_NO_DISPATCH' else 'NOT_ADMITTED')
        if journal.visited < journal.persisted_intents:
            raise ValueError('Recorded queries extend beyond deterministic original controller stop')
        result['journal'] = dict(binding_sha256=digest(binding), persisted_intents=journal.persisted_intents,
            new_callback_calls=journal.new_callbacks, reused_callback_returns=journal.reused_returns)
        return result
