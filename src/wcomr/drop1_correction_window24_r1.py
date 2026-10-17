"""Four-arm correction-window adapter; original readout and sampling unchanged.

This module alone is not a production CPU proof or GPU authorization. The
registered complete88 numerical paths and real production entry remain required.
"""
import math
from statistics import mean
import weakref

from . import drop1_full18_r1 as original
from .source_phase_fixed_mask_r1 import execute_fixed, mask_fingerprint

CARD = 'WC-DROP1-WINDOW-CAL4-FOURARM-FULL24-R1-20261018-A'
RUN = 'wc-drop1-correction-window-cal4-full24-r1'
METHODS = ('S26-C', 'S25-C', 'S25-A1', 'S25-A3')
COUNTS = dict(requests=4, methods=4, formal_paths=16, full_warmup_paths=8,
              total_paths=24, ordinary_pairs=864, ordinary_CFG_calls=1728,
              loads=1, new_teacher_pairs=0)
CPU_COUNTS = dict(new_two_flow_audit_lean_paths=64,
                  original_three_arm_audit_control_paths=24,
                  total_paths=88, actual_updates_per_path=36)
OLD_METHODS = {'S26-C': 'S26-C', 'S25-C': 'S25-C', 'S25-A1': 'S25-A'}
TIMING = original.TIMING
CPU_STATUS = 'CORRECTION_WINDOW_COMPLETE88_TWO_FLOW_NUMERICAL_CPU_PASS_NOT_GPU'
CONTRASTS = (('S25-A3', 'S25-A1'), ('S25-A3', 'S25-C'), ('S25-A3', 'S26-C'),
             ('S25-C', 'S26-C'), ('S25-A1', 'S25-C'), ('S25-A1', 'S26-C'))


def plans():
    old = original.plans()
    values = {k: old[v] for k, v in OLD_METHODS.items()}
    window = list(values['S25-A1'])
    assert window[20:24] == ['A', 'C', 'C', 'D']
    window[21:23] = ['A', 'A']
    values['S25-A3'] = tuple(window)
    return values


def validate_static_manifest(value, original_config):
    """Only the registered scope/masks/inputs, explicitly not production-ready."""
    expected = dict(card=CARD, namespace='DROP1_WINDOW24', methods=list(METHODS),
        plans={k: list(v) for k, v in plans().items()}, scope_counts=COUNTS,
        CPU_scope=CPU_COUNTS, old_equivalent_methods=OLD_METHODS,
        A_rule=dict(beta=1, shared_alpha=1, trusted_D_write=False),
        only_A1_to_A3_changed_actual_updates=[22, 23])
    if (any(value.get(k) != v for k, v in expected.items())
            or value.get('requests') != original_config['requests']
            or len(value['requests']) != 4
            or value.get('actual_CPU_accepted') is not False
            or value.get('forecast_complete_GPUh') is not None
            or value.get('billed_limit_GPUh') is not None
            or value.get('quality_results') is not None
            or value.get('speed_results') is not None
            or value.get('new_GPU_submissions') != 0):
        raise ValueError('Keep the complete registered24/88 scope; static scope is not production acceptance')
    for method, plan in plans().items():
        mask_fingerprint(plan)
        if plan.count('D') != (26 if method == 'S26-C' else 25):
            raise ValueError('Frozen dense quota changed')
        if plan.count('A') != {'S26-C': 0, 'S25-C': 0, 'S25-A1': 1, 'S25-A3': 3}[method]:
            raise ValueError('Frozen correction quota changed')


def matrix(scenes):
    if len(scenes) != 4 or len(set(scenes)) != 4 or any(not isinstance(s, str) or not s for s in scenes):
        raise ValueError('All four distinct original CAL inputs required')
    rows = []
    for repeat in (1, 2):
        for method in METHODS if repeat == 1 else METHODS[::-1]:
            rows.append(dict(id=f'warm_{repeat}_{method}', scene=scenes[0], method=method,
                             section='WARMUP', round=repeat))
    for i, scene in enumerate(scenes):
        for method in METHODS if i % 2 == 0 else METHODS[::-1]:
            rows.append(dict(id=f'timed_{i}_{method}', scene=scene, method=method, section='TIMED', round=1))
    return rows


