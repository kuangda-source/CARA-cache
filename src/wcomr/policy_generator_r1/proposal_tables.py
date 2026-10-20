"""Explicit guided-output quadratic statistics and measured-cost interfaces.

The quadratic identity requires a runtime-validated linear blend in the actual
output coordinate. This module refuses hidden-space or unverified surrogates.
"""
from dataclasses import dataclass
import math

from .budgeted_planner import ScoredEdge, number
from .interval_grammar import enumerate_edges


@dataclass(frozen=True)
class QuadraticStats:
    e2: float
    ed: float
    d2: float
    fusion_contract: str

    def __post_init__(self):
        number(self.e2, "mean e^2")
        number(self.d2, "mean d^2")
        if type(self.ed) not in (int, float) or not math.isfinite(self.ed):
            raise ValueError("mean e*d must be finite")
        if self.fusion_contract != "VALIDATED_GUIDED_OUTPUT_LINEAR_BLEND":
            raise ValueError("Do not infer velocity interpolation from nonlinear feature/head fusion")
        tolerance = 1e-12 * max(1.0, self.e2 * self.d2, self.ed * self.ed)
        if self.ed * self.ed > self.e2 * self.d2 + tolerance:
            raise ValueError("Second moments violate the Cauchy-Schwarz constraint")

    def at(self, alpha):
        if type(alpha) not in (int, float) or not math.isfinite(alpha) or not 0 <= alpha <= 1:
            raise ValueError("Finite alpha in [0,1] required")
        value = math.fsum((self.e2, 2 * alpha * self.ed, alpha * alpha * self.d2))
        tolerance = 1e-12 * max(1.0, self.e2, abs(2 * alpha * self.ed), alpha * alpha * self.d2)
        if value < -tolerance:
            raise ValueError("Negative physical squared-error estimate")
        return max(0.0, value)


@dataclass(frozen=True)
class Costs:
    dense_seconds: tuple
    C_seconds: tuple
    A_seconds_by_alpha: dict
    shared_seconds: float
    profile_identity: str
    measurement_protocol: str
    evidence_kind: str

    def validate(self, profile):
        if self.profile_identity != profile.identity or not self.measurement_protocol:
            raise ValueError("Costs must bind the current execution profile and timing boundary")
        if self.evidence_kind not in ("SYNTHETIC_UNIT_FIXTURE", "OBSERVED_COMPONENT_PROPOSAL_COSTS"):
            raise ValueError("A forecast or D count cannot masquerade as observed action costs")
        if set(self.A_seconds_by_alpha) != set(profile.alpha_candidates):
            raise ValueError("Price each supported alpha's actual readout path")
        for values in (self.dense_seconds, self.C_seconds, *self.A_seconds_by_alpha.values()):
            if len(values) != profile.horizon:
                raise ValueError("Every action cost table must cover the full horizon")
            for value in values:
                number(value, "action seconds", True)
        number(self.shared_seconds, "non-edge shared seconds")
        return self

    def edge_seconds(self, edge):
        terms = [self.dense_seconds[edge.start - 1]]
        for t in range(edge.start + 1, edge.end):
            table = self.A_seconds_by_alpha[edge.alpha] if edge.action_at(t) == "A" else self.C_seconds
            terms.append(table[t - 1])
        return math.fsum(terms)


def make_proxy_graph(profile, *, statistics, fit_members, costs, weights,
                     label_basis, statistic_profile_identity):
    """statistics[(member,s,t)] are complete per-member second moments.

    The initial frozen weighting rule is uniform; a future propagation
    ablation must use an explicitly bound g^2 table, with the step factor paid
    once. This function never fills missing source/time cells with zero.
    """
    costs.validate(profile)
    if label_basis not in ("SYNTHETIC_UNIT_FIXTURE", "TEACHER_CONDITIONED_PROPOSAL"):
        raise ValueError("Explicitly label the off-policy proposal-table origin")
    if (label_basis == "SYNTHETIC_UNIT_FIXTURE") != (costs.evidence_kind == "SYNTHETIC_UNIT_FIXTURE"):
        raise ValueError("Keep synthetic demonstration tables separate from real proposal assets")
    if statistic_profile_identity != profile.identity:
        raise ValueError("Statistics from another model/solver profile cannot be substituted")
    if not fit_members or len(set(fit_members)) != len(fit_members):
        raise ValueError("Freeze distinct CAL_FIT members")
    if len(weights) != profile.horizon:
        raise ValueError("A fixed full-horizon weight rule is required")
    for w in weights:
        number(w, "weight")
    members = set(fit_members)
    if any(key[0] not in members or not 1 <= key[1] < key[2] <= profile.horizon
           for key in statistics):
        raise ValueError("Foreign CAL members or noncausal source/time labels")
    graph, missing = [], set()
    for edge in enumerate_edges(profile):
        required = [(member, edge.start, t) for member in fit_members
                    for t in range(edge.start + 1, edge.end)]
        absent = [key for key in required if key not in statistics]
        if absent:
            missing.update(absent)
            continue
        terms = []
        for member in fit_members:
            terms.append(math.fsum(weights[t - 1] * statistics[(member, edge.start, t)].at(
                edge.alpha if edge.action_at(t) == "A" else 0.0)
                for t in range(edge.start + 1, edge.end)))
        graph.append(ScoredEdge(edge, costs.edge_seconds(edge), math.fsum(terms) / len(fit_members)))
    return dict(graph=tuple(graph), missing_cells=tuple(sorted(missing)), label_basis=label_basis,
        status="PROPOSAL_GRAPH_READY" if not missing else "INCOMPLETE_TABLE_NO_ZERO_FILL",
        free_running_error_truth=False, production_CPU_accepted=False)
