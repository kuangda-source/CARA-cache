"""Fixed V1 scalar estimation and parent-held-out diagnostics, before video selection.

This boundary checks complete label structure and same-state provenance claims.
The production collector and its original terminal acceptance must separately
establish those claims. Scalar fitting cannot authorize GPU work or accept video.
"""
from dataclasses import dataclass
from functools import lru_cache
import math

import numpy as np

from .cara_fast_spec_r1 import digest, profile_from
from .cara_source_lifecycle_planner_r1 import plan

FAMILIES = ('stage', 'stage_age', 'stage_age_previous_gap')
FEATURE_NAMES = ('1', 'sigma', 'sigma_squared', 'sigma_age', 'sigma_age_squared',
                 'sigma_times_age', 'previous_sigma_gap', 'previous_gap_squared',
                 'sigma_times_previous_gap', 'age_times_previous_gap')
WIDTH = dict(zip(FAMILIES, (3, 6, 10)))
RIDGE = 1e-4


@dataclass(frozen=True)
class Sample:
    member: str
    parent: str
    t: int
    a: int
    b: int
    coordinates: tuple
    target: float


def coordinates(sigmas, t, a, b):
    sigma = sigmas[t-1]
    return sigma, abs(sigma-sigmas[b-1]), abs(sigmas[b-1]-sigmas[a-1])


def features(point, family):
    sigma, age, gap = point
    return (1., sigma, sigma*sigma, age, age*age, sigma*age,
            gap, gap*gap, sigma*gap, age*gap)[:WIDTH[family]]


def complete_samples(packet, design, schedule):
    """Bind exactly the preregistered64 rows; never fit old normalized S labels."""
    if (packet.get('schema') != 'CARA_V1_SAME_STATE_SCALAR_LABELS_R1'
            or packet.get('status') != 'COMPLETE'
            or packet.get('input_kind') not in ('SYNTHETIC_CPU', 'PRODUCTION_CAPTURE')
            or packet.get('design_scope_sha256') != design['scope_sha256']
            or packet.get('schedule_sha256') != digest(schedule)):
        raise ValueError('Complete declared V1 scalar packet and original design/grid required')
    provenance = packet.get('provenance', {})
    if (provenance.get('teacher') != 'candidate_own_current_state_shadow_D'
            or provenance.get('teacher_writes_parent') is not False
            or provenance.get('target') != 'FP64_MSE_OF_ACTUAL_SAME_STATE_FP32_CFG'
            or provenance.get('target_normalized') is not False):
        raise ValueError('Own-state nonwriting shadow D and unnormalized FP64 target required')
    parents = {p['id']: p for p in design['parents']}
    expected = {(member, p['id'], s['t']): s
                for member in design['FIT'] for p in design['parents'] for s in p['states']}
    rows = packet.get('rows', [])
    if len(expected) != 64 or len(rows) != len(expected):
        raise ValueError('Complete64 denominator required, including both FIT and four parents')
    found = set()
    samples = []
    for row in rows:
        key = row['member'], row['parent_id'], row['t']
        if key not in expected or key in found or type(row['t']) is not int:
            raise ValueError('Distinct preregistered FIT/parent/C-state identities required')
        source = expected[key]
        a, b, t = row['a'], row['b'], row['t']
        if (type(a) is not int or type(b) is not int or (a, b) != (source['a'], source['b'])
                or row['parent_fingerprint'] != parents[row['parent_id']]['policy']['fingerprint']
                or row['source_steps_by_CFG'] != [[a, b], [a, b]]):
            raise ValueError('Actual latest two true D sources in both CFG branches required')
        bindings = ('C_input_state_id', 'shadow_D_input_state_id',
                    'parent_before_shadow_id', 'parent_after_shadow_id')
        if (any(not isinstance(row[k], str) or not row[k] for k in bindings)
                or row[bindings[0]] != row[bindings[1]]
                or row[bindings[2]] != row[bindings[3]]):
            raise ValueError('Same input state and unchanged parent across shadow D required')
        squared, count = row['sum_squared_error_fp64'], row['element_count']
        if (type(squared) not in (int, float) or not math.isfinite(squared) or squared < 0
                or type(count) is not int or count <= 0):
            raise ValueError('Finite nonnegative FP64 squared-error sum and element count required')
        samples.append(Sample(key[0], key[1], t, a, b,
                              coordinates(schedule['sigmas'], t, a, b), float(squared/count)))
        found.add(key)
    return tuple(sorted(samples, key=lambda s: (s.parent, s.member, s.t)))


