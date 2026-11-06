"""Independent small-graph oracle and scientific-boundary failure controls."""
import copy
import math
import random
import unittest

from wcomr.policy_generator_r1.interval_grammar import (Profile, Edge, compile_policy,
    enumerate_edges, edge_variants, validate_edge)
from wcomr.policy_generator_r1.budgeted_planner import solve, cost_units, two_topologies
from wcomr.policy_generator_r1.proposal_tables import Costs, QuadraticStats, make_proxy_graph
from wcomr.policy_generator_r1.search_protocol import (front_dense_control, joint_neighbors,
    QueryLedger, choose_observed, initial_batch)


def fixture(n=6, minimum_A=2):
    profile = Profile(n, (1, n), 2, 1, minimum_A, "synthetic-profile-" + str(n))
    costs = Costs((4.0,) * n, (1.0,) * n, {0.5: (2.5,) * n, 1.0: (1.5,) * n},
                  3.0, profile.identity, "synthetic-paid-whole-request", "SYNTHETIC_UNIT_FIXTURE")
    stats = {(member, s, t): QuadraticStats(float((t-s)**2), -0.8*(t-s)**2,
             0.64*(t-s)**2, "VALIDATED_GUIDED_OUTPUT_LINEAR_BLEND")
             for member in ("cal-a", "cal-b") for s in range(1, n)
             for t in range(s+1, min(n, s+profile.max_source_age)+1)}
    bundle = make_proxy_graph(profile, statistics=stats, fit_members=("cal-a", "cal-b"),
        costs=costs, weights=(1.0,)*n, label_basis="SYNTHETIC_UNIT_FIXTURE",
        statistic_profile_identity=profile.identity)
    return profile, costs, stats, bundle


def exhaustive(profile, graph):
    """Enumerate complete paths independently; grammar checks only at the leaf."""
    by_start = {}
    for row in graph:
        by_start.setdefault(row.edge.start, []).append(row)
    result = []
    def visit(node, path):
        if node == profile.horizon+1:
            try:
                compile_policy(profile, tuple(r.edge for r in path))
            except ValueError:
                return
            result.append(path)
            return
        for row in by_start.get(node, ()):
            visit(row.edge.end, path+(row,))
    visit(1, ())
    return result


class GrammarTests(unittest.TestCase):
    def test_window_count_and_terminal_no_model_call(self):
        p = Profile(9, (1, 9), 6, 1, 1, "different-adapter")
        self.assertEqual(len(edge_variants(p, 1, 8)), 43)
        policy = compile_policy(p, (Edge(1, 8, (2, 7), 1.0), Edge(8, 9), Edge(9, 10)))
        self.assertEqual(len(policy["actions"]), 9)
        self.assertEqual(policy["terminal_model_calls"], 0)
        self.assertEqual(policy["source_before"][6], 1)

    def test_protected_age_and_stale_overlay_rejected(self):
        p = Profile(8, (1, 4, 8), 3, 1, 1, "adapter")
        for edge in (Edge(1, 6), Edge(4, 9), Edge(1, 4, (2, 4), 1.0)):
            with self.assertRaises(ValueError): validate_edge(p, edge)

    def test_required_anchor_history_is_not_assumed(self):
        p = Profile(4, (1, 4), 2, 1, 2, "adapter")
        with self.assertRaises(ValueError): compile_policy(p, (Edge(1, 4, (2, 3), 1.0), Edge(4, 5)))
        compile_policy(p, (Edge(1, 2), Edge(2, 4, (3, 3), 1.0), Edge(4, 5)))

    def test_other_horizons_and_dense_only_profile(self):
        for n in (1, 5, 13, 41):
            p = Profile(n, (1,) if n == 1 else (1, n), 0, 1, 2, "N-"+str(n))
            policy = compile_policy(p, tuple(Edge(t, t+1) for t in range(1, n+1)))
            self.assertEqual(policy["counts"], {"D": n, "A": 0, "C": 0})

    def test_invalid_profiles_and_edge_canonical_types(self):
        for n in (True, 0, -1):
            with self.assertRaises(ValueError): Profile(n, (1,), 2, 1, 1, "x")
        p, _, _, _ = fixture()
        for edge in (Edge(1, 2, [], 0.0), Edge(1, 2, (), float("nan")), Edge(1, 3, (2, 2), 0.0)):
            with self.assertRaises(ValueError): validate_edge(p, edge)


