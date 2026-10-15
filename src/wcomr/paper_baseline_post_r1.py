"""Complete-denominator analysis, observed cost/fidelity and finite frontiers."""
import copy
import math
from statistics import mean

from .paper_baseline_grid_r1 import METHODS,matrix


def full_rows(runs,scenes):
    plan=matrix(scenes);expected={r['id']:r for r in plan}
    if len({r['id'] for r in runs})!=len(runs):raise ValueError('Duplicate N05 output row')
    if [r['id'] for r in runs]!=[r['id'] for r in plan[:len(runs)]]:
        raise ValueError('Observed N05 execution must retain the registered order prefix')
    for r in runs:
        if r['id'] not in expected or any(r.get(k)!=v for k,v in expected[r['id']].items()):
            raise ValueError('Foreign method/input or order identity')
    index={r['id']:r for r in runs};rows=[]
    for p in plan:
        r=copy.deepcopy(index.get(p['id'],{**p,'status':'NOT_REACHED'}))
        if r['status']=='RUNNING':
            r.update(original_runner_status='RUNNING',status='TECH_FAILED_TERMINAL_RUNNER_INCOMPLETE')
        rows.append(r)
    return rows


def summaries(rows,scenes):
    plan=matrix(scenes)
    if len(rows)!=66 or [r['id'] for r in rows]!=[r['id'] for r in plan]:
        raise ValueError('All66 positions in original registered order required')
    methods=[];valid={};timed={}
    for r in rows:
        if r['section']!='TIMED' or r['status']!='COMPLETE' or r.get('endpoint_audit')!='PASS':continue
        seconds=r['core_seconds']
        if not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<=0:
            raise ValueError('Finite positive observed model-resident cost required')
        timed[(r['scene'],r['method'])]=r
        if 'LPIPS' in r:
            lp=r['LPIPS'];dist=lp['frame_distances']
            if (lp['frames']!=93 or len(dist)!=93
                    or any(not math.isfinite(v) or v<0 for v in dist)
                    or abs(sum(dist)/93-lp['mean_LPIPS'])>1e-12):
                raise ValueError('Independent complete93-frame LPIPS mean differs')
            valid[(r['scene'],r['method'])]=r
    for method in METHODS:
        values=[]
        for scene in scenes:
            r=timed.get((scene,method));q=valid.get((scene,method))
            original=next(x for x in rows if x['section']=='TIMED' and x['scene']==scene and x['method']==method)
            values.append(dict(scene=scene,status=original['status'],endpoint_audit=original.get('endpoint_audit'),
                main_seconds=r['core_seconds'] if r else None,
                LPIPS=q['LPIPS']['mean_LPIPS'] if q else None,
                speedups={base:timed[(scene,base)]['core_seconds']/r['core_seconds']
                    for base in ('NATIVE35','WC_DEFAULT','RA_DEFAULT') if r and (scene,base) in timed},
                actual_actions=original.get('actions'),
                requested_steps=original.get('baseline_grid_point',{}).get('requested_steps')))
        times=[x['main_seconds'] for x in values if x['main_seconds'] is not None]
        losses=[x['LPIPS'] for x in values if x['LPIPS'] is not None]
        methods.append(dict(method=method,denominator=4,timed_scenes=len(times),scored_scenes=len(losses),
            complete_four_scene_mean_seconds=mean(times) if len(times)==4 else None,
            complete_four_scene_mean_LPIPS=mean(losses) if len(losses)==4 else None,scene_rows=values))
    contrasts=[]
    for candidate in ('A_NO_P','TABLE_PHASE_H1'):
        for baseline in METHODS[:9]:
            values=[]
            for scene in scenes:
                a=valid.get((scene,candidate));b=valid.get((scene,baseline))
                if a is None or b is None:
                    values.append(dict(scene=scene,status='MISSING_OR_REJECTED_NO_ZERO_IMPUTATION'));continue
                la,lb=a['LPIPS']['mean_LPIPS'],b['LPIPS']['mean_LPIPS']
                values.append(dict(scene=scene,status='SCORED',candidate_seconds=a['core_seconds'],baseline_seconds=b['core_seconds'],
                    speedup_baseline_over_candidate=b['core_seconds']/a['core_seconds'],
                    candidate_LPIPS=la,baseline_LPIPS=lb,LPIPS_absolute_change=la-lb,
                    LPIPS_change_percent=100*(la/lb-1) if lb>0 else None))
            done=[r for r in values if r['status']=='SCORED']
            contrasts.append(dict(candidate=candidate,baseline=baseline,denominator=4,paired_scenes=len(done),scene_rows=values,
                complete_mean_LPIPS_absolute_change=mean(r['LPIPS_absolute_change'] for r in done) if len(done)==4 else None,
                complete_mean_seconds_saved=mean(r['baseline_seconds']-r['candidate_seconds'] for r in done) if len(done)==4 else None))
    complete=[r for r in methods if r['timed_scenes']==r['scored_scenes']==4]
    frontier=[]
    for r in complete:
        cost,loss=r['complete_four_scene_mean_seconds'],r['complete_four_scene_mean_LPIPS']
        dominated_by=[x['method'] for x in complete if x is not r
            and x['complete_four_scene_mean_seconds']<=cost and x['complete_four_scene_mean_LPIPS']<=loss
            and (x['complete_four_scene_mean_seconds']<cost or x['complete_four_scene_mean_LPIPS']<loss)]
        frontier.append(dict(method=r['method'],observed_non_dominated=not dominated_by,dominated_by=dominated_by))
    return dict(methods=methods,contrasts=contrasts,observed_finite_grid_frontier=frontier,
        full_scope_slots=66,scientific_slots=44,no_scenario_winner_splicing=True,
        continuous_frontier_or_time_interpolation_claim=False,stable_repeated_speed_benchmark_claim=False,
        direct_corrected_neighbor_comparison_complete=False)
