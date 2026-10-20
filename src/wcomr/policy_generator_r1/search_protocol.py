"""Deterministic proposal controls, one joint refinement, and query accounting.

These are CPU interfaces. Evaluators must supply complete natural-trajectory
endpoints; no function here loads a diffusion model or dispatches a GPU.
"""
from decimal import Decimal, ROUND_FLOOR
import math

from .budgeted_planner import cost_units, number
from .interval_grammar import Edge, compile_policy


def initial_batch(simple_controls, graph_candidates):
    """Four fixed slots; duplicate plans are aliases, never free extra queries."""
    slots = [("SIMPLE_C", simple_controls.get("C")), ("SIMPLE_A", simple_controls.get("A"))]
    slots += [("GRAPH_MIN", graph_candidates[0] if graph_candidates else None),
              ("GRAPH_DIVERSE", graph_candidates[1] if len(graph_candidates) > 1 else None)]
    selected, unavailable = {}, []
    for role, row in slots:
        if row is None:
            unavailable.append(role)
            continue
        key = row["policy"]["fingerprint"]
        if key not in selected:
            selected[key] = dict(proposal=row, roles=[])
        selected[key]["roles"].append(role)
    return dict(batch=list(selected.values()), unavailable_roles=unavailable,
                distinct_endpoint_information_queries=len(selected))


def _path_proposal(profile, edges, costs, budget, quantum, lookup=None):
    policy = compile_policy(profile, edges)
    seconds = [costs.edge_seconds(e) for e in edges]
    units = sum(cost_units(t, quantum) for t in seconds)
    available = int(((Decimal(str(budget)) - Decimal(str(costs.shared_seconds)))
                     / Decimal(str(quantum))).to_integral_value(rounding=ROUND_FLOOR))
    if units > available:
        return None
    if lookup is not None and any(e.key not in lookup for e in edges):
        return None
    policy["budget_predicted_seconds"] = math.fsum((costs.shared_seconds, *seconds))
    return dict(policy=policy, predicted_seconds=math.fsum((costs.shared_seconds, *seconds)),
        proxy_loss=(math.fsum(lookup[e.key].proxy_loss for e in edges) if lookup is not None else None),
        discrete_cost_units=units)


def front_dense_control(profile, costs, *, budget_seconds, mode, quantum_seconds):
    """Generic prefix/periodic tail grammar, selected with cost only, no endpoints."""
    costs.validate(profile)
    if mode not in ("C", "A") or (mode == "A" and 1.0 not in profile.alpha_candidates):
        raise ValueError("Frozen simple controls use all-C or all-A at shared alpha=1")
    candidates = {}
    for prefix in range(1, profile.horizon + 1):
        for period in range(1, profile.max_source_age + 2):
            dense = sorted(set(range(1, prefix + 1)) | set(profile.protected_dense)
                           | set(range(prefix + period, profile.horizon + 1, period)))
            bounds = dense + [profile.horizon + 1]
            edges = tuple(Edge(s, r, (s + 1, r - 1) if mode == "A" and r > s + 1 else (),
                               1.0 if mode == "A" and r > s + 1 else 0.0)
                          for s, r in zip(bounds, bounds[1:]))
            try:
                candidate = _path_proposal(profile, edges, costs, budget_seconds, quantum_seconds)
            except ValueError:
                continue
            if candidate is not None:
                candidates[candidate["policy"]["fingerprint"]] = candidate
    def key(c):
        actions = c["policy"]["actions"]
        prefix = next((i for i, a in enumerate(actions) if a != "D"), len(actions))
        return (-actions.count("D"), -prefix, c["predicted_seconds"], c["policy"]["fingerprint"])
    return min(candidates.values(), key=key) if candidates else None