class PlannerTests(unittest.TestCase):
    def test_DP_best_matches_exhaustive_multiple_graphs_and_budgets(self):
        comparisons = 0
        for n in (3, 4, 5, 6, 7):
            p, costs, _, bundle = fixture(n)
            paths = exhaustive(p, bundle["graph"])
            for units in range(n*3, n*8+1, 3):
                feasible = [path for path in paths if sum(cost_units(r.predicted_seconds, 0.5) for r in path) <= units]
                actual = solve(p, bundle["graph"], budget_seconds=costs.shared_seconds+units*0.5,
                               shared_seconds=costs.shared_seconds, quantum_seconds=0.5, paths_per_state=1)
                comparisons += 1
                if not feasible:
                    self.assertEqual(actual["status"], "BUDGET_NOT_VERIFIED")
                    continue
                expected = min(feasible, key=lambda path: (math.fsum(r.proxy_loss for r in path),
                    sum(cost_units(r.predicted_seconds, 0.5) for r in path), tuple(r.edge.key for r in path)))
                expected_policy = compile_policy(p, tuple(r.edge for r in expected))
                self.assertEqual(actual["proposals"][0]["policy"]["fingerprint"], expected_policy["fingerprint"])
        self.assertGreater(comparisons, 40)

    def test_decimal_rounding_never_grants_an_unpaid_unit(self):
        self.assertEqual(cost_units(0.30000000000000004, 0.1), 4)
        self.assertEqual(cost_units(0.3, 0.1), 3)

    def test_charges_each_update_once_including_shared_and_terminal(self):
        p, c, _, b = fixture(4)
        dense = [e for e in b["graph"] if e.edge.end == e.edge.start+1]
        r = solve(p, dense, budget_seconds=19, shared_seconds=3, quantum_seconds=0.5)
        self.assertEqual(r["proposals"][0]["predicted_seconds"], 19)
        self.assertEqual(r["proposals"][0]["policy"]["counts"]["D"], 4)
        self.assertFalse(solve(p, dense, budget_seconds=18.99, shared_seconds=3, quantum_seconds=0.5)["proposals"])

    def test_deterministic_across_graph_permutation(self):
        p, c, _, b = fixture()
        graph = list(b["graph"])
        a = solve(p, graph, budget_seconds=22, shared_seconds=c.shared_seconds, quantum_seconds=0.5)
        random.Random(17).shuffle(graph)
        self.assertEqual(a, solve(p, graph, budget_seconds=22, shared_seconds=c.shared_seconds, quantum_seconds=0.5))
        self.assertLessEqual(len(two_topologies(a)), 2)

    def test_duplicate_or_bad_cost_not_silently_accepted(self):
        p, c, _, b = fixture()
        with self.assertRaises(ValueError):
            solve(p, b["graph"]+(b["graph"][0],), budget_seconds=22, shared_seconds=c.shared_seconds, quantum_seconds=0.5)


class ProposalTests(unittest.TestCase):
    def test_quadratic_matches_direct_output_blend(self):
        e, d = (1., -2., 3.), (-0.5, 1.0, -1.5)
        s = QuadraticStats(math.fsum(x*x for x in e)/3, math.fsum(x*y for x,y in zip(e,d))/3,
                           math.fsum(x*x for x in d)/3, "VALIDATED_GUIDED_OUTPUT_LINEAR_BLEND")
        for a in (0, 0.5, 1):
            self.assertAlmostEqual(s.at(a), math.fsum((x+a*y)**2 for x,y in zip(e,d))/3)

    def test_nonlinear_fusion_or_impossible_moments_rejected(self):
        for args in [(1., 0., 1., "FEATURE_BEFORE_NONLINEAR_HEAD"), (1., 2., 1., "VALIDATED_GUIDED_OUTPUT_LINEAR_BLEND")]:
            with self.assertRaises(ValueError): QuadraticStats(*args)

    def test_missing_source_time_labels_are_not_zero_filled(self):
        p, c, stats, _ = fixture()
        del stats[("cal-a", 1, 2)]
        b = make_proxy_graph(p, statistics=stats, fit_members=("cal-a", "cal-b"), costs=c,
            weights=(1.,)*p.horizon, label_basis="SYNTHETIC_UNIT_FIXTURE", statistic_profile_identity=p.identity)
        self.assertIn(("cal-a", 1, 2), b["missing_cells"])
        self.assertFalse(any(x.edge.start == 1 and x.edge.end > 2 for x in b["graph"]))

    def test_alpha_prices_and_profile_identity_bound(self):
        p, c, _, _ = fixture()
        self.assertNotEqual(c.edge_seconds(Edge(1, 3, (2, 2), 0.5)), c.edge_seconds(Edge(1, 3, (2, 2), 1.0)))
        wrong = Costs(c.dense_seconds, c.C_seconds, c.A_seconds_by_alpha, 3, "foreign", "protocol", c.evidence_kind)
        with self.assertRaises(ValueError): wrong.validate(p)


