"""Offline CAL66 frozen-contract screening; never dispatches or changes raw data."""
import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.policy_generator_r1.paired_budget_design import paired_budget

CONTRACT = 'plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md'
QUALITY_LIMITS = dict(MUSIQ_LONGER512=1., subject_consistency=.01, motion_smoothness=.01)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference_role(summaries, n):
    c, a = f'S{n}_C', f'S{n}_A_PHASE'
    return c if summaries[c]['LPIPS'] <= summaries[a]['LPIPS'] + 1e-12 else a


def gates(candidate, reference, native, differences):
    absolute = reference['LPIPS'] - candidate['LPIPS']
    relative = absolute / reference['LPIPS']
    quality = {name: {d: candidate['quality'][d] - baseline['quality'][d]
                      for d in QUALITY_LIMITS}
               for name, baseline in (('S_reference', reference), ('Native35', native))}
    checks = dict(budget_point=candidate['budget']['V'] <= 1,
                  absolute_gain=absolute >= .002, relative_gain=relative >= .05,
                  at_least_three_improved=sum(x < 0 for x in differences) >= 3,
                  worst_LPIPS_increase=max(differences) <= .01)
    for name, deltas in quality.items():
        for d, value in deltas.items():
            checks[f'{name}:{d}'] = value >= -QUALITY_LIMITS[d]
    return dict(absolute_LPIPS_gain=absolute, relative_LPIPS_gain=relative,
                per_prompt_LPIPS_delta=differences, quality_deltas=quality,
                checks=checks, passed=all(checks.values()),
                failed_checks=[k for k, v in checks.items() if not v])


def choose(summaries, screening):
    eligible = [r for r, v in screening.items() if v['passed']]
    if not eligible:
        return None
    best = min(summaries[r]['LPIPS'] for r in eligible)
    close = [r for r in eligible if summaries[r]['LPIPS'] - best <= .002]
    return min(close, key=lambda r: (summaries[r]['budget']['V'], summaries[r]['actions']['A'], r))


