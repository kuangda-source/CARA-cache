"""Reconstruct frozen H1 receipts and optionally summarize new read-only E0 data."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean, median
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wcomr.p_acr_e0_analysis import fixed_direction_error, near, scalar_oracles, verify_h1_step

H1 = "reports/wc_h1_cost_curve_full60_collection_20261014_0245.json.gz"
PARAM = "manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, obj):
    with path.open("x") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def h1_analysis():
    capture = json.loads(gzip.decompress((ROOT / H1).read_bytes()))
    parameters = json.loads((ROOT / PARAM).read_text())
    frozen = {k: v for k, v in parameters.items() if k != "fingerprint"}
    near_fingerprint = hashlib.sha256(json.dumps(frozen, sort_keys=True, allow_nan=False).encode()).hexdigest()
    if near_fingerprint != parameters["fingerprint"]:
        raise ValueError("H1 frozen parameter fingerprint changed")
    paths = []
    for run in capture["runner"]["runs"]:
        if run["section"] != "TIMED" or run["method"] not in ("H1_LOW", "H1_MID", "H1_HIGH"):
            continue
        if run["curve_parameters_fingerprint"] != parameters["fingerprint"] and run["method"] == "H1_MID":
            raise ValueError("MID parameter identity changed")
        if len(run["source_history"]) != 36 or [x["step"] for x in run["source_history"]] != list(range(1, 37)):
            raise ValueError("Full36 decision denominator required")
        rows = [verify_h1_step(x, parameters, run["curve_lambda"]) for x in run["source_history"]]
        for row in rows:
            row["scheduler_timestep"] = run["scheduler_timesteps"][row["step"] - 1]
            row["sigma"] = None  # timestep is not sigma; no guessed conversion
        paths.append({"id": run["id"], "scene": run["scene"], "method": run["method"],
                      "lambda": run["curve_lambda"], "rows": rows,
                      "categories": dict(Counter(r["category"] for r in rows)),
                      "semantic_actions": dict(Counter(r["actual_readout"] for r in rows)),
                      "no_H1_branch_teacher_saved_in_clean_run": True,
                      "pre_action_probe_tensor_history_saved": False})
    if len(paths) != 12 or len({p["scene"] for p in paths}) != 4:
        raise ValueError("All three lambdas times four scenes required")
    mid = [p for p in paths if p["method"] == "H1_MID"]
    active = [r for p in mid for r in p["rows"] if r["category"] == "OPTIMIZER"]
    active_d = [r for r in active if r["winner"] == "D"]
    near_boundary = sorted(({"scene": p["scene"], "step": r["step"], "winner": r["winner"],
                             "runner_up": r["runner_up"], "margin_seconds": r["margin_seconds"]}
                            for p in mid for r in p["rows"] if r["category"] == "OPTIMIZER"),
                           key=lambda r: r["margin_seconds"])
    result = {"status": "E0_ALL12_H1_PATHS432_STEPS_INDEPENDENTLY_RECONSTRUCTED",
              "sources": {H1: sha(ROOT / H1), PARAM: sha(ROOT / PARAM)},
              "frozen_fingerprint": parameters["fingerprint"], "source_revision": capture["source_revision"],
              "paths": paths,
              "mid_summary": {"paths": 4, "steps": 144, "active_scores": len(active),
                              "active_D_steps_each": sorted({r["step"] for r in active_d}),
                              "protected_steps_each": [r["step"] for r in mid[0]["rows"] if r["protected"]],
                              "active_margin_range_seconds": [min(r["margin_seconds"] for r in active), max(r["margin_seconds"] for r in active)],
                              "active_D_margin_range_seconds": [min(r["margin_seconds"] for r in active_d), max(r["margin_seconds"] for r in active_d)],
                              "closest_boundaries": near_boundary[:12],
                              "D31": [{"scene": p["scene"], **p["rows"][30]} for p in mid]},
              "GPU_submissions": 0, "model_forwards": 0, "policy_changes": 0}
    return result


def oracle_analysis(remote, parameters):
    if remote["status"] != "E0_ALL28_RAW_FILES_CPU_READ_IDENTITY_VERIFIED" or remote["budget_before_sha256"] != remote["budget_after_sha256"]:
        raise ValueError("Complete read-only raw audit required")
    group = next(g for g in remote["groups"] if g["kind"] == "SOURCE_PHASE16")
    if len(group["points"]) != 16:
        raise ValueError("All16 same-state source/phase controls required")
    families = []
    for point in group["points"]:
        sel = point["selection"]
        for name in ("C", "D_REFERENCE_A", "FUSION_A"):
            m = point["moments"][name]
            oracle = scalar_oracles(m["mc"], m["mu"], m["cross"])
            near(oracle["q_base"], m["q_guided_direct"], "raw CFG Gram identity")
            costs = parameters["cost_seconds"]
            price_a = parameters["source_A_cost_seconds"][sel["source"]]
            qa = oracle["q_base"]
            # Conditional price ceiling, not a measured new P price/latency.
            ceiling = {direction: costs["D"] - (oracle["q_" + direction + "_oracle"] / qa) * (costs["D"] - price_a)
                       if qa > 0 and name != "C" else None for direction in ("Pc", "Pu")}
            families.append({"scene": sel["scene"], "source": sel["source"], "phase": sel["phase"],
                             "step": sel["chosen"]["step"], "readout": name,
                             "sigma": point["sigma"], "moments": m, **oracle,
                             "fixed_0": {d: fixed_direction_error(m["mc"], m["mu"], m["cross"], d, 0.) for d in ("Pc", "Pu")},
                             "fixed_1": {d: fixed_direction_error(m["mc"], m["mu"], m["cross"], d, 1.) for d in ("Pc", "Pu")},
                             "max_competitive_price_vs_A_D_seconds": ceiling,
                             "price_scope": parameters["prices_scope"], "trajectory": "PI0_NOT_H1",
                             "directions_selected_using_current_teacher": True, "deployable_coefficient": False})
    summaries = []
    for name in ("C", "D_REFERENCE_A", "FUSION_A"):
        for source in ("ALL", "D", "P"):
            rows = [r for r in families if r["readout"] == name and (source == "ALL" or r["source"] == source)]
            q = mean(r["q_base"] for r in rows)
            summaries.append({"readout": name, "source": source, "states": len(rows), "q_base_mean": q,
                              "Pc_mean_loss_reduction_fraction": 1 - mean(r["q_Pc_oracle"] for r in rows) / q,
                              "Pu_mean_loss_reduction_fraction": 1 - mean(r["q_Pu_oracle"] for r in rows) / q,
                              "Pc_median_point_gain_fraction": median(r["Pc_gain_fraction"] for r in rows),
                              "Pu_median_point_gain_fraction": median(r["Pu_gain_fraction"] for r in rows),
                              "best_per_point_oracle_mean_loss_reduction_fraction": 1 - mean(min(r["q_Pc_oracle"], r["q_Pu_oracle"]) for r in rows) / q})
    return {"status": "E0_16_PI0_STATES48_OFFLINE_READOUT_FAMILIES_ANALYZED", "families": families,
            "summaries": summaries, "new_P_clean_price_measured": False,
            "H1_active_D_states_measured": False, "endpoint_or_deployed_action_result": False,
            "current_teacher_as_online_input": False}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--h1-output", type=Path)
    a.add_argument("--remote-capture", type=Path)
    a.add_argument("--oracle-output", type=Path)
    args = a.parse_args()
    if not args.h1_output and not args.remote_capture:
        raise ValueError("H1 output or audited raw oracle input required")
    if args.h1_output:
        result = h1_analysis()
        write_new(args.h1_output, result)
        print(json.dumps({"H1": result["status"], "mid": {k: v for k, v in result["mid_summary"].items() if k not in ("D31", "closest_boundaries")}}))
    if args.remote_capture:
        if not args.oracle_output:
            raise ValueError("New oracle output path required")
        remote = json.loads(gzip.decompress(args.remote_capture.read_bytes()))["remote"]
        parameters = json.loads((ROOT / PARAM).read_text())
        oracle = oracle_analysis(remote, parameters)
        oracle["sources"] = {str(args.remote_capture): sha(args.remote_capture), PARAM: sha(ROOT / PARAM)}
        write_new(args.oracle_output, oracle)
        print(json.dumps({"oracle": oracle["status"], "fusion_summaries": [r for r in oracle["summaries"] if r['readout'] == 'FUSION_A']}))


if __name__ == "__main__":
    main()
