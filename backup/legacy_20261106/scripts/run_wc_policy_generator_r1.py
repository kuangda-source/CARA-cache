#!/usr/bin/env python3
"""Read a finite JSON proposal bundle; write CPU proposals, never launch models."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.policy_generator_r1.proposal_tables import Costs, QuadraticStats, make_proxy_graph
from wcomr.policy_generator_r1.budgeted_planner import solve, two_topologies
from wcomr.policy_generator_r1.search_protocol import front_dense_control, initial_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.input.read_bytes()
    data = json.loads(source)
    p = dict(data["profile"])
    p["protected_dense"] = tuple(p["protected_dense"])
    p["alpha_candidates"] = tuple(p["alpha_candidates"])
    profile = Profile(**p)
    c = dict(data["costs"])
    c["dense_seconds"], c["C_seconds"] = tuple(c["dense_seconds"]), tuple(c["C_seconds"])
    c["A_seconds_by_alpha"] = {float(a): tuple(v) for a, v in c["A_seconds_by_alpha"].items()}
    costs = Costs(**c)
    statistics = {}
    for row in data["statistics"]:
        key = (row["member"], row["source"], row["update"])
        if key in statistics:
            raise ValueError("Duplicate source/time/member statistics")
        statistics[key] = QuadraticStats(row["e2"], row["ed"], row["d2"], row["fusion_contract"])
    graph = make_proxy_graph(profile, statistics=statistics, fit_members=tuple(data["CAL_FIT_members"]),
        costs=costs, weights=tuple(data["weights"]), label_basis=data["label_basis"],
        statistic_profile_identity=data["statistic_profile_identity"])
    result = solve(profile, graph["graph"], budget_seconds=data["budget_seconds"],
        shared_seconds=costs.shared_seconds, quantum_seconds=data["quantum_seconds"],
        paths_per_state=data["paths_per_state"], maximum_final_paths=data["maximum_final_paths"])
    controls = {mode: front_dense_control(profile, costs, budget_seconds=data["budget_seconds"],
        mode=mode, quantum_seconds=data["quantum_seconds"]) for mode in ("C", "A")}
    output = dict(scope="CPU_PROPOSALS_ONLY_NO_COSMOS_OR_VIDEO_RESULT", input_sha256=hashlib.sha256(source).hexdigest(),
        input_evidence_kind=costs.evidence_kind, label_basis=graph["label_basis"],
        table_status=graph["status"], missing_cells=graph["missing_cells"],
        result=result, initial_simple_controls=controls, graph_two_topologies=two_topologies(result),
        first_endpoint_batch=initial_batch(controls, two_topologies(result)),
        final_selected_policy=None, actual_budget_verified=False,
        production_CPU_accepted=False, GPU_dispatch_ready=False, new_GPU_submissions=0)
    # Missing real proposal cells are an actionable gap, not inferred zero risk.
    if graph["missing_cells"]:
        output["scope"] = "CALIBRATION_ASSETS_REQUIRED_PARTIAL_GRAPH_ONLY"
    with args.output.open("x") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(dict(output=str(args.output), scope=output["scope"],
        proposals=len(result["proposals"]), missing_cells=len(graph["missing_cells"]), new_GPU_submissions=0)))


if __name__ == "__main__":
    main()