def analyze(capture, acceptance, settlement):
    # This imports the already accepted, enumerated SM86 identity adapter.
    from wc_two_card_cara_cal66_gpu_r1 import accept_terminal
    from wcomr.policy_price_terminal_r1 import record
    v, a, settled = [json.loads(Path(p).read_text()) for p in (capture, acceptance, settlement)]
    replay = accept_terminal(v)
    assert replay['full_protocol_accepted'] and all(a.get(k) == val for k, val in replay.items())
    assert a['capture_sha256'] == sha(capture)
    assert settled['original']['launch'] == v['launch']
    assert settled['original']['billing_sha256'] == v['files']['billing']['sha256']
    assert settled['original']['billing']['actual_GPUh'] == a['actual_GPUh']
    card, quality = record(v, 'card'), record(v, 'quality_progress')
    members = card['CAL_FIT_members']
    roles = card['formal_roles']
    scientific = a['scientific']
    clocks = {(r['role'], r['member'], r['repeat']): r['seconds']
              for r in scientific['clocks'] if r['section'] == 'QUALITY'}
    lp = {(role, r['member']): r['LPIPS'] for role, rows in scientific['quality'].items()
          for r in rows if r['repeat'] == 1}
    for m in members:
        lp['NATIVE35', m] = 0.  # Reference self-distance, not an extra score.
    qs = {}
    for row in quality['rows']:
        p, result = row['planned'], row['result']
        key = p['role'], p['case_id'], p['dimension']
        assert key not in qs and result['status'] == 'SCORED'
        assert math.isfinite(result['value'])
        qs[key] = result['value']
    assert len(qs) == 156 and len(clocks) == 52 and len(lp) == 52
    summaries = {}
    for role in roles:
        times = [clocks[role, m, 1] for m in members]
        losses = [lp[role, m] for m in members]
        policy = card['roles'][role].get('policy')
        actions = {k: policy['actions'].count(k) for k in ('D', 'C', 'A')} if policy else {
            'D': next(s['actual_updates'] for s in card['matrix'] if s['role'] == role), 'C': 0, 'A': 0}
        budget = paired_budget([dict(prompt=m, candidate=[clocks[role, m, 1]],
                                     native=[clocks['NATIVE35', m, 1]]) for m in members])
        summaries[role] = dict(seconds=statistics.mean(times), LPIPS=statistics.mean(losses),
                               actions=actions, budget=budget,
                               quality={d: statistics.mean(qs[role, m, d] for m in members)
                                        for d in QUALITY_LIMITS},
                               per_prompt=[dict(member=m, seconds=clocks[role, m, 1], LPIPS=lp[role, m],
                                                quality={d: qs[role, m, d] for d in QUALITY_LIMITS})
                                           for m in members])
    references = {str(n): reference_role(summaries, n) for n in (24, 25)}
    screening = {}
    for n in (24, 25):
        ref = references[str(n)]
        for suffix in ('C', 'A_PHASE_ALL', 'A_PHASE_AGE3'):
            role = f'SHARED{n}_{suffix}'
            screening[role] = dict(reference=ref, **gates(summaries[role], summaries[ref],
                summaries['NATIVE35'], [lp[role, m] - lp[ref, m] for m in members]))
    selected = choose(summaries, screening)
    native_comparisons = {}
    for role in screening:
        native = min(('NATIVE26', 'NATIVE28'), key=lambda n: (
            abs(summaries[n]['seconds'] / summaries[role]['seconds'] - 1), card['roles'][n]['requested_steps']))
        c, n = summaries[role], summaries[native]
        dominates = {r: summaries[r]['seconds'] <= c['seconds'] * 1.03
                        and summaries[r]['LPIPS'] <= c['LPIPS']
                        and all(summaries[r]['quality'][d] >= c['quality'][d] for d in QUALITY_LIMITS)
                     for r in ('NATIVE26', 'NATIVE28')}
        native_comparisons[role] = dict(nearest_time_role=native,
            absolute_relative_time_gap=abs(n['seconds'] / c['seconds'] - 1),
            near_time=abs(n['seconds'] / c['seconds'] - 1) <= .03,
            dominated_by_small_step_native=any(dominates.values()), dominance_by_role=dominates,
            native_minus_candidate_quality={d: n['quality'][d] - c['quality'][d] for d in QUALITY_LIMITS},
            native_LPIPS=n['LPIPS'], candidate_LPIPS=c['LPIPS'])
    branch = 'STOP_NO_ELIGIBLE_CANDIDATE'
    if selected:
        match = native_comparisons[selected]
        branch = ('STOP_NATIVE_DOMINATES' if match['dominated_by_small_step_native'] else
                  'REGISTER_MISSING_NATIVE_TIME_MATCH' if not match['near_time'] else
                  'FREEZE_ONE_CAL_CANDIDATE_PREPARE_NEW_DEV_NOT_AUTHORIZED')
    comparisons = []
    for n in (24, 25):
        pairs = [(f'SHARED{n}_C', f'S{n}_C'),
                 (f'S{n}_A_PHASE', f'S{n}_C'),
                 (f'SHARED{n}_A_PHASE_ALL', f'SHARED{n}_C'),
                 (f'SHARED{n}_A_PHASE_AGE3', f'SHARED{n}_A_PHASE_ALL'),
                 (f'SHARED{n}_A_PHASE_ALL', f'S{n}_A_PHASE')]
        for left, right in pairs:
            delta = [lp[left, m] - lp[right, m] for m in members]
            comparisons.append(dict(candidate=left, reference=right,
                LPIPS_delta=statistics.mean(delta), relative_LPIPS_change=statistics.mean(delta)/summaries[right]['LPIPS'],
                improved_prompts=sum(x < 0 for x in delta), worst_increase=max(delta),
                per_prompt_delta=delta, seconds_delta=summaries[left]['seconds']-summaries[right]['seconds']))
    # Repeats stay diagnostic: no selective averaging for the CAL ranking.
    repeat_diagnostics = []
    for row in scientific['clocks']:
        if row['section'] == 'TIMING_REPEAT':
            first = clocks[row['role'], row['member'], 1]
            repeat_diagnostics.append(dict(role=row['role'], member=row['member'],
                                           first_seconds=first, repeat_seconds=row['seconds'], delta=row['seconds']-first))
    frozen = None
    if selected:
        n = str(summaries[selected]['actions']['D'])
        aroles = [f'SHARED{n}_A_PHASE_AGE3', f'SHARED{n}_A_PHASE_ALL']
        best_a = aroles[0] if summaries[aroles[0]]['LPIPS'] <= summaries[aroles[1]]['LPIPS'] + 1e-12 else aroles[1]
        frozen = dict(role=selected, policy=card['roles'][selected]['policy'], S_reference=references[n],
                      small_step_native=native_comparisons[selected]['nearest_time_role'],
                      proposed_DEV_roles=['NATIVE35', native_comparisons[selected]['nearest_time_role'],
                          f'S{n}_C', f'S{n}_A_PHASE', f'SHARED{n}_C', best_a],
                      reason='Pre-registered CAL screening only; no held-out/deployment acceptance')
    return dict(status='CAL66_COMPLETE_ACCEPTED_FROZEN_RULE_ANALYSIS', created_unix=time.time(),
        evidence={k: dict(path=str(p), sha256=sha(p)) for k,p in (
            ('capture',capture),('acceptance',acceptance),('central_settlement',settlement),
            ('decision_contract',ROOT/CONTRACT),('analysis_source',Path(__file__)))},
        launch_id=v['launch']['launch_id'], source_revision=v['launch']['source_revision'],
        cohort=dict(CAL=members, seeds=[0], formal_roles=13, formal_paths=52, total_paths=66,
                    repeated_clocks_not_extra_samples=True, selection_clock='QUALITY_FIRST_ROUND_ONLY'),
        summaries=summaries, S_references=references, screening=screening,
        native_comparisons=native_comparisons, comparisons=comparisons,
        repeat_diagnostics=repeat_diagnostics, selected_role=selected, frozen_candidate=frozen,
        next_branch=branch, actual_GPUh=a['actual_GPUh'], historical_bridge=scientific['historical_bridge'],
        deployment_accepted=False, heldout_evidence=False, GPU_submissions=0,
        original_alpha_and_thresholds_unchanged=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('capture','acceptance','settlement','output'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): raise ValueError('Preserve previous analysis')
    result=analyze(a.capture,a.acceptance,a.settlement)
    with a.output.open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','selected_role','next_branch','actual_GPUh')}))


if __name__=='__main__': main()
