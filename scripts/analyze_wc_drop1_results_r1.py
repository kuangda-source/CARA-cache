#!/usr/bin/env python3
"""Recompute the accepted whole18 endpoint contrasts from all original frames."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


METHODS = ('S26-C', 'S25-C', 'S25-A')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(xs):
    xs = list(xs)
    return math.fsum(xs) / len(xs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--acceptance', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    capture = json.loads(gzip.decompress(a.capture.read_bytes()))
    accepted = json.loads(a.acceptance.read_text())
    assert accepted['accepted'] and not accepted['errors']
    assert accepted['capture_sha256'] == sha(a.capture)
    final = capture['final']
    rows = final['rows']
    assert len(rows) == 18 and all(r['status'] == 'COMPLETE' for r in rows)
    formal = [r for r in rows if r['section'] == 'TIMED']
    assert len(formal) == 12
    scenes = list(dict.fromkeys(r['scene'] for r in formal))
    assert len(scenes) == 4
    by = {(r['scene'], r['method']): r for r in formal}
    scene_rows, comparisons = [], []
    for scene in scenes:
        triplet = {m: by[(scene, m)] for m in METHODS}
        scores = {m: r['LPIPS'] for m, r in triplet.items()}
        assert len({v['reference_sha256'] for v in scores.values()}) == 1
        assert all(v['pts'] == scores['S26-C']['pts'] for v in scores.values())
        values = {}
        for method, row in triplet.items():
            score = scores[method]
            frames = score['frame_distances']
            assert len(frames) == score['frames'] == row['decoded_video']['frames'] == 93
            assert len(score['pts']) == 93 and all(math.isfinite(x) and x >= 0 for x in frames)
            assert score['candidate_sha256'] == row['video_artifact']['sha256']
            q = mean(frames)
            assert math.isclose(q, score['mean_LPIPS'], rel_tol=0, abs_tol=1e-15)
            values[method] = dict(
                LPIPS=q, core_seconds=row['core_seconds'],
                guarded_invocation_without_write_seconds=row['guarded_pipeline_without_write_seconds'],
                counts=row['counts'], original_id=row['id'], frames=93,
                reference_sha256=score['reference_sha256'],
                video_sha256=score['candidate_sha256'])
        denom = values['S25-C']['LPIPS'] - values['S26-C']['LPIPS']
        scene_rows.append(dict(scene=scene, methods=values,
            recovery_of_deleted_D_distortion_fraction=(values['S25-C']['LPIPS'] - values['S25-A']['LPIPS']) / denom if denom > 0 else None))
    aggregates = {
        m: dict(mean_LPIPS=mean(r['methods'][m]['LPIPS'] for r in scene_rows),
                mean_core_seconds=mean(r['methods'][m]['core_seconds'] for r in scene_rows),
                mean_guarded_invocation_seconds=mean(r['methods'][m]['guarded_invocation_without_write_seconds'] for r in scene_rows))
        for m in METHODS}
    for candidate, baseline in [('S25-A', 'S25-C'), ('S25-A', 'S26-C'), ('S25-C', 'S26-C')]:
        pairs = []
        for row in scene_rows:
            scene = row['scene']
            c, b = row['methods'][candidate], row['methods'][baseline]
            cf, bf = by[(scene, candidate)]['LPIPS']['frame_distances'], by[(scene, baseline)]['LPIPS']['frame_distances']
            pairs.append(dict(scene=scene,
                LPIPS_change=c['LPIPS'] - b['LPIPS'],
                LPIPS_change_percent=100 * (c['LPIPS'] / b['LPIPS'] - 1),
                core_change_seconds=c['core_seconds'] - b['core_seconds'],
                core_change_percent=100 * (c['core_seconds'] / b['core_seconds'] - 1),
                core_speedup_baseline_over_candidate=b['core_seconds'] / c['core_seconds'],
                guarded_speedup_baseline_over_candidate=b['guarded_invocation_without_write_seconds'] / c['guarded_invocation_without_write_seconds'],
                improved_frames=sum(c < b for c, b in zip(cf, bf)),
                worsened_frames=sum(c > b for c, b in zip(cf, bf)),
                tied_frames=sum(c == b for c, b in zip(cf, bf))))
        c, b = aggregates[candidate], aggregates[baseline]
        comparisons.append(dict(candidate=candidate, baseline=baseline, per_scene=pairs,
            independent_scene_denominator=4, independent_seed_count=1,
            improved_scenes=sum(r['LPIPS_change'] < 0 for r in pairs),
            faster_scenes=sum(r['core_change_seconds'] < 0 for r in pairs),
            equal_scene_mean_LPIPS_change_percent=100 * (c['mean_LPIPS'] / b['mean_LPIPS'] - 1),
            mean_individual_scene_LPIPS_change_percent=mean(r['LPIPS_change_percent'] for r in pairs),
            equal_scene_mean_core_change_seconds=c['mean_core_seconds'] - b['mean_core_seconds'],
            equal_scene_mean_core_change_percent=100 * (c['mean_core_seconds'] / b['mean_core_seconds'] - 1),
            core_speedup_ratio_of_equal_scene_means=b['mean_core_seconds'] / c['mean_core_seconds'],
            guarded_speedup_ratio_of_equal_scene_means=b['mean_guarded_invocation_seconds'] / c['mean_guarded_invocation_seconds']))
    pool = capture['pool']
    deleted = aggregates['S25-C']['mean_LPIPS'] - aggregates['S26-C']['mean_LPIPS']
    out = dict(status='ACCEPTED_WHOLE18_ALL12_RAW_FRAME_ENDPOINT_CONTRASTS_RECOMPUTED',
        capture_ref=str(a.capture), capture_sha256=sha(a.capture),
        acceptance_ref=str(a.acceptance), acceptance_sha256=sha(a.acceptance),
        scene_rows=scene_rows, aggregates=aggregates, comparisons=comparisons,
        recovery_of_deleted_D_distortion_ratio_of_equal_scene_means=(aggregates['S25-C']['mean_LPIPS'] - aggregates['S25-A']['mean_LPIPS']) / deleted if deleted > 0 else None,
        all_paths=18, formal_paths=12, formal_frames=1116, failures=0, rejects=0, missing=0,
        actual_GPUh=capture['billing']['actual_GPUh'],
        pool_snapshot={k: pool[k] for k in ('cap_gpu_hours', 'origin_used_gpu_hours', 'used_gpu_hours', 'reserved_gpu_hours', 'available_gpu_hours')},
        fixed_25D_A_versus_C_effect=True, A_alone_cheaper_claim=False,
        stable_repeated_clean_speed_claim=False, independent_new_input_confirmation=False,
        absolute_physics_or_semantic_quality_claim=False, new_GPU_submissions=0,
        frame_sign_counts_are_descriptive_not_independent_samples=True,
        nested_guarded_and_core_intervals_are_not_added=True)
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'aggregates', 'recovery_of_deleted_D_distortion_ratio_of_equal_scene_means', 'actual_GPUh', 'pool_snapshot')}, ensure_ascii=False))
    for r in comparisons:
        print(json.dumps({k: v for k, v in r.items() if k != 'per_scene'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
