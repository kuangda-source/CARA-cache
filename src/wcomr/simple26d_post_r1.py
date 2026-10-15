"""Full-denominator fidelity contrasts; concurrent timing has no speed claim."""
from statistics import mean
from .simple26d_r1 import METHODS,matrix

def full_rows(actual,scenes):
    expected=matrix(scenes);ids=[r['id'] for r in actual]
    if len(set(ids))!=len(ids) or any(i not in {p['id'] for p in expected} for i in ids):raise ValueError('Duplicate/foreign actual path')
    lookup={r['id']:r for r in actual}
    return [lookup.get(p['id'],{**p,'status':'NOT_REACHED_FULL_SCOPE_RETAINED'}) for p in expected]

def summaries(rows,scenes):
    if [r['id'] for r in rows]!=[p['id'] for p in matrix(scenes)]:raise ValueError('All36 original slots required')
    valid={(r['scene'],r['method']):r for r in rows if r['section']=='TIMED' and 'LPIPS' in r and r.get('endpoint_audit')=='PASS'}
    methods=[]
    for method in METHODS:
        ss=[]
        for scene in scenes:
            r=valid.get((scene,method))
            ss.append(dict(scene=scene,status='MISSING_OR_REJECTED_NO_IMPUTATION') if r is None else dict(scene=scene,status='SCORED',LPIPS=r['LPIPS']['mean_LPIPS'],diagnostic_main_seconds=r['core_seconds'],counts=r['counts']))
        scored=[s for s in ss if s['status']=='SCORED']
        methods.append(dict(method=method,denominator=4,scored_scenes=len(scored),scene_rows=ss,
            complete_four_scene_mean_LPIPS=mean(s['LPIPS'] for s in scored) if len(scored)==4 else None))
    contrasts=[]
    pairs=[('UNIFORM_A','FIXED_A'),('FRONT_DENSE_A','FIXED_A'),('UNIFORM_C','FIXED_PLAIN'),('FRONT_DENSE_C','FIXED_PLAIN'),
        ('FIXED_A','FIXED_PLAIN'),('UNIFORM_A','UNIFORM_C'),('FRONT_DENSE_A','FRONT_DENSE_C')]
    for a,b in pairs:
        ss=[]
        for scene in scenes:
            x,y=valid.get((scene,a)),valid.get((scene,b))
            if x is None or y is None:ss.append(dict(scene=scene,status='MISSING_OR_REJECTED_NO_IMPUTATION'));continue
            lx,ly=x['LPIPS']['mean_LPIPS'],y['LPIPS']['mean_LPIPS']
            ss.append(dict(scene=scene,status='SCORED',candidate_LPIPS=lx,baseline_LPIPS=ly,
                absolute_change=lx-ly,change_percent=100*(lx/ly-1) if ly>0 else None))
        done=[s for s in ss if s['status']=='SCORED']
        contrasts.append(dict(candidate=a,baseline=b,denominator=4,scored_scenes=len(done),improved_scenes=sum(s['absolute_change']<0 for s in done),
            complete_mean_absolute_change=mean(s['absolute_change'] for s in done) if len(done)==4 else None,scene_rows=ss))
    return dict(methods=methods,contrasts=contrasts,full_scope_slots=36,scientific_slots=24,
        timing_claim='CONCURRENT_DIAGNOSTIC_NOT_CLEAN_LATENCY',same_D_quota_does_not_mean_equal_A_or_total_cost=True,
        no_scenario_winner_splicing=True,independent_input_confirmation=False,net_acceleration_claim=False)
