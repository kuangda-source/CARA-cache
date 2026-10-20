"""Model-profile-driven grammar: D at s, readouts in (s,r), terminal N+1.

No particular model's update numbers, protected region, or source lifetime are
defaults. Structural validity is separate from production runtime acceptance.
"""
from dataclasses import dataclass
import hashlib
import json
import math

from . import VERSION


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _positive_int(value, name, allow_zero=False):
    if type(value) is not int or value < (0 if allow_zero else 1):
        raise ValueError(name + " must be an explicit integer")


@dataclass(frozen=True)
class Profile:
    horizon: int
    protected_dense: tuple
    max_source_age: int
    min_C_anchors: int
    min_A_anchors: int
    identity: str
    alpha_candidates: tuple = (0.5, 1.0)

    def __post_init__(self):
        _positive_int(self.horizon, "horizon")
        _positive_int(self.max_source_age, "max_source_age", True)
        _positive_int(self.min_C_anchors, "min_C_anchors")
        _positive_int(self.min_A_anchors, "min_A_anchors")
        if (not isinstance(self.protected_dense, tuple)
                or len(set(self.protected_dense)) != len(self.protected_dense)
                or any(type(x) is not int or not 1 <= x <= self.horizon
                       for x in self.protected_dense)
                or 1 not in self.protected_dense):
            raise ValueError("Explicit protected D set must contain the initial update")
        if not isinstance(self.identity, str) or not self.identity:
            raise ValueError("Model/sampler/hardware identity is required")
        if (not isinstance(self.alpha_candidates, tuple) or not self.alpha_candidates
                or len(set(self.alpha_candidates)) != len(self.alpha_candidates)
                or any(type(a) not in (int, float) or not math.isfinite(a)
                       or not 0 < a <= 1 for a in self.alpha_candidates)):
            raise ValueError("Freeze distinct finite shared alpha candidates in (0,1]")

    @property
    def anchor_cap(self):
        return max(self.min_C_anchors, self.min_A_anchors)

    @property
    def fingerprint(self):
        return digest(dict(version=VERSION, horizon=self.horizon,
            protected_dense=sorted(self.protected_dense), max_source_age=self.max_source_age,
            min_C_anchors=self.min_C_anchors, min_A_anchors=self.min_A_anchors,
            alpha_candidates=sorted(self.alpha_candidates), identity=self.identity))


@dataclass(frozen=True)
class Edge:
    start: int
    end: int
    window: tuple = ()
    alpha: float = 0.0

    @property
    def key(self):
        return (self.start, self.end, self.window, self.alpha)

    @property
    def identity(self):
        return digest(self.key)

    def action_at(self, step):
        if not self.start <= step < self.end:
            raise ValueError("Update lies outside this interval")
        if step == self.start:
            return "D"
        return "A" if self.window and self.window[0] <= step <= self.window[1] else "C"


def validate_edge(profile, edge):
    if not isinstance(edge.window, tuple) or type(edge.alpha) not in (int, float):
        raise ValueError("Canonical interval window and numeric alpha required")
    if (type(edge.start) is not int or type(edge.end) is not int
            or not 1 <= edge.start < edge.end <= profile.horizon + 1):
        raise ValueError("Intervals require 1 <= s < r <= N+1")
    if any(edge.start < t < edge.end for t in profile.protected_dense):
        raise ValueError("An interval cannot skip a protected D")
    if edge.end - edge.start - 1 > profile.max_source_age:
        raise ValueError("Reuse exceeds this adapter's supported true-anchor age")
    if edge.window:
        if (not isinstance(edge.window, tuple) or len(edge.window) != 2
                or any(type(x) is not int for x in edge.window)
                or not edge.start < edge.window[0] <= edge.window[1] < edge.end
                or type(edge.alpha) not in (float, int)
                or edge.alpha not in profile.alpha_candidates):
            raise ValueError("A is one supported contiguous window strictly between D boundaries")
    elif edge.alpha != 0:
        raise ValueError("A pure-C interval has no correction strength")
    return edge


def edge_variants(profile, start, end):
    plain = Edge(start, end)
    try:
        validate_edge(profile, plain)
    except ValueError:
        return ()
    result = [plain]
    for first in range(start + 1, end):
        for last in range(first, end):
            for alpha in sorted(profile.alpha_candidates):
                result.append(Edge(start, end, (first, last), float(alpha)))
    return tuple(result)


def enumerate_edges(profile):
    return tuple(edge for start in range(1, profile.horizon + 1)
        for end in range(start + 1, min(profile.horizon + 1,
                                      start + profile.max_source_age + 1) + 1)
        for edge in edge_variants(profile, start, end))


def required_anchors(profile, edge):
    actions = {edge.action_at(t) for t in range(edge.start + 1, edge.end)}
    return max([0] + ([profile.min_C_anchors] if "C" in actions else [])
                  + ([profile.min_A_anchors] if "A" in actions else []))


def compile_policy(profile, edges):
    edges = tuple(edges)
    actions, alpha, source_before = [], [], []
    position, anchors, last_dense = 1, 0, None
    for edge in edges:
        validate_edge(profile, edge)
        if edge.start != position:
            raise ValueError("A policy is one connected path from 1 to N+1")
        anchors += 1
        if anchors < required_anchors(profile, edge):
            raise ValueError("Readout lacks the required strictly causal true-D anchors")
        for step in range(edge.start, edge.end):
            action = edge.action_at(step)
            source_before.append(last_dense)
            actions.append(action)
            alpha.append(edge.alpha if action == "A" else None)
            if action == "D":
                last_dense = step
        position = edge.end
    if position != profile.horizon + 1 or len(actions) != profile.horizon:
        raise ValueError("The terminal node performs no update; all N updates must be covered")
    identity = dict(profile=profile.fingerprint, actions=actions, shared_alpha=alpha)
    return dict(version=VERSION, fingerprint=digest(identity),
        profile_identity=profile.identity, grammar_sha256=profile.fingerprint,
        dense_mask=[x == "D" for x in actions], actions=actions, shared_alpha=alpha,
        source_before=source_before,
        intervals=[dict(start=e.start, end=e.end, A_window=list(e.window), alpha=e.alpha)
                   for e in edges],
        terminal_node=profile.horizon + 1, terminal_model_calls=0,
        counts={a: actions.count(a) for a in ("D", "A", "C")},
        fallback_policy="FULL_D_ON_UNSUPPORTED_OR_NONFINITE_READOUT_RECORD_ACTUAL_COST",
        budget_predicted_seconds=None, budget_observed_seconds=None,
        deployment_budget_status="BUDGET_NOT_VERIFIED",
        production_CPU_accepted=False, GPU_dispatch_ready=False)