def joint_neighbors(profile, graph, costs, incumbent_policies, *, budget_seconds,
                    quantum_seconds, seen=(), maximum=4, variants_per_boundary=4):
    """Merge, split/move a boundary, or change an interval's readout.

    All changed intervals are rebuilt from the supplied legal graph. The
    frozen finite variant cap controls CPU proposal size; it is not an
    optimality claim. Rank by proxy, predicted cost, then canonical identity.
    """
    if type(maximum) is not int or maximum < 1 or type(variants_per_boundary) is not int or variants_per_boundary < 1:
        raise ValueError("Freeze positive neighbor and per-boundary retention limits")
    lookup = {x.edge.key: x for x in graph}
    if len(lookup) != len(graph):
        raise ValueError("Duplicate graph edges")
    by_bounds = {}
    for item in graph:
        by_bounds.setdefault((item.edge.start, item.edge.end), []).append(item)
    for key in by_bounds:
        by_bounds[key].sort(key=lambda x: (x.proxy_loss, x.predicted_seconds, x.edge.key))
        by_bounds[key] = [x.edge for x in by_bounds[key][:variants_per_boundary]]
    candidates = {}
    seen = set(seen)
    def consider(edges):
        try:
            candidate = _path_proposal(profile, tuple(edges), costs, budget_seconds, quantum_seconds, lookup)
        except ValueError:
            return
        if candidate and candidate["policy"]["fingerprint"] not in seen:
            candidates[candidate["policy"]["fingerprint"]] = candidate
    for policy in incumbent_policies:
        if policy["grammar_sha256"] != profile.fingerprint:
            raise ValueError("Incumbent belongs to another profile")
        original = tuple(Edge(i["start"], i["end"], tuple(i["A_window"]), i["alpha"])
                         for i in policy["intervals"])
        # Validate the entire incumbent, including required causal anchors.
        if compile_policy(profile, original)["fingerprint"] != policy["fingerprint"]:
            raise ValueError("Incumbent identity mismatch")
        for index, edge in enumerate(original):
            for replacement in by_bounds.get((edge.start, edge.end), ()):
                consider(original[:index] + (replacement,) + original[index + 1:])
            for split in range(edge.start + 1, edge.end):
                for left in by_bounds.get((edge.start, split), ()):
                    for right in by_bounds.get((split, edge.end), ()):
                        consider(original[:index] + (left, right) + original[index + 1:])
        for index in range(len(original) - 1):
            left, right = original[index:index + 2]
            for merged in by_bounds.get((left.start, right.end), ()):
                consider(original[:index] + (merged,) + original[index + 2:])
            for middle in range(left.start + 1, right.end):
                if middle == right.start:
                    continue
                for new_left in by_bounds.get((left.start, middle), ()):
                    for new_right in by_bounds.get((middle, right.end), ()):
                        consider(original[:index] + (new_left, new_right) + original[index + 2:])
    return sorted(candidates.values(), key=lambda c: (c["proxy_loss"], c["predicted_seconds"],
                                                      c["policy"]["fingerprint"]))[:maximum]


class QueryLedger:
    """An old scored plan still consumes an information query when exposed."""
    def __init__(self, query_limit, calibration_GPUh_limit):
        if type(query_limit) is not int or query_limit < 1:
            raise ValueError("Positive endpoint information-query limit required")
        number(calibration_GPUh_limit, "complete calibration GPUh budget", True)
        self.query_limit, self.GPUh_limit = query_limit, calibration_GPUh_limit
        self.exposures, self.charges = {}, []
        self.charge_events = []
        self.selection_started = False
        self.selection_plans = ()

    @property
    def spent_GPUh(self):
        return math.fsum(self.charges)

    def may_evaluate(self, fingerprint, next_complete_GPUh_quote):
        number(next_complete_GPUh_quote, "next complete evaluation quote")
        return (not self.selection_started and fingerprint not in self.exposures and len(self.exposures) < self.query_limit
                and self.spent_GPUh + next_complete_GPUh_quote <= self.GPUh_limit)

    def begin_selection(self, frozen_plan_ids):
        if (self.selection_started or not frozen_plan_ids
                or len(set(frozen_plan_ids)) != len(frozen_plan_ids)
                or any(p not in self.exposures or self.exposures[p]["status"] != "COMPLETE"
                       for p in frozen_plan_ids)):
            raise ValueError("Select once from frozen, already evaluated, complete plans")
        self.selection_started = True
        self.selection_plans = tuple(frozen_plan_ids)

    def charge_preparation(self, *, actual_GPUh, description):
        number(actual_GPUh, "actual preparation/teacher/scoring GPUh")
        if not isinstance(description, str) or not description:
            raise ValueError("Identify teacher, warmup, scoring, or other calibration work")
        self.charges.append(actual_GPUh)
        self.charge_events.append(dict(kind="PREPARATION", description=description, actual_GPUh=actual_GPUh))

    def expose(self, fingerprint, *, origin, charged_GPUh, status):
        if not isinstance(fingerprint, str) or not fingerprint:
            raise ValueError("A complete plan identity is required")
        if origin not in ("NEW_EVALUATION", "ACCEPTED_PRIOR_ENDPOINT"):
            raise ValueError("Track newly computed cost separately from old endpoint information")
        if status not in ("COMPLETE", "REJECTED", "TECHNICAL_FAILURE"):
            raise ValueError("Preserve failed/rejected evaluation attempts")
        number(charged_GPUh, "actual charged GPUh")
        if self.selection_started or fingerprint in self.exposures or len(self.exposures) >= self.query_limit:
            raise ValueError("No duplicate information query or replacement beyond the frozen quota")
        if origin == "ACCEPTED_PRIOR_ENDPOINT" and charged_GPUh != 0:
            raise ValueError("Reusing an endpoint adds information, not a new GPU bill")
        self.exposures[fingerprint] = dict(origin=origin, status=status)
        self.charges.append(charged_GPUh)
        self.charge_events.append(dict(kind=origin, fingerprint=fingerprint, actual_GPUh=charged_GPUh))
        return "CALIBRATION_CAP_EXCEEDED_STOP" if self.spent_GPUh > self.GPUh_limit else "RECORDED"


