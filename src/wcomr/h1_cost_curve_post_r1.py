"""Receipt-level curve acceptance and full-denominator time/quality summaries."""
import math
from statistics import mean
from .h1_cost_curve_batch_r1 import METHODS, matrix
from .source_phase_fixed_mask_r1 import CAL_MASK_A, CAL_MASK_C
from .h1_cost_curve_production_r1 import CURVE, diagnostic_warm


def audit_row(row, planned):
    if any(row.get(k) != v for k, v in planned.items()):
        raise ValueError('Foreign curve input/method/section/order')
    if row['status'] not in ('COMPLETE', 'VIDEO_REJECTED'):
        return
    if row['solver_steps'] != 36 or row['guided_pairs'] != 36:
        raise ValueError('Full36 update receipts required')
    diag = diagnostic_warm(planned)
    if (row['in_timing_guided_copies'] != (36 if diag else 0)
            or row['in_timing_hashes'] != 0 or row['research_checkpoints'] != 0
            or bool(row['audit']) != diag or row['core_seconds'] <= 0
            or not row['write_deferred_after_main_timer']):
        raise ValueError('Only four diagnostic warm paths may copy guided outputs')
    if diag and row.get('warm_guided_outputs') != 36:
        raise ValueError('All warm guided vectors must be saved outside main timer')
    method = row['method']; actions = row.get('actions')
    if method == 'NATIVE':
        if actions is not None:
            raise ValueError('Native has no cache-action trajectory')
    elif (not isinstance(actions, list) or len(actions) != 36
          or any(a not in ('DD', 'DC', 'CD', 'CC', 'PP') for a in actions)):
        raise ValueError('Complete actual two-CFG actions required')
    if method.startswith('H1_') and row['curve_lambda'] != dict(zip(METHODS[5:8], CURVE))[method]:
        raise ValueError('Curve lambda changed after registration')
    if method.startswith('FIXED_'):
        plan = CAL_MASK_A if method == 'FIXED_A' else CAL_MASK_C
        if (row['semantic_plan'] != list(plan) or row['input_adaptive_action_selection']
                or actions != ['DD' if a == 'D' else 'CC' for a in plan]):
            raise ValueError('Frozen full36 mask/readout changed')
    hist = row.get('source_history', [])
    if method.startswith(('H1_', 'FIXED_')) and len(hist) != 36:
        raise ValueError('New curve/source methods require all36 physical source records')
    if hist:
        if len(hist) != 36 or [h['action'] for h in hist] != actions:
            raise ValueError('All source actions required')
        for h in hist:
            if h['teacher_calls'] != 0 or h['P_updates_true_D_or_zero_risk_RA_anchor']:
                raise ValueError('Online teacher or false D anchor')
            if h['action'] != 'DD' and h['true_D_before'] != h['true_D_after']:
                raise ValueError('Approximation writes true D history')
            if h['action'] == 'PP':
                if (h['source_policy']['creation_floor_proxy_after'] <= 0
                        or any(s['kind'] != 'P' or s['RA_zero_risk_reset_allowed']
                               for s in h['working_sources'])):
                    raise ValueError('P must retain nonzero source error')


def endpoint_identity(a, b):
    if (a['final_latent_sha256'] != b['final_latent_sha256'] or a['actions'] != b['actions']
            or a['decoded_video']['RGB_sha256'] != b['decoded_video']['RGB_sha256']):
        raise ValueError('Expected same algorithm/mask endpoint identity failed')


def guided_identity(left, right):
    import torch
    if len(left) != 36 or len(right) != 36:
        raise ValueError('All36 guided outputs required for both warm arms')
    if any(x.shape != y.shape or not torch.equal(x, y) for x, y in zip(left, right)):
        raise ValueError('Real guided warm outputs differ despite same action mask')


def summaries(rows, scenes):
    ids = [r['id'] for r in rows]
    expected = matrix(scenes)
    if len(ids) != len(set(ids)) or ids != [r['id'] for r in expected]:
        raise ValueError('All60 slots, including missing/rejected, in original order required')
    valid = [r for r in rows if r['section'] == 'TIMED' and r.get('endpoint_audit') == 'PASS' and 'LPIPS' in r]
    lookup = {(r['scene'], r['method']): r for r in valid}
    methods = []
    for method in METHODS:
        values = []
        for scene in scenes:
            r = lookup.get((scene, method))
            if r is None:
                values.append(dict(scene=scene, status='MISSING_OR_REJECTED_NO_ZERO_IMPUTATION'))
                continue
            seconds, loss = r['core_seconds'], r['LPIPS']['mean_LPIPS']
            if not math.isfinite(seconds) or not math.isfinite(loss) or seconds <= 0 or loss < 0:
                raise ValueError('Finite actual time and scored fidelity required')
            speeds = {base: lookup[(scene, base)]['core_seconds'] / seconds
                      for base in ('NATIVE', 'WC', 'RA') if (scene, base) in lookup}
            values.append(dict(scene=scene, status='SCORED', main_seconds=seconds,
                               LPIPS=loss, speedup_baseline_over_candidate=speeds,
                               counts=r.get('counts'), actual_actions=r.get('actions')))
        done = [v for v in values if v['status'] == 'SCORED']
        complete = len(done) == 4
        methods.append(dict(method=method, scene_rows=values, denominator=4, scored_scenes=len(done),
            complete_four_scene_mean_seconds=mean(v['main_seconds'] for v in done) if complete else None,
            complete_four_scene_mean_LPIPS=mean(v['LPIPS'] for v in done) if complete else None))
    contrasts = []
    pairs = [(a, b) for a in METHODS if a != 'NATIVE'
             for b in ('NATIVE', 'WC', 'RA', 'A_NO_P', 'P_OFF') if a != b]
    pairs += [('H1_MID', 'FIXED_A'), ('FIXED_A', 'FIXED_PLAIN'),
              ('H1_LOW', 'H1_MID'), ('H1_HIGH', 'H1_MID')]
    for candidate, base in dict.fromkeys(pairs):
        values = []
        for scene in scenes:
            x, y = lookup.get((scene, candidate)), lookup.get((scene, base))
            if x is None or y is None:
                values.append(dict(scene=scene, status='MISSING_OR_REJECTED_NO_ZERO_IMPUTATION')); continue
            lx, ly = x['LPIPS']['mean_LPIPS'], y['LPIPS']['mean_LPIPS']
            values.append(dict(scene=scene, status='SCORED', candidate_seconds=x['core_seconds'],
                baseline_seconds=y['core_seconds'], candidate_LPIPS=lx, baseline_LPIPS=ly,
                seconds_saved=y['core_seconds'] - x['core_seconds'],
                speedup_baseline_over_candidate=y['core_seconds'] / x['core_seconds'],
                LPIPS_change_percent=100 * (lx / ly - 1) if ly > 0 else None,
                LPIPS_absolute_change=lx-ly))
        done = [v for v in values if v['status'] == 'SCORED']; complete = len(done) == 4
        contrasts.append(dict(candidate=candidate, baseline=base, denominator=4,
            scored_scenes=len(done), scene_rows=values,
            improved_scenes=sum(v['candidate_LPIPS'] < v['baseline_LPIPS'] for v in done),
            complete_mean_seconds_saved=mean(v['seconds_saved'] for v in done) if complete else None,
            complete_mean_LPIPS_absolute_change=mean(v['LPIPS_absolute_change'] for v in done) if complete else None))
    return dict(methods=methods, contrasts=contrasts, full_scope_slots=60, scientific_slots=40,
                no_scenario_winner_splicing=True, stable_speed_or_independent_confirmation=False)
