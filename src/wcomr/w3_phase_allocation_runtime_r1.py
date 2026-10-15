"""Isolated full-step H1/phase/T1 execution adapter, pending production CPU.

Only paid pre-action observations are used. Frozen H1 and readout code remain
unchanged; partial P0 legality is removed only in the explicit CAD bridge.
"""
import copy, functools, hashlib, json, math
from dataclasses import replace
import numpy as np
from .source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller
from .source_phase_absolute_h1_owner_r1 import SourcePhaseH1Owner
from .source_aware_phase_sampling import bind_globals
from .w3_causal_trend_r1 import Observation, FeatureRow, coherent_scores

VERSION = 'W3_FROZEN_PHASE_AND_CURRENT_OBSERVATION_RUNTIME_R1'
METHODS = ('H1_ORIGINAL', 'H1_CAD', 'STEP23_A_ONLY', 'T1_CAD')
T1_FP = '47026e73e41b791c6be7d0bdab44de8fda189d1f11d4f0629c210fc562a8e46f'
T1_NAMES = ('step_fraction', 'log1p_sigma', 'sigma_available', 'source_is_P', 'source_age',
            'root_floor', 'delta_c', 'delta_u', 'paid_pair_available', 'local_proxy',
            'gain', 'calibration_supported', 'source_reset')


