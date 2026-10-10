"""Source-aware joint C/P/D rule; no model execution or implicit calibration.

P parameters and costs must be supplied in explicitly bound proxy units.
Actual old P0 velocity MSE ratios alone do not supply the creation floor.
The source-floor plus drift rule is empirical, not an endpoint error bound.
"""
from dataclasses import dataclass
import copy
import math

from .cfg_ra_joint_control import Calibration, finite_nonnegative, guided_proxy


@dataclass(frozen=True)
class PartialPrior:
    fingerprint: str
    creation_floor_proxy: float
    drift_ratio: float
    proxy_definition: str = 'WC_PAID_DELTA_Y'
    maximum_consecutive_P: int = 2

    def __post_init__(self):
        if (not self.fingerprint or self.proxy_definition != 'WC_PAID_DELTA_Y'
                or not finite_nonnegative(self.creation_floor_proxy)
                or self.creation_floor_proxy == 0
                or not finite_nonnegative(self.drift_ratio)
                or self.drift_ratio == 0
                or type(self.maximum_consecutive_P) is not int
                or self.maximum_consecutive_P < 1):
            raise ValueError('P needs positive, source-bound same-unit quality parameters')


@dataclass(frozen=True)
class Costs:
    fingerprint: str
    C: float
    D: float
    P: object = None

    def __post_init__(self):
        if (not self.fingerprint or any(not finite_nonnegative(x) or x == 0
                for x in (self.C, self.D)) or self.P is not None
                and (not finite_nonnegative(self.P) or self.P == 0)):
            raise ValueError('Bound positive complete-pair costs required')


@dataclass(frozen=True)
class Choice:
    step: int
    action: str
    generation: int
    state_before: tuple
    owner: int
    packets: tuple
    both_sources_ready: bool
    partial_ready: bool
    local_proxy: object
    gain: object
    added_risk: object
    predicted_creation_floor: float
    candidates: tuple
    reason: str