def execute(inference, sample, method, *, table_parameters, previous_parameters, **kw):
    if method not in METHODS or sample.seed != 0:
        raise ValueError('Original CAL seed0 and registered correction-window method required')
    before = original.base.collect_boundary()
    references, install = [], original.clean.install

    def watched(*args, **kwargs):
        result = install(*args, **kwargs)
        if result[1] is not None:
            references.append(weakref.ref(result[1]))
        return result

    try:
        with original.clean.patched(original.clean, 'install', watched):
            result = execute_fixed(inference, sample, replay_plan=plans()[method],
                table_parameters=table_parameters['SOURCE_PHASE'],
                previous_parameters=previous_parameters, **kw)
    finally:
        after = original.base.collect_boundary()
    alive = sum(ref() is not None for ref in references)
    if alive:
        raise ValueError('Completed correction-window request owner remains reachable')
    result.update(bridge_method=result['method'], method=method, timing_claim=TIMING,
        request_memory_lifecycle=dict(version='BOUNDARY_GC_ONLY_R2', before=before, after=after,
            observed_owners=len(references), owners_alive_after=alive,
            within_request_algorithm_or_guardrails_changed=False, cleanup_excluded_from_core_seconds=True))
    return result


def audit_row(row, planned):
    if any(row.get(k) != v for k, v in planned.items()):
        raise ValueError('Foreign correction-window path metadata')
    if row['status'] == 'TEXT_REJECTED':
        return
    if row['status'] not in ('COMPLETE', 'VIDEO_REJECTED'):
        raise ValueError('Unknown or incomplete request is not an audited complete execution')
    plan = plans()[row['method']]
    audit = planned['section'] == 'WARMUP'
    if (row['solver_steps'] != 36 or row['guided_pairs'] != 36
            or row['semantic_plan'] != list(plan) or row['mask_sha256'] != mask_fingerprint(plan)
            or row['actions'] != ['DD' if a == 'D' else 'CC' for a in plan]
            or row['online_teacher_calls'] or row['in_timing_hashes'] or row['research_checkpoints']
            or row['in_timing_guided_copies'] != (36 if audit else 0) or bool(row['audit']) != audit
            or not row['write_deferred_after_main_timer'] or not math.isfinite(row['core_seconds'])
            or row['core_seconds'] <= 0 or row['input_adaptive_action_selection']
            or len(row['source_history']) != 36):
        raise ValueError('Full36 execution, original timing boundary or frozen plan changed')
    for a, history in zip(plan, row['source_history']):
        readout = history['A_readout']
        if (history['teacher_calls'] or readout['teacher_calls'] or readout['extra_deep_blocks']
                or history['P_updates_true_D_or_zero_risk_RA_anchor'] or readout['readout_action'] != a):
            raise ValueError('Actual readout, teacher or dense-source semantics changed')
        if a != 'D' and history['true_D_before'] != history['true_D_after']:
            raise ValueError('C/A cannot update trusted D history')
        if a == 'C' and (readout['shared_alpha'] or readout['extra_heads']):
            raise ValueError('Plain C executed an unregistered correction')
        if a == 'A' and readout['shared_alpha'] != 1:
            raise ValueError('Every registered A keeps shared alpha1')


def full_rows(actual, scenes):
    expected = matrix(scenes)
    planned = {r['id']: r for r in expected}
    lookup = {}
    for row in actual:
        if (row['id'] in lookup or row['id'] not in planned
                or any(row.get(k) != v for k, v in planned[row['id']].items())):
            raise ValueError('Duplicate, foreign or transplanted correction-window path')
        lookup[row['id']] = row
    return [lookup.get(p['id'], {**p, 'status': 'NOT_REACHED_FULL_SCOPE_RETAINED'}) for p in expected]


