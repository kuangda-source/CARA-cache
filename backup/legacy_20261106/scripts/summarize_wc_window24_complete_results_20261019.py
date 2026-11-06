#!/usr/bin/env python3
"""Summarize the accepted original Window24 receipt offline."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

METHODS = ("S26-C", "S25-C", "S25-A1", "S25-A3")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--acceptance", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Preserve the original derived analysis")
    raw = a.capture.read_bytes()
    capture = json.loads(gzip.decompress(raw))
    accepted = json.loads(a.acceptance.read_text())
    assert accepted["capture_sha256"] == hashlib.sha256(raw).hexdigest()
    assert accepted["full_protocol_accepted"] and accepted["scientific_accepted"]
    assert accepted["finance"]["finance_accepted"] and not accepted["errors"]
    formal = [r for r in capture["final"]["rows"] if r["section"] == "TIMED"]
    assert len(formal) == 16 and all(r["status"] == "COMPLETE" for r in formal)
    scenes = [r["name"] for r in capture["config"]["requests"]]
    lookup, rows, aggregates = {}, [], {}
    for scene in scenes:
        for method in METHODS:
            row = next(r for r in formal if r["scene"] == scene and r["method"] == method)
            distances = row["LPIPS"]["frame_distances"]
            assert len(distances) == 93 and all(math.isfinite(v) and v >= 0 for v in distances)
            loss = math.fsum(distances) / 93
            assert math.isclose(loss, row["LPIPS"]["mean_LPIPS"], abs_tol=1e-12)
            entry = dict(scene=scene, method=method, LPIPS=loss,
                         core_seconds=row["core_seconds"],
                         guarded_seconds=row["guarded_pipeline_without_write_seconds"],
                         counts=row["counts"], frames=93)
            lookup[scene, method] = (entry, distances)
            rows.append(entry)
    for method in METHODS:
        entries = [lookup[s, method][0] for s in scenes]
        aggregates[method] = {
            "mean_LPIPS": math.fsum(r["LPIPS"] for r in entries) / 4,
            "mean_core_seconds": math.fsum(r["core_seconds"] for r in entries) / 4,
            "mean_guarded_seconds": math.fsum(r["guarded_seconds"] for r in entries) / 4}
    comparisons = []
    for contrast in accepted["contrasts"]:
        ca, ba = contrast["candidate"], contrast["baseline"]
        cs, bs = aggregates[ca], aggregates[ba]
        per_scene = []
        for scene in scenes:
            c, cd = lookup[scene, ca]
            b, bd = lookup[scene, ba]
            per_scene.append(dict(
                scene=scene, LPIPS_change_percent=100 * (c["LPIPS"] / b["LPIPS"] - 1),
                core_change_seconds=c["core_seconds"] - b["core_seconds"],
                improved_frames=sum(x < y for x, y in zip(cd, bd)),
                worsened_frames=sum(x > y for x, y in zip(cd, bd))))
        change = 100 * (cs["mean_LPIPS"] / bs["mean_LPIPS"] - 1)
        assert math.isclose(change, contrast["complete_four_scene_relative_mean_change_percent"],
                            abs_tol=1e-10)
        for r, original in zip(per_scene, contrast["scene_rows"]):
            assert r["scene"] == original["scene"]
            assert (r["improved_frames"], r["worsened_frames"]) == (
                original["improved_frames"], original["worsened_frames"])
        comparisons.append(dict(
            candidate=ca, baseline=ba, equal_scene_LPIPS_change_percent=change,
            equal_scene_core_change_seconds=cs["mean_core_seconds"] - bs["mean_core_seconds"],
            equal_scene_core_change_percent=100 * (cs["mean_core_seconds"] / bs["mean_core_seconds"] - 1),
            core_speedup=bs["mean_core_seconds"] / cs["mean_core_seconds"],
            guarded_speedup=bs["mean_guarded_seconds"] / cs["mean_guarded_seconds"],
            improved_scenes=sum(r["LPIPS_change_percent"] < 0 for r in per_scene),
            per_scene=per_scene))
    loss = {m: aggregates[m]["mean_LPIPS"] for m in METHODS}
    recovery = {m: (loss["S25-C"] - loss[m]) / (loss["S25-C"] - loss["S26-C"])
                for m in ("S25-A1", "S25-A3")}
    result = dict(
        status="WINDOW24_ACCEPTED_ALL16_FRAMES_AND_CONTRASTS_RECOMPUTED_OFFLINE",
        capture_ref=str(a.capture), capture_sha256=hashlib.sha256(raw).hexdigest(),
        acceptance_ref=str(a.acceptance),
        acceptance_sha256=hashlib.sha256(a.acceptance.read_bytes()).hexdigest(),
        source_revision=capture["launch"]["source_revision"],
        registered_paths=24, formal_paths=16, scored_frames=16 * 93,
        rows=rows, aggregates=aggregates, comparisons=comparisons,
        deleted_D_extra_distortion_recovery=recovery,
        original_finance=accepted["finance"],
        pool_snapshot=capture["pool"],
        original_GPU_and_post_terminal=True,
        own_UUID_lock_free=capture["own_UUID_lock_free"],
        all_original_controls_accepted=True, statistical_unit="four old CAL scenes, seed0",
        same_25D_is_not_equal_total_cost=True,
        independent_new_input_confirmation=False, stable_repeated_clean_speed_claim=False,
        multiple_frame_observations_are_independent_samples=False,
        GPU_submissions=0, SSH_queries=0, new_quality_scores=0)
    with a.output.open("x") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(dict(output=str(a.output), aggregates=aggregates,
                         recovery=recovery, actual_GPUh=accepted["actual_GPUh"])))


if __name__ == "__main__":
    main()