class SourceAwareCPDController:
    def __init__(self, calibration, threshold, costs, partial_prior=None):
        if (not isinstance(calibration, Calibration) or not finite_nonnegative(threshold)
                or not isinstance(costs, Costs) or partial_prior is not None
                and not isinstance(partial_prior, PartialPrior)):
            raise ValueError('Bound current RA calibration, costs and optional P prior required')
        self.calibration, self.threshold = calibration, float(threshold)
        self.costs, self.partial_prior = costs, partial_prior
        self.anchor = None
        self.working_kind = self.working_step = None
        self.creation_floor = self.accumulated = 0.
        self.consecutive_P = self.last_completed_step = self.generation = 0
        self.history = []
        self.poisoned = False

    def _state(self):
        return (self.anchor, self.working_kind, self.working_step,
                self.creation_floor, self.accumulated, self.consecutive_P,
                self.last_completed_step, self.generation, self.poisoned)

    def _next(self, step):
        if (self.poisoned or type(step) is not int
                or step != self.last_completed_step+1 or not 1 <= step <= 36):
            raise ValueError('Healthy next logical full36 step required')

    def _choice(self, step, packet_values, ready, partial_ready, protected=False):
        self._next(step)
        if type(ready) is not bool or type(partial_ready) is not bool:
            raise ValueError('Explicit actual source and projection readiness required')
        action, reason = 'D', 'actual_protected_dense' if protected else 'shared_dense_anchor_not_ready'
        local = gain = added = None
        floor = 0.
        candidates = ()
        if not protected and ready and self.anchor is not None:
            cell = (self.anchor, step)
            if cell not in self.calibration.rho_at or step not in self.calibration.gains:
                reason = 'missing_current_calibration'
            elif (len(packet_values) != 2 or [p[:2] for p in packet_values]
                  != [(0, 2*(step-1) % 70), (1, 2*(step-1) % 70+1)]):
                reason = 'invalid_paid_branch_pair'
            else:
                try:
                    local = guided_proxy(packet_values[0][2], packet_values[1][2],
                                         self.calibration.rho_at[cell])
                    gain = self.calibration.gains[step]
                    c_added = gain*(self.creation_floor+local)
                    if not math.isfinite(self.accumulated+c_added):
                        raise ValueError('Nonfinite interval score')
                    options = [('D', self.costs.D, 0., 0.)]
                    if self.accumulated+c_added <= self.threshold:
                        options.append(('C', self.costs.C, c_added, self.creation_floor))
                    p = self.partial_prior
                    if (partial_ready and p is not None and self.costs.P is not None
                            and self.consecutive_P < p.maximum_consecutive_P):
                        p_added = gain*(p.creation_floor_proxy+p.drift_ratio*local)
                        if finite_nonnegative(p_added) and self.accumulated+p_added <= self.threshold:
                            options.append(('P', self.costs.P, p_added, p.creation_floor_proxy))
                    # Equal cost preserves C before P before D; measured cost may
                    # legitimately make D cheaper than either approximation.
                    chosen = min(options, key=lambda x: (x[1], {'C':0, 'P':1, 'D':2}[x[0]]))
                    action, _, added, floor = chosen
                    candidates = tuple(options)
                    reason = 'cheapest_feasible_bound_action'
                except (ValueError, OverflowError, TypeError):
                    local = gain = added = None
                    reason = 'nonfinite_or_invalid_proxy'
        return Choice(step, action, self.generation, self._state(), id(self),
                      packet_values, ready, partial_ready, local, gain, added,
                      floor, candidates, reason)

    def decide(self, step, packets, *, both_sources_ready, partial_ready):
        # Snapshot only public scalar probe fields. No observer/teacher calls.
        values = tuple((getattr(p,'slot',None), getattr(p,'counter',None),
                        getattr(p,'delta_y',None)) for p in packets)
        return self._choice(step, values, both_sources_ready, partial_ready)

    def commit(self, choice, *, actual_action, pair_completed):
        if not isinstance(choice, Choice) or choice.owner != id(self):
            raise ValueError('Decision belongs to a different controller')
        self._next(choice.step)
        if choice.state_before != self._state() or choice.generation != self.generation:
            raise ValueError('Stale source/history decision')
        expected = self._choice(choice.step, choice.packets, choice.both_sources_ready,
            choice.partial_ready, protected=choice.reason == 'actual_protected_dense')
        if choice != expected:
            raise ValueError('Modified action, score or source decision')
        if type(pair_completed) is not bool or not pair_completed or actual_action != choice.action:
            self.poisoned = True
            raise ValueError('Incomplete or mismatched actual semantic pair; discard owner')
        if actual_action == 'D':
            self.anchor = self.working_step = choice.step
            self.working_kind = 'D'
            self.creation_floor = self.accumulated = 0.
            self.consecutive_P = 0
        else:
            self.accumulated += choice.added_risk
            if actual_action == 'P':
                self.working_kind, self.working_step = 'P', choice.step
                self.creation_floor = choice.predicted_creation_floor
                self.consecutive_P += 1
            else:
                self.consecutive_P = 0
        self.last_completed_step = choice.step
        self.generation += 1
        self.history.append(choice)

    def commit_protected_dense(self, step, *, actual_action, pair_completed):
        choice = self._choice(step, (), False, False, protected=True)
        self.commit(choice, actual_action=actual_action, pair_completed=pair_completed)

    def state_dict(self):
        return copy.deepcopy({'binding': (self.calibration.fingerprint, self.threshold,
            self.costs, self.partial_prior), 'state': self._state(), 'history': self.history})

    def restore(self, snapshot):
        # Only exact previously exported histories are valid restore inputs;
        # deployment tensor state must separately restore at the same boundary.
        expected = (self.calibration.fingerprint, self.threshold, self.costs, self.partial_prior)
        if (set(snapshot) != {'binding','state','history'} or snapshot['binding'] != expected
                or type(snapshot['state']) is not tuple or len(snapshot['state']) != 9
                or type(snapshot['history']) is not list):
            raise ValueError('Restore binding or state layout differs')
        old = self.state_dict()
        # Independently replay decisions to validate source/interval transitions.
        replay = SourceAwareCPDController(self.calibration,self.threshold,self.costs,self.partial_prior)
        for original in snapshot['history']:
            if not isinstance(original,Choice) or original.owner != id(self):
                raise ValueError('Foreign history cannot restore this owner')
            d = replay._choice(original.step,original.packets,original.both_sources_ready,
                original.partial_ready,protected=original.reason=='actual_protected_dense')
            from dataclasses import replace
            if replace(d,owner=id(self)) != original:
                raise ValueError('Modified restored decision or history')
            replay.commit(d,actual_action=d.action,pair_completed=True)
        # Failed owners are not healthy checkpoints.
        if replay._state() != snapshot['state'] or snapshot['state'][-1]:
            raise ValueError('Restored state differs from complete actual-pair history')
        (self.anchor,self.working_kind,self.working_step,self.creation_floor,
         self.accumulated,self.consecutive_P,self.last_completed_step,
         self.generation,self.poisoned) = snapshot['state']
        self.history = copy.deepcopy(snapshot['history'])
        return old
