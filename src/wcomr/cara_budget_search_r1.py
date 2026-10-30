"""CPU search component for the proposed BudCache-style CARA-C comparator.

This module supplies no model loader, transport or GPU authorization. A future
production evaluator needs its own complete card, durable query recovery and
accepted source/teacher identities before using the controller.
"""
import copy
from dataclasses import dataclass
import math
import random

from .cara_fast_spec_r1 import digest, policy_from_mask, uniform_mask


# R1 is the registered Cosmos36/19D adaptation, not a generic search API.
# These identities are from the original R2 RUN_SPEC, checked by CPU acceptance.
SCHEDULE_SHA256 = '65ffb14b08fa40b48ed4d19eccd9ccc11bf30d3b9b3675aada7e991fea3aaeea'
PROFILE_FINGERPRINT = '0273c501d6f8383b81900d113dc68f9a304feed444dfc5c3d29184ec6c2e5889'
FIT_MEMBERS = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199')


@dataclass(frozen=True)
class SearchConfig:
    seed: int
    max_evaluations: int
    sa_iterations: int = 200
    hc_iterations: int = 5
    temperature_start: float = 0.1
    temperature_end: float = 1e-4
    hc_neighbors: int = 20
    local_window: int = 3

    def __post_init__(self):
        integers = (self.seed, self.max_evaluations, self.sa_iterations,
                    self.hc_iterations, self.hc_neighbors, self.local_window)
        if (any(type(value) is not int for value in integers)
                or self.max_evaluations < 1 or self.sa_iterations < 0 or self.hc_iterations < 0
                or self.hc_neighbors < 1 or self.local_window < 0):
            raise ValueError('Finite positive query cap and valid search counts required')
        temperatures = (self.temperature_start, self.temperature_end)
        if (any(type(value) not in (int, float) or not math.isfinite(value) for value in temperatures)
                or not 0 < self.temperature_end <= self.temperature_start):
            raise ValueError('Finite positive decreasing search temperatures required')


def initial_mask(schedule, profile):
    if profile.horizon != 36 or schedule['actual_updates'] != 36:
        raise ValueError('This proposed comparator uses the registered 36-update grid')
    # Preserve the already registered Uniform19 initialization. Adding step24 to
    # farthest-point seeds would change the entire mask, even though the original
    # Uniform19 already contains it. Protect it only during subsequent swaps.
    dense, _ = uniform_mask(schedule, profile, 19)
    if 24 not in dense:
        raise ValueError('Registered Uniform19 must already contain protected step24')
    policy_from_mask(profile, dense)
    return dense


def legal_swaps(profile, dense):
    """Full supported swap neighborhood of the CURRENT mask, not only of F19."""
    protected = set(profile.protected_dense) | {24}
    if len(dense) != 19 or not protected <= set(dense):
        raise ValueError('The 19D budget and common protected steps are required')
    policy_from_mask(profile, dense)
    choices = []
    for remove in sorted(set(dense)-protected):
        for add in sorted(set(range(1, profile.horizon+1))-set(dense)):
            candidate = sorted((set(dense)-{remove}) | {add})
            try:
                policy_from_mask(profile, candidate)
            except ValueError:
                continue  # The existing production grammar owns age/anchor validity.
            choices.append((remove, add, candidate))
    return choices


def hc_sample(choices, rng, maximum, window):
    local = {(remove, add) for remove, add, _ in choices if abs(remove-add) <= window}
    # Preserve the official sampled local/global HC design. Canonical sorting and
    # a private RNG make the adapted controller independent of process RNG state.
    for _ in range(maximum*2):
        remove, add, _ = rng.choice(choices)
        if abs(remove-add) > window:
            local.add((remove, add))
    selected = rng.sample(sorted(local), min(maximum, len(local)))
    lookup = {(remove, add): dense for remove, add, dense in choices}
    return [lookup[pair] for pair in selected]


