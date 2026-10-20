"""Finite proxy-graph DP, with conservative discrete predicted costs only.

The capped anchor-count state enforces structural warmup. It does not make
the actual latent/cache/solver process Markovian or its final loss additive.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import math

from .interval_grammar import compile_policy, required_anchors, validate_edge


def number(value, name, positive=False):
    if (type(value) not in (int, float) or not math.isfinite(value)
            or (value <= 0 if positive else value < 0)):
        raise ValueError(name + " must be finite and " + ("positive" if positive else "nonnegative"))
    return float(value)


def cost_units(seconds, quantum):
    number(seconds, "interval cost", True)
    number(quantum, "cost quantum", True)
    return int((Decimal(str(seconds)) / Decimal(str(quantum))).to_integral_value(rounding=ROUND_CEILING))


@dataclass(frozen=True)
class ScoredEdge:
    edge: object
    predicted_seconds: float
    proxy_loss: float


@dataclass(frozen=True)
class Path:
    edges: tuple
    loss_terms: tuple
    predicted_terms: tuple
    units: int

    @property
    def loss(self):
        return math.fsum(self.loss_terms)

    @property
    def seconds(self):
        return math.fsum(self.predicted_terms)

    @property
    def key(self):
        return (self.loss, self.units, tuple(e.key for e in self.edges))


def solve(profile, graph, *, budget_seconds, shared_seconds, quantum_seconds,
          paths_per_state=4, maximum_final_paths=32):
    number(budget_seconds, "deployment budget", True)
    number(shared_seconds, "shared work")
    number(quantum_seconds, "cost quantum", True)
    if (type(paths_per_state) is not int or paths_per_state < 1
            or type(maximum_final_paths) is not int or maximum_final_paths < 1):
        raise ValueError("Freeze positive integer path retention limits")
    available = Decimal(str(budget_seconds)) - Decimal(str(shared_seconds))
    budget_units = int((available / Decimal(str(quantum_seconds))).to_integral_value(rounding=ROUND_FLOOR))
    by_start, identities = {}, set()
    for scored in graph:
        validate_edge(profile, scored.edge)
        number(scored.predicted_seconds, "edge cost", True)
        number(scored.proxy_loss, "proxy loss")
        if scored.edge.key in identities:
            raise ValueError("Duplicate edge identity in a supplied graph")
        identities.add(scored.edge.key)
        by_start.setdefault(scored.edge.start, []).append(scored)
    for values in by_start.values():
        values.sort(key=lambda x: x.edge.key)
    # State: boundary, spent discrete cost, true-anchor count capped at the
    # adapter's structural requirement. Keep multiple paths for proposals.
    states = {1: {(0, 0): [Path((), (), (), 0)]}}
    for start in range(1, profile.horizon + 1):
        for (spent, anchors), labels in list(states.get(start, {}).items()):
            for scored in by_start.get(start, ()):
                after = min(anchors + 1, profile.anchor_cap)
                if after < required_anchors(profile, scored.edge):
                    continue
                units = cost_units(scored.predicted_seconds, quantum_seconds)
                if spent + units > budget_units:
                    continue
                target = states.setdefault(scored.edge.end, {}).setdefault((spent + units, after), [])
                for label in labels:
                    target.append(Path(label.edges + (scored.edge,),
                        label.loss_terms + (scored.proxy_loss,),
                        label.predicted_terms + (scored.predicted_seconds,), spent + units))
                target.sort(key=lambda p: p.key)
                del target[paths_per_state:]
    final = [p for labels in states.get(profile.horizon + 1, {}).values() for p in labels]
    final.sort(key=lambda p: p.key)
    proposals, seen = [], set()
    for path in final:
        policy = compile_policy(profile, path.edges)
        policy["budget_predicted_seconds"] = math.fsum((shared_seconds, path.seconds))
        if policy["fingerprint"] in seen:
            continue
        seen.add(policy["fingerprint"])
        proposals.append(dict(policy=policy, proxy_loss=path.loss,
            predicted_seconds=math.fsum((shared_seconds, path.seconds)),
            discrete_cost_units=path.units, discrete_budget_units=budget_units))
        if len(proposals) == maximum_final_paths:
            break
    return dict(status=("PROXY_PROPOSALS_ONLY_ACTUAL_BUDGET_UNVERIFIED" if proposals
                        else "BUDGET_NOT_VERIFIED"), proposals=proposals,
        nearest_verified_policy=None,
        claim="Best path is exact only for the supplied finite additive proxy graph and discrete predicted budget",
        diversity_scope="Retained path reservoir; no guarantee of globally optimal diverse topologies",
        budget_seconds=budget_seconds, shared_seconds=shared_seconds,
        quantum_seconds=quantum_seconds, production_CPU_accepted=False,
        GPU_dispatch_ready=False)


def two_topologies(result):
    """Best proxy path, then maximum dense-mask distance in retained pool."""
    if not result["proposals"]:
        return ()
    first = result["proposals"][0]
    mask = first["policy"]["dense_mask"]
    candidates = [r for r in result["proposals"][1:] if r["policy"]["dense_mask"] != mask]
    candidates.sort(key=lambda r: (-sum(a != b for a, b in zip(mask, r["policy"]["dense_mask"])),
                                   r["proxy_loss"], r["predicted_seconds"], r["policy"]["fingerprint"]))
    return (first, candidates[0]) if candidates else (first,)