def validate_T1(p):
    body = {k: v for k, v in p.items() if k != 'fingerprint'}
    actual = hashlib.sha256(json.dumps(body, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if (actual != p['fingerprint'] or actual != T1_FP or p['model'] != 'T1'
            or tuple(p['feature_names']) != T1_NAMES or p['training_source_domain'] != ['D']
            or p['age_domain'] != [1, 6] or p['window'] != 4 or p['ridge'] != 1
            or not p['gain_squared_applied_once']):
        raise ValueError('Exact frozen primary6 T1 parameters required')
    mean, std, weights = (np.asarray(p[k], float) for k in ('mean', 'std', 'weights'))
    if (mean.shape != (13,) or std.shape != (13,) or weights.shape != (14, 2)
            or not all(np.isfinite(a).all() for a in (mean, std, weights)) or not (std > 0).all()):
        raise ValueError('Finite frozen 13-feature scaling and two-target weights required')
    return mean, std, weights


def online_feature(o, previous_source_id):
    """Exact T1 values without teacher access or mutable history additions."""
    o.validate()
    values = (o.step/36, math.log1p(o.sigma) if o.sigma is not None else 0., float(o.sigma is not None),
        float(o.source_kind == 'P'), float(o.source_age or 0), o.root_floor,
        o.delta_c or 0., o.delta_u or 0., float(o.delta_c is not None), o.local_proxy or 0.,
        o.gain or 0., float(o.calibration_supported), float(o.step == 1 or previous_source_id != o.source_id))
    if not all(math.isfinite(v) for v in values): raise ValueError('Finite causal T1 values required')
    return FeatureRow(o, 'T1', T1_NAMES, values, tuple(range(max(1, o.step-3), o.step+1)), o.sigma is not None)


class PhaseAllocationController(SourcePhaseH1Controller):
    def __init__(self, *a, allocation_method, frozen_T1, request_identity, **kw):
        if allocation_method not in METHODS or (not isinstance(request_identity, tuple)
                or len(request_identity) != 2 or not isinstance(request_identity[0], str)
                or not request_identity[0] or type(request_identity[1]) is not int):
            raise ValueError('Registered method and request prompt/seed required')
        self.allocation_method = allocation_method
        self.frozen_T1 = copy.deepcopy(frozen_T1)
        self.T1_mean, self.T1_std, self.T1_weights = validate_T1(frozen_T1)
        self.request_identity = request_identity
        super().__init__(*a, **kw)
        if allocation_method == 'T1_CAD' and self.table_parameters['lambda_seconds_per_weighted_absolute_MSE'] != frozen_T1['lambda_seconds_per_weighted_absolute_MSE']:
            raise ValueError('Frozen T1 lambda and actual H1 quotation must agree')

    def predicted_actions(self, choice):
        table = super().predicted_actions(choice)
        if table is not None and self.allocation_method in ('H1_CAD', 'T1_CAD'):
            table = {a: v for a, v in table.items() if a != 'P'}
        return table

    def _feature(self, choice):
        state = choice.state_before; source, created = state[1:3]
        source_id = source+':'+str(created) if source else None
        previous = self.history[choice.step-2].state_before if choice.step > 1 else None
        previous_id = previous[1]+':'+str(previous[2]) if previous and previous[1] else None
        paid = len(choice.packets) == 2
        if paid and tuple(v[:2] for v in choice.packets) != ((0, 2*(choice.step-1)%70), (1, 2*(choice.step-1)%70+1)):
            raise ValueError('Actual paid probe pair counter changed')
        sigma = float(self.sigma_at(choice.step))
        observation = Observation(self.request_identity[0], self.request_identity[1], choice.step,
            'ordinary_pre_action:'+str((self.request_identity, choice.step, state[7])), sigma,
            source, source_id, choice.step-created if source else None, state[3],
            choice.packets[0][2] if paid else None, choice.packets[1][2] if paid else None,
            choice.local_proxy, choice.gain, False, True)
        return online_feature(observation, previous_id)

    def _trace(self, base):
        supported = (base.both_sources_ready and base.local_proxy is not None and base.gain is not None
            and base.reason.startswith('MATH_EVENT_TABLE_ABSOLUTE_H1:')
            and base.state_before[1] == 'D' and base.state_before[2] is not None
            and 1 <= base.step-base.state_before[2] <= 6)
        trace = dict(base_H1_action=base.reason.rsplit(':', 1)[-1] if base.reason.startswith('MATH_EVENT_') else base.action,
                     supported_D_source=supported, feature=None, prediction=None, decision=None,
                     fallback_reason=None)
        if self.allocation_method != 'T1_CAD' or not supported: return trace
        try:
            feature = self._feature(base)
            raw = np.einsum('i,ij->j', np.r_[1., (np.asarray(feature.values)-self.T1_mean)/self.T1_std], self.T1_weights, optimize=False)
            if not np.isfinite(raw).all(): raise ValueError('Nonfinite frozen prediction')
            costs = self.table_parameters['cost_seconds']
            decision = coherent_scores(raw, feature.observation,
                costs={'C': costs['C'], 'A': self.table_parameters['source_A_cost_seconds']['D'], 'D': costs['D']},
                lam=self.frozen_T1['lambda_seconds_per_weighted_absolute_MSE'])
            trace.update(feature=dict(names=feature.names, values=feature.values, prefix_steps=feature.prefix_steps,
                sigma=feature.observation.sigma), prediction=raw.tolist(), decision=decision)
        except (ValueError, OverflowError) as e:
            trace['fallback_reason'] = type(e).__name__+':'+str(e)
        return trace

    def _choice(self, step, packet_values, ready, partial_ready, protected=False):
        base = super()._choice(step, packet_values, ready, partial_ready, protected)
        # An UNKNOWN pi0 fallback must not silently reintroduce P into the CAD bridge.
        if self.allocation_method in ('H1_CAD', 'T1_CAD') and base.action == 'P':
            base = replace(base, action='D', added_risk=0., predicted_creation_floor=0.,
                candidates=tuple(v for v in base.candidates if v[0] != 'P'),
                reason='MATH_EVENT_TABLE_PI0_UNKNOWN_FALLBACK:D')
        if protected: return base
        trace = self._trace(base)
        name = None
        if (self.allocation_method == 'STEP23_A_ONLY' and step == 23 and base.action == 'D'
                and trace['supported_D_source']): name = 'A'
        elif self.allocation_method == 'T1_CAD' and trace['decision'] is not None:
            name = trace['decision']['action']
        if name is None: return base
        floor = 0. if name == 'D' else self.creation_floor
        root = 0. if name == 'D' else base.gain*(floor+base.local_proxy)
        candidates = base.candidates
        if self.allocation_method == 'T1_CAD':
            dec = trace['decision']; costs = self.table_parameters['cost_seconds']
            candidates = tuple((a, self.table_parameters['source_A_cost_seconds']['D'] if a == 'A' else costs[a],
                dec['risk'][a], 0. if a == 'D' else self.creation_floor) for a in ('C', 'A', 'D'))
        return replace(base, action='C' if name == 'A' else name, added_risk=root,
            predicted_creation_floor=floor, candidates=candidates,
            reason='MATH_EVENT_W3_'+self.allocation_method+':'+name)

    def query_basis(self, choice):
        result = super().query_basis(choice)
        # Reconstruct only the parent H1 rule at the saved pre-action boundary.
        if choice.reason.startswith('MATH_EVENT_W3_'):
            table = self.predicted_actions(choice)
            name = min(table, key=lambda a: (table[a]['score'], {'C': 0, 'A': 1, 'P': 2, 'D': 3}[a]))
            base = replace(choice, action='C' if name == 'A' else name, reason='MATH_EVENT_TABLE_ABSOLUTE_H1:'+name)
        else: base = choice
        trace = self._trace(base)
        result.update(allocation_runtime_version=VERSION, allocation_method=self.allocation_method,
            actual_semantic_action=choice.reason.rsplit(':', 1)[-1] if choice.reason.startswith('MATH_EVENT_') else choice.action,
            H1_table_candidate_risk_and_price=result['candidate_risk_and_price'],
            allocation_trace=trace, teacher_or_future_in_predictor=False, risk_gain_squared_applied_again=False,
            P0_legal=self.allocation_method not in ('H1_CAD', 'T1_CAD'))
        if trace['decision'] is not None:
            dec = trace['decision']; costs = self.table_parameters['cost_seconds']
            result['candidate_risk_and_price'] = {a: {'price': self.table_parameters['source_A_cost_seconds']['D'] if a == 'A' else costs[a],
                'gain_squared_risk': dec['risk'][a], 'score': dec['scores'][a]} for a in ('C', 'A', 'D')}
        return result

    def state_dict(self):
        result = super().state_dict()
        result['binding'] += (VERSION, self.allocation_method, T1_FP, self.request_identity)
        return result

    def restore(self, snapshot):
        if set(snapshot) != {'binding', 'state', 'history'} or snapshot['binding'] != self.state_dict()['binding']:
            raise ValueError('Exact allocation policy and request snapshot required')
        replay = PhaseAllocationController(self.calibration, self.threshold, self.costs, self.partial_prior,
            strategy=self.strategy, table_parameters=self.table_parameters, math_parameters=self.math_parameters,
            horizon=1, sigma_at=self.sigma_at, allocation_method=self.allocation_method,
            frozen_T1=self.frozen_T1, request_identity=self.request_identity)
        for original in snapshot['history']:
            if original.owner != id(self): raise ValueError('Foreign allocation history')
            d = replay._choice(original.step, original.packets, original.both_sources_ready, original.partial_ready,
                protected=original.reason == 'actual_protected_dense')
            if replace(d, owner=id(self)) != original: raise ValueError('Modified allocation history')
            replay.commit(d, actual_action=d.action, pair_completed=True)
        if replay._state() != snapshot['state'] or snapshot['state'][-1]: raise ValueError('Incomplete or poisoned allocation state')
        old = self.state_dict()
        (self.anchor, self.working_kind, self.working_step, self.creation_floor, self.accumulated,
         self.consecutive_P, self.last_completed_step, self.generation, self.poisoned) = snapshot['state']
        self.history = copy.deepcopy(snapshot['history'])
        return old


class PhaseAllocationOwner(SourcePhaseH1Owner):
    def __init__(self, *a, allocation_method, frozen_T1, request_identity, **kw):
        ctor = bind_globals(SourcePhaseH1Owner.__init__, {'SourcePhaseH1Controller': functools.partial(
            PhaseAllocationController, allocation_method=allocation_method, frozen_T1=frozen_T1, request_identity=request_identity)})
        ctor(self, *a, **kw)

    def installation(self):
        return super().installation()+(VERSION, self.controller.allocation_method, T1_FP, self.controller.request_identity)


def _execute_request(inference, sample, method, *, table_parameters, previous_parameters, frozen_T1, **kw):
    from . import clean_speed20_r1 as clean
    if method not in METHODS: raise ValueError('Complete original/CAD/step23/frozenT1 bridge required')
    holder = {}
    def factory(*a, **kwargs):
        owner = PhaseAllocationOwner(*a, allocation_method=method, frozen_T1=frozen_T1,
            request_identity=(sample.name, sample.seed), table_parameters=table_parameters['SOURCE_PHASE'],
            math_parameters=previous_parameters, horizon=1, source_mode='FUSION', **kwargs)
        holder['owner'] = owner
        return owner
    with clean.patched(clean, 'CurrentBirthSamplingOwner', factory):
        result = clean.execute(inference, sample, 'KEEP_A_P', **kw)
    owner = holder['owner']
    result.update(bridge_method=result['method'], method=method, source_history=copy.deepcopy(owner.deployment.history),
        semantic_plan=[h['A_readout']['readout_action'] for h in owner.deployment.history],
        frozen_T1_fingerprint=T1_FP, online_teacher_calls=0, allocation_runtime_version=VERSION)
    return result


def execute(*a, **kw):
    """Reuse the accepted request-boundary cleanup; never clear live sources."""
    import weakref
    from . import clean_speed20_r1 as clean
    from .simple26d_memory_r2 import collect_boundary
    before = collect_boundary(); refs = []; install = clean.install
    def observed_install(*args, **kwargs):
        result = install(*args, **kwargs)
        if result[1] is not None: refs.append(weakref.ref(result[1]))
        return result
    try:
        with clean.patched(clean, 'install', observed_install): result = _execute_request(*a, **kw)
    finally: after = collect_boundary()
    alive = sum(r() is not None for r in refs)
    if alive: raise ValueError('Completed allocation owner remains reachable')
    result['request_memory_lifecycle'] = dict(version='BOUNDARY_GC_ONLY_R2', before=before, after=after,
        observed_owners=len(refs), owners_alive_after=alive, within_request_algorithm_or_guardrails_changed=False)
    return result