def summaries(rows, scenes):
    if rows != full_rows(rows, scenes) or len(rows) != 24:
        raise ValueError('All original24 positions in order required')
    valid = {}
    references = {}
    for row in rows:
        if row['section'] != 'TIMED' or row.get('status') != 'COMPLETE' or row.get('endpoint_audit') != 'PASS' or row.get('LPIPS') is None:
            continue
        score = row['LPIPS']
        frames = score['frame_distances']
        ref = score['reference_sha256']
        expected = plans()[row['method']]
        counts = dict(DD=expected.count('D'), PP=0, C_plain=expected.count('C'),
                      A=expected.count('A'), C_or_A_after_P=0)
        if (score['frames'] != 93 or len(frames) != 93 or len(score['pts']) != 93
                or not isinstance(ref, str) or len(ref) != 64 or any(c not in '0123456789abcdef' for c in ref)
                or row['counts'] != counts
                or any(not math.isfinite(x) or x < 0 for x in frames)
                or not math.isclose(mean(frames), score['mean_LPIPS'], rel_tol=0, abs_tol=1e-12)
                or not math.isfinite(row['core_seconds']) or row['core_seconds'] <= 0):
            raise ValueError('Full93 finite original scores and main timing required')
        identity = (score['reference_sha256'], score['pts'])
        if row['scene'] in references and references[row['scene']] != identity:
            raise ValueError('A scene cannot compare different Native references or PTS')
        references[row['scene']] = identity
        valid[(row['scene'], row['method'])] = row
    methods = []
    for method in METHODS:
        per_scene = [dict(scene=s, status='SCORED', LPIPS=valid[(s, method)]['LPIPS']['mean_LPIPS'],
            main_seconds=valid[(s, method)]['core_seconds'], counts=valid[(s, method)]['counts'])
            if (s, method) in valid else dict(scene=s, status='MISSING_OR_REJECTED_RETAINED') for s in scenes]
        scored = [r for r in per_scene if r['status'] == 'SCORED']
        methods.append(dict(method=method, denominator=4, scored_scenes=len(scored), scene_rows=per_scene,
            complete_four_scene_mean_LPIPS=mean(r['LPIPS'] for r in scored) if len(scored) == 4 else None))
    contrasts = []
    for candidate, baseline in CONTRASTS:
        pairs = []
        for scene in scenes:
            a, b = valid.get((scene, candidate)), valid.get((scene, baseline))
            if a is None or b is None:
                pairs.append(dict(scene=scene, status='MISSING_OR_REJECTED_RETAINED'))
                continue
            la, lb = a['LPIPS']['mean_LPIPS'], b['LPIPS']['mean_LPIPS']
            pairs.append(dict(scene=scene, status='SCORED', candidate_LPIPS=la, baseline_LPIPS=lb,
                absolute_change=la-lb, change_percent=100*(la/lb-1) if lb else None,
                candidate_seconds=a['core_seconds'], baseline_seconds=b['core_seconds'],
                speedup_baseline_over_candidate=b['core_seconds']/a['core_seconds'],
                actual_candidate_counts=a['counts'], actual_baseline_counts=b['counts']))
        contrasts.append(dict(candidate=candidate, baseline=baseline, denominator=4, scene_rows=pairs,
                              scored_scenes=sum(p['status'] == 'SCORED' for p in pairs)))
    return dict(methods=methods, contrasts=contrasts, full_scope_slots=24, scientific_slots=16,
        timing_claim=TIMING, independent_input_confirmation=False, net_acceleration_claim=False,
        no_scenario_winner_splicing=True, same_D_quota_does_not_mean_equal_A_or_total_cost=True)