def search(schedule, profile, config, *, fit_members, context_sha256, evaluate):
    """Run a bounded search using complete, equally weighted FIT objectives.

    One evaluation means one complete cohort, not one video. Attempted cohort
    requests consume the cap even when evaluation fails. Teacher generation is
    a separate physical cost; this cap must not be used as a whole-card quote.
    """
    members = tuple(fit_members)
    if members != FIT_MEMBERS:
        raise ValueError('Exact registered FIT identities and order required; no CHECK/final inputs')
    if digest(schedule) != SCHEDULE_SHA256 or profile.fingerprint != PROFILE_FINGERPRINT:
        raise ValueError('Original registered schedule and profile required')
    if (not isinstance(context_sha256, str) or len(context_sha256) != 64
            or any(c not in '0123456789abcdef' for c in context_sha256)):
        raise ValueError('Bound evaluator context digest required')
    rng = random.Random(config.seed)
    current = initial_mask(schedule, profile)
    queries = []
    best = None
    termination = None
    failure = None
    sa_completed = hc_completed = 0

    def assess(dense, phase, iteration):
        nonlocal best, termination, failure
        if len(queries) >= config.max_evaluations:
            termination = 'QUERY_CAP_REACHED'
            return None
        policy = policy_from_mask(profile, dense)
        request = dict(query_id=len(queries)+1, context_sha256=context_sha256,
            phase=phase, iteration=iteration, FIT_members=list(members), generation_seed=0,
            requested_steps=35, actual_updates=36, D_pair_budget=19,
            dense=list(dense), policy=policy)
        request_sha = digest(request)
        request['request_sha256'] = request_sha
        record = dict(query_id=request['query_id'], phase=phase, iteration=iteration,
            dense=list(dense), policy_fingerprint=policy['fingerprint'],
            request_sha256=request_sha, requested_endpoint_paths=len(members), status='ATTEMPTED')
        queries.append(record)
        try:
            response = evaluate(copy.deepcopy(request))
            if response['request_sha256'] != request_sha:
                raise ValueError('Evaluator response belongs to another query/context')
            rows = response['rows']
            if (len(rows) != len(members) or {row['member'] for row in rows} != set(members)
                    or any(row['status'] != 'COMPLETE' or type(row['RGB_MSE']) not in (int, float)
                        or not math.isfinite(row['RGB_MSE']) or row['RGB_MSE'] < 0 for row in rows)):
                raise ValueError('Complete finite two-FIT endpoint objective required')
            by_member = {row['member']: row['RGB_MSE'] for row in rows}
            loss = math.fsum(by_member[member]/len(members) for member in members)
            if not math.isfinite(loss):
                raise ValueError('Nonfinite aggregate endpoint objective')
            record.update(status='COMPLETE', RGB_MSE_by_member=by_member, mean_RGB_MSE=loss)
        except Exception as error:
            failure = dict(type=type(error).__name__, message=str(error), query_id=record['query_id'])
            record.update(status='FAILED', failure=failure)
            termination = 'EVALUATION_FAILED_NO_RETRY'
            return None
        if best is None or loss < best['mean_RGB_MSE']:
            best = dict(dense=list(dense), policy_fingerprint=policy['fingerprint'],
                mean_RGB_MSE=loss, query_id=record['query_id'])
        return loss

    current_loss = assess(current, 'INITIAL', 0)
    cooling = (config.temperature_end/config.temperature_start)**(1/max(config.sa_iterations, 1))
    temperature = config.temperature_start
    for iteration in range(config.sa_iterations):
        if termination:
            break
        choices = legal_swaps(profile, current)
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
        current, current_loss = best['dense'], best['mean_RGB_MSE']
    for iteration in range(config.hc_iterations):
        if termination:
            break
        choices = legal_swaps(profile, current)
        if not choices:
            termination = 'NO_LEGAL_SWAPS'
            break
        candidates = hc_sample(choices, rng, config.hc_neighbors, config.local_window)
        step_best = None
        for candidate in candidates:
            loss = assess(candidate, 'HC', iteration)
            if termination:
                break
            if step_best is None or loss < step_best[1]:
                step_best = (candidate, loss)
        if termination:
            break
        if step_best is not None and step_best[1] < current_loss:
            current, current_loss = step_best
        hc_completed += 1
    if termination is None:
        termination = 'CONFIGURED_SEARCH_FINISHED'
    unique = len({tuple(row['dense']) for row in queries})
    return dict(version='CARA_BUDCACHE_STYLE_SEARCH_COMPONENT_R1', termination=termination,
        configured_search_finished=termination == 'CONFIGURED_SEARCH_FINISHED',
        convergence_claimed=False, best_complete_candidate=best, failure=failure, queries=queries,
        attempted_cohort_evaluations=len(queries), completed_cohort_evaluations=sum(row['status']=='COMPLETE' for row in queries),
        requested_endpoint_paths=sum(row['requested_endpoint_paths'] for row in queries),
        unique_candidate_masks=unique, duplicate_candidate_calls=len(queries)-unique,
        SA_iterations_completed=sa_completed, HC_iterations_completed=hc_completed,
        config=dict(vars(config)), context_sha256=context_sha256,
        teacher_cost_included=False, evaluation_memoization=False,
        durable_production_recovery_implemented=False, GPU_dispatch_ready=False)