@dataclass(frozen=True)
class Estimator:
    family: str
    coefficients: tuple
    coordinate_bounds: tuple
    source_triples: frozenset
    design_rank: int

    def raw(self, point):
        return math.fsum(c*x for c, x in zip(self.coefficients, features(point, self.family)))

    def predict(self, point):
        return max(0., self.raw(point))

    def outside(self, point):
        width = FAMILIES.index(self.family)+1
        return any(x < lo or x > hi for x, (lo, hi) in zip(point[:width], self.coordinate_bounds))

    def record(self):
        return dict(family=self.family, feature_names=list(FEATURE_NAMES[:WIDTH[self.family]]),
                    coefficients=list(self.coefficients), ridge=RIDGE,
                    intercept_penalized=False, features_standardized=False,
                    objective='input_equal_mean_squared_label_error_plus_ridge_nonintercept',
                    negative_prediction='clamp_zero', design_rank=self.design_rank,
                    coordinate_bounds=[list(pair) for pair in self.coordinate_bounds])


def fit(samples, family):
    if family not in FAMILIES or not samples:
        raise ValueError('One of the three frozen families and nonempty validated samples required')
    members = sorted({s.member for s in samples})
    counts = {m: sum(s.member == m for s in samples) for m in members}
    x = np.asarray([features(s.coordinates, family) for s in samples], dtype=np.float64)
    y = np.asarray([s.target for s in samples], dtype=np.float64)
    weights = np.asarray([1./(len(members)*counts[s.member]) for s in samples])
    penalty = np.eye(WIDTH[family], dtype=np.float64)*math.sqrt(RIDGE)
    penalty[0, 0] = 0.
    # The augmented least-squares SVD avoids squaring the condition number.
    augmented_x = np.vstack((np.sqrt(weights[:, None])*x, penalty))
    augmented_y = np.concatenate((np.sqrt(weights)*y, np.zeros(WIDTH[family])))
    coefficients = np.linalg.lstsq(augmented_x, augmented_y, rcond=None)[0]
    if not np.isfinite(coefficients).all():
        raise ValueError('Nonfinite fixed ridge solution')
    bounds = tuple((min(s.coordinates[i] for s in samples), max(s.coordinates[i] for s in samples))
                   for i in range(3))
    return Estimator(family, tuple(float(c) for c in coefficients), bounds,
                     frozenset((s.t, s.a, s.b) for s in samples), int(np.linalg.matrix_rank(x)))


def diagnostics(model, samples):
    by_member = {}
    for member in sorted({s.member for s in samples}):
        rows = [s for s in samples if s.member == member]
        errors = [model.predict(s.coordinates)-s.target for s in rows]
        by_member[member] = dict(rows=len(rows), MSE=math.fsum(e*e for e in errors)/len(rows),
                                 MAE=math.fsum(abs(e) for e in errors)/len(rows))
    count = len(samples)
    return dict(rows=count, by_member=by_member,
                input_equal_MSE=math.fsum(r['MSE'] for r in by_member.values())/len(by_member),
                input_equal_MAE=math.fsum(r['MAE'] for r in by_member.values())/len(by_member),
                zero_clamp_fraction=sum(model.raw(s.coordinates) < 0 for s in samples)/count,
                marginal_outside_training_fraction=sum(model.outside(s.coordinates) for s in samples)/count,
                unseen_t_a_b_fraction=sum((s.t, s.a, s.b) not in model.source_triples for s in samples)/count)


