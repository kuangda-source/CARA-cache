#!/usr/bin/env python3
"""Offline CAL12 factorial and shared-plan analysis from accepted frame records.

No server connection, model import, score generation, or experiment dispatch.
All 93 frames are retained; the statistical unit remains one of four CAL prompts.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def mean(values):
    return statistics.fmean(values)


def formal(rows):
    return [r for r in rows if r['section'] == 'TIMED']


def effective_plan(row):
    p = [h['readout_action'] for h in row['A_history']]
    assert len(p) == len(row['actions']) == 36
    assert all(a in ('D', 'A', 'C') for a in p)
    assert all((a == 'D') == (raw == 'DD')
               for a, raw in zip(p, row['actions']))
    assert not any(h['C_or_P_observation_updates_D_anchor']
                   for h in row['A_history'])
    return p


def row_summary(row, batch, expected_reference):
    assert row['status'] == 'COMPLETE' and row['solver_steps'] == 36
    lp = row['LPIPS']
    frames = lp['frame_distances']
    assert lp['frames'] == row['decoded_video']['frames'] == len(frames) == 93
    assert len(lp['pts']) == 93
    assert all(math.isfinite(x) and x >= 0 for x in frames)
    assert math.isclose(mean(frames), lp['mean_LPIPS'], abs_tol=1e-14)
    assert lp['reference_sha256'] == expected_reference
    assert lp['candidate_sha256'] == row['video_artifact']['sha256']
    plan = effective_plan(row)
    return dict(scene=row['scene'], method=row['method'], source_batch=batch,
                original_row_id=row['id'], LPIPS=mean(frames),
                core_seconds=row['core_seconds'],
                guarded_seconds=row['guarded_pipeline_without_write_seconds'],
                actual_counts=dict(Counter(plan)), plan=plan,
                D_steps=[i + 1 for i, a in enumerate(plan) if a == 'D'],
                A_steps=[i + 1 for i, a in enumerate(plan) if a == 'A'],
                reference_video_sha256=expected_reference,
                video_sha256=row['video_artifact']['sha256'],
                final_latent_sha256=row['final_latent_sha256'],
                frame_distances=frames, frame_pts=lp['pts'],
                observer=row.get('observer'), timing_claim=row['timing_claim'])


def contrast(rows, scenes, candidate, baseline):
    result = []
    for scene in scenes:
        a, b = rows[scene, candidate], rows[scene, baseline]
        assert a['frame_pts'] == b['frame_pts']
        diffs = [x - y for x, y in zip(a['frame_distances'], b['frame_distances'])]
        result.append(dict(scene=scene, candidate_LPIPS=a['LPIPS'],
                           baseline_LPIPS=b['LPIPS'],
                           absolute_change=a['LPIPS'] - b['LPIPS'],
                           relative_change_percent=100 * (a['LPIPS'] / b['LPIPS'] - 1),
                           improved_frames=sum(x < 0 for x in diffs),
                           worsened_frames=sum(x > 0 for x in diffs),
                           equal_frames=sum(x == 0 for x in diffs),
                           candidate_core_seconds=a['core_seconds'],
                           baseline_core_seconds=b['core_seconds']))
    ca = mean(x['candidate_LPIPS'] for x in result)
    ba = mean(x['baseline_LPIPS'] for x in result)
    ct = mean(x['candidate_core_seconds'] for x in result)
    bt = mean(x['baseline_core_seconds'] for x in result)
    return dict(candidate=candidate, baseline=baseline, prompt_denominator=4,
                candidate_mean_LPIPS=ca, baseline_mean_LPIPS=ba,
                absolute_mean_change=ca-ba,
                relative_ratio_of_prompt_means_percent=100 * (ca/ba-1),
                improved_prompts=sum(x['absolute_change'] < 0 for x in result),
                worsened_prompts=sum(x['absolute_change'] > 0 for x in result),
                candidate_mean_core_seconds=ct, baseline_mean_core_seconds=bt,
                descriptive_core_seconds_change=ct-bt,
                descriptive_core_percent_change=100 * (ct/bt-1),
                clean_latency_or_action_price_claim=False, per_scene=result)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--capture', type=Path, required=True)
    ap.add_argument('--acceptance', type=Path, required=True)
    ap.add_argument('--window-capture', type=Path, required=True)
    ap.add_argument('--window-acceptance', type=Path, required=True)
    ap.add_argument('--simple-capture', type=Path, required=True)
    ap.add_argument('--simple-acceptance', type=Path, required=True)
    ap.add_argument('--bank-automation', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    assert not a.output.exists(), 'Preserve the original analysis receipt'
    c, accepted = read(a.capture), read(a.acceptance)
    w, wa = read(a.window_capture), read(a.window_acceptance)
    s, sa = read(a.simple_capture), read(a.simple_acceptance)
    assert accepted['full_protocol_accepted'] and accepted['registered_paths'] == 12
    assert accepted['formal_denominator'] == accepted['scored_nonNative_formal'] == 8
    assert accepted['capture_sha256'] == sha(a.capture)
    assert wa['full_protocol_accepted'] and wa['registered_paths'] == 24
    assert sha(a.window_capture) == wa['capture_sha256'] == c['upstream_sha256']
    assert c['upstream'] == w and c['upstream_acceptance'] == wa
    assert sa['status'] == 'SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED'
    assert sa['capture_sha256'] == sha(a.simple_capture)
    assert len(formal(c['final']['rows'])) == 8
    assert len(formal(w['final']['rows'])) == 16
    refs = {r['scene']: r['video_artifact']['sha256']
            for r in c['final']['Native_reference_bindings']}
    scenes = list(refs)
    assert len(scenes) == 4
    rows, originals = {}, {}
    for batch, values in [('Window24', formal(w['final']['rows'])),
                          ('CAL12', formal(c['final']['rows']))]:
        for r in values:
            key = r['scene'], r['method']
            assert key not in rows
            originals[key] = r
            rows[key] = row_summary(r, batch, refs[r['scene']])
    for old in c['final']['old_CAL_bindings']:
        method = 'S25-A1' if old['method'] == 'S25-A' else old['method']
        actual = originals[old['scene'], method]
        assert old['video_artifact']['sha256'] == actual['video_artifact']['sha256']
        assert old['final_latent_sha256'] == actual['final_latent_sha256']
        assert old['LPIPS']['frame_distances'] == actual['LPIPS']['frame_distances']
    for r in formal(s['final']['rows']):
        if r['method'] == 'FRONT_DENSE_C':
            old = originals[r['scene'], 'S26-C']
            assert r['video_artifact']['sha256'] == old['video_artifact']['sha256']
            assert r['LPIPS']['frame_distances'] == old['LPIPS']['frame_distances']
        elif r['method'] in ('UNIFORM_C', 'FRONT_DENSE_A'):
            rows[r['scene'], r['method']] = row_summary(r, 'N06_R2', refs[r['scene']])
    labels = {'G00': 'S25-C', 'G10': 'S25-A1', 'G01': 'G01_LATE_A', 'G11': 'S25-A3'}
    interactions = []
    for scene in scenes:
        x = {k: rows[scene, m] for k, m in labels.items()}
        assert len({tuple(r['D_steps']) for r in x.values()}) == 1
        for k, steps in [('G00', []), ('G10', [21]), ('G01', [22, 23]), ('G11', [21, 22, 23])]:
            assert x[k]['A_steps'] == steps and len(x[k]['D_steps']) == 25
        b, v = rows[scene, 'S26-C'], rows[scene, 'VARIATION26_C']
        assert len(b['D_steps']) == len(v['D_steps']) == 26
        assert b['A_steps'] == v['A_steps'] == []
        assert set(b['D_steps']) - set(v['D_steps']) == {33}
        assert set(v['D_steps']) - set(b['D_steps']) == {22}
        losses = {k: v['LPIPS'] for k, v in x.items()}
        interaction = losses['G11']-losses['G10']-losses['G01']+losses['G00']
        early = losses['G00']-losses['G10']
        early_after_late = losses['G01']-losses['G11']
        late = losses['G00']-losses['G01']
        late_after_early = losses['G10']-losses['G11']
        assert math.isclose(interaction, early-early_after_late, abs_tol=1e-14)
        assert math.isclose(interaction, late-late_after_early, abs_tol=1e-14)
        interactions.append(dict(scene=scene, **losses, interaction=interaction,
            early_A21_benefit_without_late=early,
            early_A21_benefit_with_late=early_after_late,
            late_A22_23_benefit_without_early=late,
            late_A22_23_benefit_with_early=late_after_early))
    pairs = [('S25-A1', 'S25-C'), ('G01_LATE_A', 'S25-C'),
             ('S25-A3', 'S25-A1'), ('S25-A3', 'G01_LATE_A'),
             ('S25-A3', 'S25-C'), ('G01_LATE_A', 'S25-A1'),
             ('G01_LATE_A', 'S26-C'), ('S25-A3', 'S26-C'),
             ('VARIATION26_C', 'S26-C'), ('VARIATION26_C', 'UNIFORM_C'),
             ('VARIATION26_C', 'FRONT_DENSE_A')]
    contrasts = [contrast(rows, scenes, *p) for p in pairs]
    methods = list(dict.fromkeys(m for _, m in rows))
    means = {m: dict(LPIPS=mean(rows[sc, m]['LPIPS'] for sc in scenes),
                    core_seconds=mean(rows[sc, m]['core_seconds'] for sc in scenes),
                    guarded_seconds=mean(rows[sc, m]['guarded_seconds'] for sc in scenes),
                    actual_counts=rows[scenes[0], m]['actual_counts']) for m in methods}
    files = [a.capture, a.acceptance, a.window_capture, a.window_acceptance,
             a.simple_capture, a.simple_acceptance, a.bank_automation, Path(__file__)]
    out = dict(status='ACCEPTED_CAL12_OFFLINE_FACTORIAL_AND_PLAN_ANALYSIS_COMPLETE',
        scene_order=scenes, prompt_denominator=4, seeds_per_prompt=1,
        prompt_status='PREVIOUSLY_EXPOSED_CAL_NOT_INDEPENDENT_FINAL_TEST',
        source_bindings={str(p): dict(sha256=sha(p), bytes=p.stat().st_size) for p in files},
        verified_controls=dict(CAL12_full12=True, Window24_full24=True,
            N06_full36=True, old_N12_endpoints_identical=True,
            N06_front_C_equals_S26_C=True, all_same_Native_references=True,
            all_actual_masks_and_A_steps_verified=True),
        per_prompt_means=means, per_scene_methods=list(rows.values()),
        contrasts=contrasts,
        A_factorial=dict(labels=labels, per_scene=interactions,
            mean_interaction=mean(r['interaction'] for r in interactions),
            positive_interaction_prompts=sum(r['interaction'] > 0 for r in interactions),
            lower_loss_interpretation='POSITIVE_INTERACTION_MEANS_OVERLAPPING_BENEFIT_NOT_SUPERADDITIVE_SYNERGY',
            early_has_one_A_late_group_has_two_A=True,
            equal_number_single_A_location_effect_identified=False),
        shared_plan=dict(removed_D=33, added_D=22, both_D_count=26,
            both_A_count=0, both_C_count=10, origin='FROZEN_GAIN_SQUARED_WEIGHTED_NATIVE_VARIATION',
            exact_curvature_or_optimality_proven=False,
            gain_weight_ablation_completed=False,
            shared_plan_plus_continuous_A_combination_tested=False),
        research_boundaries=dict(clean_speed_or_equal_wall_cost_claim=False,
            online_H1_independent_advantage_proven=False,
            causal_factorial_prompt_unit_count=4, frames_are_independent_samples=False,
            joint_component_additivity_proven=False,
            BANK24_validates_single_step_gate_not_A3_or_VARIATION26_transfer=True),
        all_comparisons_and_four_prompts_retained=True, BANK24_schedule_modified=False,
        new_GPU_submissions=0, new_quality_model_scores=0, SSH_calls=0)
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(status=out['status'], means=means,
        contrasts=[{k: r[k] for k in ('candidate','baseline','relative_ratio_of_prompt_means_percent','improved_prompts')}
                   for r in contrasts], mean_interaction=out['A_factorial']['mean_interaction']), ensure_ascii=False))


if __name__ == '__main__':
    main()
