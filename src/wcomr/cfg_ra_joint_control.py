"""Cosmos paid-probe RA-style C/D policy, independent of model execution.

The CFG geometry and accumulated propagation-weighted proxy follow RA-CFGCache.
This module does not estimate correlation, fabricate propagation calibration,
run a teacher, change WC tensors, or install a production policy. Actual pair
completion must commit the decision; score-only calls do not advance history.
"""
from dataclasses import dataclass
import math
from types import MappingProxyType


def finite_nonnegative(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def guided_proxy(ec, eu, rho):
    """Actual Cosmos guidance7 means 8*c - 7*u, rather than 7*c - 6*u."""
    if (not finite_nonnegative(ec) or not finite_nonnegative(eu)
            or type(rho) not in (int, float) or not math.isfinite(rho) or not -1 <= rho <= 1):
        raise ValueError('Invalid branch proxy or correlation')
    # Equivalent PSD form avoids subtracting two large positive energies.
    energy = (8*ec-7*eu)**2 + 112*ec*eu*(1-rho)
    if not math.isfinite(energy):
        raise ValueError('Nonfinite guided proxy energy')
    return math.sqrt(energy)


@dataclass(frozen=True)
class Calibration:
    fingerprint: str
    rho_at: object
    gains: object
    proxy_definition: str = 'WC_PAID_DELTA_Y'
    model_family: str = 'Cosmos-Predict2.5-2B'
    solver: str = 'UniPC-Karras-36'
    guided_weights: tuple = (8, -7)
    branch_order: tuple = ('conditional', 'negative_prompt')

    def __post_init__(self):
        if (not self.fingerprint or self.proxy_definition != 'WC_PAID_DELTA_Y'
                or self.model_family != 'Cosmos-Predict2.5-2B' or self.solver != 'UniPC-Karras-36'
                or self.guided_weights != (8, -7)
                or self.branch_order != ('conditional', 'negative_prompt')):
            raise ValueError('Calibration protocol differs from current Cosmos contract')
        rho = dict(self.rho_at); gains = dict(self.gains)
        for (anchor, step), value in rho.items():
            if (type(anchor) is not int or type(step) is not int or not 1 <= anchor < step <= 36
                    or type(value) not in (int, float) or not math.isfinite(value) or not -1 <= value <= 1):
                raise ValueError('Invalid anchor/step correlation calibration')
        for step, value in gains.items():
            if type(step) is not int or not 1 <= step <= 36 or not finite_nonnegative(value):
                raise ValueError('Invalid propagation calibration')
        object.__setattr__(self, 'rho_at', MappingProxyType(rho))
        object.__setattr__(self, 'gains', MappingProxyType(gains))


@dataclass(frozen=True)
class Decision:
    step: int
    action: str
    anchor_before: object
    accumulated_before: float
    local_proxy: object
    propagation_gain: object
    added_risk: object
    reason: str
    generation: int


class JointCDController:
    """Logical sampler-step indexed policy; WC modulo counters are not time."""
    def __init__(self, calibration, threshold):
        if not isinstance(calibration, Calibration) or not finite_nonnegative(threshold):
            raise ValueError('Current calibration and finite threshold required')
        self.calibration = calibration
        self.threshold = float(threshold)
        self.anchor = None
        self.accumulated = 0.
        self.last_completed_step = 0
        self.generation = 0
        self.history = []
        self.poisoned = False

    def _next_step(self, step):
        if self.poisoned:
            raise ValueError('Failed pair controller must be discarded')
        if type(step) is not int or step != self.last_completed_step+1 or not 1 <= step <= 36:
            raise ValueError('Logical full36 sampler step skipped, repeated or wrapped')

    def decide(self, step, packets, *, both_sources_ready):
        self._next_step(step)
        if type(both_sources_ready) is not bool:
            raise ValueError('Explicit branch source readiness required')
        reason = 'calibrated_proxy'
        local = gain = added = None
        if not both_sources_ready or self.anchor is None:
            action, reason = 'DD', 'shared_dense_anchor_not_ready'
        else:
            cell = (self.anchor, step)
            if cell not in self.calibration.rho_at or step not in self.calibration.gains:
                action, reason = 'DD', 'missing_current_calibration'
            elif (len(packets) != 2 or [getattr(p, 'slot', None) for p in packets] != [0, 1]
                    or [getattr(p, 'counter', None) for p in packets] != [(2*(step-1)) % 70, (2*(step-1)) % 70+1]):
                action, reason = 'DD', 'invalid_paid_branch_pair'
            else:
                try:
                    local = guided_proxy(packets[0].delta_y, packets[1].delta_y, self.calibration.rho_at[cell])
                    gain = self.calibration.gains[step]
                    added = gain*local
                    total = self.accumulated+added
                    if not math.isfinite(total):
                        raise ValueError('Nonfinite accumulated proxy')
                    action = 'CC' if total <= self.threshold else 'DD'
                except (ValueError, OverflowError, AttributeError, TypeError):
                    local = gain = added = None
                    action, reason = 'DD', 'nonfinite_or_invalid_proxy'
        return Decision(step, action, self.anchor, self.accumulated, local, gain, added, reason, self.generation)

    def commit(self, decision, *, actual_action, pair_completed):
        if not isinstance(decision, Decision):
            raise ValueError('Source-bound policy decision required')
        self._next_step(decision.step)
        if (decision.generation != self.generation or decision.anchor_before != self.anchor
                or decision.accumulated_before != self.accumulated):
            raise ValueError('Stale score cannot commit changed deployment history')
        if type(pair_completed) is not bool or not pair_completed or actual_action != decision.action:
            self.poisoned = True
            raise ValueError('Incomplete or mismatched executed pair; discard controller')
        if actual_action == 'DD':
            self.anchor = decision.step
            self.accumulated = 0.
        elif actual_action == 'CC' and finite_nonnegative(decision.added_risk):
            self.accumulated += decision.added_risk
        else:
            self.poisoned = True
            raise ValueError('First RA controller supports actual joint C/D only')
        self.last_completed_step = decision.step
        self.generation += 1
        self.history.append(decision)

    def commit_protected_dense(self, step, *, actual_action, pair_completed):
        """Record actual protected dense work performed outside the selector."""
        self._next_step(step)
        d = Decision(step, 'DD', self.anchor, self.accumulated, None, None, None,
                     'actual_protected_dense', self.generation)
        self.commit(d, actual_action=actual_action, pair_completed=pair_completed)