def choose_observed(records, *, members, candidate_fingerprints, budget_seconds, timing_protocol,
                    profile_identity, split, loss_ceiling):
    """Prompt-equal averaging, then finite deterministic measured selection.

    members are (prompt,seed) pairs. No partial candidate, failed position,
    teacher proxy, TEST record, or incompatible timing is silently accepted.
    """
    if split not in ("CAL_FIT", "CAL_SELECT") or not timing_protocol or not members:
        raise ValueError("Frozen calibration split and timing boundary required")
    if len(set(members)) != len(members):
        raise ValueError("Duplicate calibration members")
    if not candidate_fingerprints or len(set(candidate_fingerprints)) != len(candidate_fingerprints):
        raise ValueError("Freeze every candidate, including plans with no returned endpoints")
    number(budget_seconds, "observed deployment budget", True)
    prompt_ids = {p for p, _seed in members}
    if isinstance(loss_ceiling, dict):
        if set(loss_ceiling) != prompt_ids:
            raise ValueError("Freeze a tail ceiling for every prompt")
        ceilings = loss_ceiling
        for ceiling in ceilings.values():
            number(ceiling, "per-prompt loss ceiling")
    else:
        number(loss_ceiling, "predeclared per-prompt loss ceiling")
        ceilings = {p: loss_ceiling for p in prompt_ids}
    by_plan, seen = {p: {} for p in candidate_fingerprints}, set()
    for record in records:
        member = (record["prompt"], record["seed"])
        key = (record["fingerprint"], member)
        if (record["split"] != split or member not in members or key in seen
                or record["fingerprint"] not in by_plan
                or record["timing_protocol"] != timing_protocol
                or record["profile_identity"] != profile_identity
                or record.get("endpoint_basis") != "NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS"):
            raise ValueError("Foreign/duplicate split, profile, timing, or non-endpoint evidence")
        seen.add(key)
        by_plan.setdefault(record["fingerprint"], {})[member] = record
    feasible, excluded = [], {}
    for fingerprint, rows in by_plan.items():
        if set(rows) != set(members) or any(r["status"] != "COMPLETE" for r in rows.values()):
            excluded[fingerprint] = "MISSING_REJECTED_OR_FAILED_FULL_DENOMINATOR_RETAINED"
            continue
        prompts = {}
        for (prompt, _seed), row in rows.items():
            number(row["LPIPS"], "observed loss")
            number(row["measured_seconds"], "observed time", True)
            prompts.setdefault(prompt, []).append(row)
        loss = [math.fsum(r["LPIPS"] for r in values) / len(values) for values in prompts.values()]
        times = [math.fsum(r["measured_seconds"] for r in values) / len(values) for values in prompts.values()]
        avg_loss, avg_seconds = math.fsum(loss) / len(loss), math.fsum(times) / len(times)
        if avg_seconds > budget_seconds or any(value > ceilings[p] for p,value in zip(prompts,loss)):
            excluded[fingerprint] = "OUTSIDE_PREDECLARED_MEASURED_TIME_OR_TAIL_GUARD"
            continue
        feasible.append(dict(fingerprint=fingerprint, mean_LPIPS=avg_loss,
                             measured_mean_seconds=avg_seconds, prompts=len(prompts)))
    feasible.sort(key=lambda x: (x["mean_LPIPS"], x["measured_mean_seconds"], x["fingerprint"]))
    return dict(status="OBSERVED_CALIBRATION_FEASIBLE" if feasible else "BUDGET_NOT_VERIFIED",
        selected=feasible[0] if feasible else None, order=feasible, excluded=excluded,
        split=split, is_independent_TEST=False, production_CPU_accepted=False)