def fit_validate_plan(samples, design, manifest, weights):
    """Same four parent-held-out folds and exact19/22 top3 DP for every family."""
    sigmas = manifest['schedule']['sigmas']
    profile = profile_from(manifest['profile'])
    reports = []
    for family in FAMILIES:
        folds = []
        for parent in design['parents']:
            train = tuple(s for s in samples if s.parent != parent['id'])
            held_out = tuple(s for s in samples if s.parent == parent['id'])
            if len(train) != 48 or len(held_out) != 16:
                raise ValueError('Four complete whole-parent folds across both FIT required')
            model = fit(train, family)
            folds.append(dict(held_out_parent=parent['id'],
                              train_parents=sorted({s.parent for s in train}),
                              train_rows=len(train), held_out_members=sorted({s.member for s in held_out}),
                              diagnostic=diagnostics(model, held_out), model=model.record()))
        model = fit(samples, family)

        @lru_cache(maxsize=None)
        def risk(t, a, b):
            return model.predict(coordinates(sigmas, t, a, b))

        candidates = {}
        for budget in (19, 22):
            result = plan(profile, budget, risk, weights, top_k=3)
            for row in result['plans']:
                past = []
                states = []
                for t, action in enumerate(row['policy']['actions'], 1):
                    if action == 'D':
                        past.append(t)
                    else:
                        a, b = past[-2:]
                        states.append(Sample('UNOBSERVED_CANDIDATE', '', t, a, b,
                                             coordinates(sigmas, t, a, b), 0.))
                # Candidate predictions are diagnostics, never measured endpoint quality.
                row['predicted_C_states'] = len(states)
                row['zero_clamp_fraction'] = sum(model.raw(s.coordinates) < 0 for s in states)/len(states)
                row['marginal_outside_training_fraction'] = sum(model.outside(s.coordinates) for s in states)/len(states)
                row['unseen_t_a_b_fraction'] = sum((s.t, s.a, s.b) not in model.source_triples for s in states)/len(states)
            candidates[str(budget)] = result
        reports.append(dict(family=family, full_model=model.record(),
                            in_sample=diagnostics(model, samples), whole_parent_folds=folds,
                            held_out_input_equal_MSE=math.fsum(f['diagnostic']['input_equal_MSE'] for f in folds)/len(folds),
                            candidates=candidates))
    return dict(schema='CARA_V1_FIXED_ESTIMATION_PROXY_CANDIDATES_R1',
                status='OFFLINE_ESTIMATES_AND_CANDIDATES_REQUIRE_FULL_VIDEO_SELECTION',
                design_scope_sha256=design['scope_sha256'], samples=len(samples), families=reports,
                held_out_unit='entire_parent_across_both_FIT', adjacent_random_split=False,
                feature_or_ridge_search=False, real_video_efficacy=False,
                whole_collection_provenance_accepted=False, GPU_dispatch_ready=False, GPU_submissions=0)


def select_complete_FIT(candidates, scores, members):
    """Select once from complete accepted-input93-frame curves; never use CHECK."""
    by_id = {r['policy']['fingerprint']: r for r in candidates}
    if not 1 <= len(by_id) == len(candidates) <= 3 or len(set(members)) != 2:
        raise ValueError('One to three distinct candidates and two frozen FIT required')
    expected = {(candidate, member) for candidate in by_id for member in members}
    seen = set()
    means = {candidate: [] for candidate in by_id}
    for row in scores:
        key = row['candidate_id'], row['member']
        curve = row['Alex_curve']
        if (key not in expected or key in seen or row['status'] != 'COMPLETE'
                or len(curve) != 93 or any(type(x) not in (int, float) or not math.isfinite(x) or x < 0 for x in curve)):
            raise ValueError('Complete distinct FIT-only93-frame denominator required; retain failures')
        means[key[0]].append(math.fsum(curve)/93)
        seen.add(key)
    if seen != expected:
        raise ValueError('All FIT candidates must be completely scored before selection')
    ranking = sorted((math.fsum(means[key])/len(members), row['proxy_cost'],
                      tuple(row['dense_steps']), key) for key, row in by_id.items())
    return dict(candidate_id=ranking[0][3], input_equal_Alex=ranking[0][0],
                ranking=[dict(input_equal_Alex=alex, proxy_cost=cost, dense_steps=list(mask),
                              candidate_id=key) for alex, cost, mask, key in ranking],
                selection='input_equal_Alex_then_proxy_then_lexicographic_D_mask',
                scoring_originals_accepted_separately_required=True, CHECK_used=False)