class SearchTests(unittest.TestCase):
    def test_duplicate_initial_slots_do_not_create_extra_queries(self):
        proposal = {"policy": {"fingerprint": "same"}}
        batch = initial_batch({"C": proposal, "A": proposal}, (proposal,))
        self.assertEqual(batch["distinct_endpoint_information_queries"], 1)
        self.assertEqual(batch["batch"][0]["roles"], ["SIMPLE_C", "SIMPLE_A", "GRAPH_MIN"])
        self.assertEqual(batch["unavailable_roles"], ["GRAPH_DIVERSE"])

    def test_simple_controls_and_refinements_remain_legal(self):
        p, c, _, b = fixture(7, minimum_A=1)
        initial = front_dense_control(p, c, budget_seconds=25, mode="A", quantum_seconds=0.5)
        self.assertIsNotNone(initial)
        seen = (initial["policy"]["fingerprint"],)
        neighbors = joint_neighbors(p, b["graph"], c, (initial["policy"],), budget_seconds=25,
                                    quantum_seconds=0.5, seen=seen, maximum=1000)
        self.assertTrue(neighbors)
        self.assertTrue(any(x["policy"]["dense_mask"] != initial["policy"]["dense_mask"] for x in neighbors))
        for row in neighbors:
            self.assertNotIn(row["policy"]["fingerprint"], seen)
            self.assertLessEqual(row["predicted_seconds"], 25)
            self.assertEqual(len(row["policy"]["actions"]), p.horizon)
            self.assertTrue(all(a is None for a,x in zip(row["policy"]["shared_alpha"],row["policy"]["actions"]) if x == "D"))

    def test_old_endpoint_exposure_counts_even_with_zero_compute(self):
        ledger = QueryLedger(2, 1.)
        ledger.charge_preparation(actual_GPUh=0.2, description="teacher and complete warmup")
        ledger.expose("old", origin="ACCEPTED_PRIOR_ENDPOINT", charged_GPUh=0., status="COMPLETE")
        self.assertEqual(len(ledger.exposures), 1)
        self.assertAlmostEqual(ledger.spent_GPUh, 0.2)
        ledger.expose("failed", origin="NEW_EVALUATION", charged_GPUh=0.1, status="TECHNICAL_FAILURE")
        self.assertFalse(ledger.may_evaluate("replacement", 0.1))
        with self.assertRaises(ValueError): ledger.expose("replacement", origin="NEW_EVALUATION", charged_GPUh=0., status="COMPLETE")

    def test_complete_calibration_cap_is_checked_before_next_plan(self):
        ledger = QueryLedger(8, 0.5)
        ledger.charge_preparation(actual_GPUh=0.4, description="proposal statistics")
        self.assertFalse(ledger.may_evaluate("new", 0.2))

    def test_selection_closes_search_before_holdout_is_read(self):
        ledger = QueryLedger(8, 1.)
        ledger.expose("fit", origin="NEW_EVALUATION", charged_GPUh=0.1, status="COMPLETE")
        ledger.begin_selection(("fit",))
        self.assertFalse(ledger.may_evaluate("after-holdout", 0.1))
        with self.assertRaises(ValueError): ledger.begin_selection(("fit",))
        with self.assertRaises(ValueError): ledger.expose("after-holdout", origin="NEW_EVALUATION", charged_GPUh=0., status="COMPLETE")

    def test_prompt_equal_aggregation_and_all_missing_candidate_retained(self):
        members = (("a",1),("a",2),("b",1))
        rows = [dict(fingerprint="p", prompt=p, seed=s, status="COMPLETE", split="CAL_FIT",
            timing_protocol="paid", profile_identity="profile", LPIPS=l, measured_seconds=2.,
            endpoint_basis="NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS")
            for (p,s),l in zip(members,(0.,0.,1.))]
        result = choose_observed(rows, members=members, candidate_fingerprints=("p","absent"), budget_seconds=3,
            timing_protocol="paid", profile_identity="profile", split="CAL_FIT", loss_ceiling=1.)
        self.assertEqual(result["selected"]["mean_LPIPS"], 0.5)
        self.assertIn("absent", result["excluded"])

    def test_TEST_or_proxy_or_incompatible_timing_cannot_select(self):
        row = dict(fingerprint="p", prompt="a", seed=0, status="COMPLETE", split="CAL_FIT",
            timing_protocol="paid", profile_identity="profile", LPIPS=0.1, measured_seconds=2.,
            endpoint_basis="NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS")
        kwargs = dict(members=(("a",0),), candidate_fingerprints=("p",), budget_seconds=3,
                      timing_protocol="paid", profile_identity="profile", split="CAL_FIT", loss_ceiling=1.)
        for key,value in (("split","TEST"),("endpoint_basis","TEACHER_CONDITIONED_PROPOSAL"),("timing_protocol","concurrent")):
            bad = dict(row, **{key:value})
            with self.assertRaises(ValueError): choose_observed([bad], **kwargs)

    def test_rejection_and_over_budget_do_not_produce_a_frozen_policy(self):
        row = dict(fingerprint="p", prompt="a", seed=0, status="COMPLETE", split="CAL_SELECT",
            timing_protocol="paid", profile_identity="profile", LPIPS=0.1, measured_seconds=20.,
            endpoint_basis="NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS")
        kwargs = dict(members=(("a",0),), candidate_fingerprints=("p",), budget_seconds=3,
                      timing_protocol="paid", profile_identity="profile", split="CAL_SELECT", loss_ceiling=1.)
        self.assertEqual(choose_observed([row], **kwargs)["status"], "BUDGET_NOT_VERIFIED")
        row["status"] = "REJECTED"
        self.assertIsNone(choose_observed([row], **kwargs)["selected"])


if __name__ == "__main__":
    unittest.main()
