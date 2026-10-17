"""Frozen complete one-D-replacement experiment; original numerical execution reused."""
import collections
import gc
import hashlib
import json
from pathlib import Path
import weakref

from . import clean_speed20_r1 as clean
from . import simple26d_memory_r2 as base
from .simple26d_r1 import MODE_REF, STRATEGY, sha, write
from .source_phase_fixed_mask_r1 import execute_fixed, mask_fingerprint

CONFIG='configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json'
RUN='wc-drop1-cal4-three-arm-full18-r1'
CARD='WC-DROP1-CAL4-THREEARM-FULL18-R1-20261017-A'
METHODS=('S26-C','S25-C','S25-A')
COUNTS=dict(requests=4,methods=3,scientific_paths=12,full_warmup_paths=6,total_paths=18,
    ordinary_pairs=648,ordinary_CFG_calls=1296,loads=1,teacher_pairs=0,score_videos=12)
CPU_STATUS='DROP1_FULL56_TWO_FLOW_NUMERICAL_CPU_PASS_NOT_GPU'
PRODUCTION_CPU_STATUS='DROP1_FULL18_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
TIMING='SINGLE_PASS_DEVELOPMENT_CORE_TIME_NOT_REPEATED_CLEAN_SPEED'


def plans():
    front=set(range(1,22))|{24,27,30,33,36}
    original=tuple('D' if n in front else 'C' for n in range(1,37))
    c=list(original);c[20]='C'
    a=c.copy();a[20]='A'
    return dict(zip(METHODS,(original,tuple(c),tuple(a))))


def matrix(scenes):
    if len(scenes)!=4 or len(set(scenes))!=4:
        raise ValueError('All original four CAL scenes required')
    rows=[]
    for repeat in (1,2):
        for method in METHODS if repeat==1 else METHODS[::-1]:
            rows.append(dict(id=f'warm_{repeat}_{method}',scene=scenes[0],method=method,section='WARMUP',round=repeat))
    for i,scene in enumerate(scenes):
        for method in METHODS if i%2==0 else METHODS[::-1]:
            rows.append(dict(id=f'timed_{i}_{method}',scene=scene,method=method,section='TIMED',round=1))
    return rows


def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['methods']!=list(METHODS)
        or c['scope_counts']!=COUNTS or c['plans']!={k:list(v) for k,v in plans().items()}
        or c['strategy']!=STRATEGY or c['A_method']!='BETA1_ONE_PHASE'
        or c['memory_policy']!='BOUNDARY_GC_ONLY_R2'
        or c['cumulative_cap_GPUh']!=226 or c['autonomy_exclusive_upper_GPUh']!=12
        or c['timing_claim']!=TIMING or c['deleted_D_update']!=21
        or not 0<c['forecast_complete_GPUh']<=c['billed_limit_GPUh']<12
        or c['warmup_repeats']!=2 or len(c['requests'])!=4
        or any(c[k] for k in ('training','online_teachers','P_enabled','F_B_enabled','endpoint_tuning','new_native_generation'))
        or any(q['seed']!=0 or q['num_steps']!=35 or q['num_output_frames']!=93
            or q['resolution']!='432,768' or q['guidance']!=7 for q in c['requests'])):
        raise ValueError('Frozen whole18 scope, legal plans, original readout or budget changed')
    for method,plan in plans().items():
        mask_fingerprint(plan)
        expected=26 if method=='S26-C' else 25
        if plan.count('D')!=expected or plan.count('A')!=(method=='S25-A'):
            raise ValueError('Exact paid D/A quotas required')
        last=0
        for n,a in enumerate(plan,1):
            if a=='D':last=n
            elif not 1<=n-last<=6:raise ValueError('Original age support required')


def execute(inference,sample,method,*,table_parameters,previous_parameters,**kw):
    if method not in METHODS or sample.seed!=0:
        raise ValueError('Frozen original CAL method/seed required')
    before=base.collect_boundary();references=[];old=clean.install
    def watched(*a,**k):
        result=old(*a,**k)
        if result[1] is not None:references.append(weakref.ref(result[1]))
        return result
    try:
        with clean.patched(clean,'install',watched):
            result=execute_fixed(inference,sample,replay_plan=plans()[method],
                table_parameters=table_parameters['SOURCE_PHASE'],previous_parameters=previous_parameters,**kw)
    finally:
        after=base.collect_boundary()
    alive=sum(ref() is not None for ref in references)
    if alive:raise ValueError('Completed request owner is still reachable')
    result.update(bridge_method=result['method'],method=method,timing_claim=TIMING,
        request_memory_lifecycle=dict(version='BOUNDARY_GC_ONLY_R2',before=before,after=after,
            observed_owners=len(references),owners_alive_after=alive,
            within_request_algorithm_or_guardrails_changed=False,cleanup_excluded_from_core_seconds=True))
    return result


def audit_row(row,planned):
    if any(row.get(k)!=v for k,v in planned.items()):raise ValueError('Foreign path or order')
    if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):return
    plan=plans()[row['method']];audit=planned['section']=='WARMUP'
    if (row['solver_steps']!=36 or row['guided_pairs']!=36
        or row['semantic_plan']!=list(plan) or row['mask_sha256']!=mask_fingerprint(plan)
        or row['actions']!=['DD' if a=='D' else 'CC' for a in plan]
        or row['online_teacher_calls'] or row['in_timing_hashes'] or row['research_checkpoints']
        or row['in_timing_guided_copies']!=(36 if audit else 0) or bool(row['audit'])!=audit
        or not row['write_deferred_after_main_timer'] or row['core_seconds']<=0
        or row['input_adaptive_action_selection'] or len(row['source_history'])!=36):
        raise ValueError('Full36 physical execution, readout, trace or timing differs')
    for step,(a,h) in enumerate(zip(plan,row['source_history']),1):
        readout=h['A_readout']
        if (h['teacher_calls'] or readout['teacher_calls'] or readout['extra_deep_blocks']
            or h['P_updates_true_D_or_zero_risk_RA_anchor']
            or readout['readout_action']!=a):
            raise ValueError('Readout, teacher or source identity changed')
        if a!='D' and h['true_D_before']!=h['true_D_after']:
            raise ValueError('C/A cannot write trusted D history')
        if a=='C' and (readout['shared_alpha'] or readout['extra_heads']):
            raise ValueError('Plain C paid correction')
        if a=='A' and (step!=21 or readout['shared_alpha']!=1):
            raise ValueError('Only frozen alpha1 correction at actual update21')


def validate(project,stage):
    stage=Path(stage)
    old_c,reg,old,inputs,tables,previous=base.validate(project,stage)
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    proof=json.loads((stage/'drop1-sampling-CPU-result.json').read_text())
    if (proof['status']!=CPU_STATUS or proof['actual_CPU_paths']!=56
        or proof['new_complete_paths']!=48 or proof['old_control_paths']!=8
        or proof['GPU_submissions'] or proof['CUDA_initialized']
        or proof['payload_sha256']!=reg['payload_sha256']
        or len(proof['checks'])!=2
        or not all(x['complete_CPU_paths']==28 and x['all36_clean_outputs_actions_video_equal'] for x in proof['checks'])):
        raise ValueError('Complete current56 numerical CPU and unchanged source required')
    if c['requests']!=old_c['requests']:
        raise ValueError('Original four inputs changed')
    calibration=inputs[0]
    for method,plan in plans().items():
        anchor=None
        for step,action in enumerate(plan,1):
            if action=='D':anchor=step
            elif (anchor,step) not in calibration.rho_at or step not in calibration.gains:
                raise ValueError('Original real calibration does not support '+str((method,anchor,step)))
    ref=c['front26_reference']
    if sha(stage/ref['ref'])!=ref['sha256']:raise ValueError('Original front26 reference changed')
    controls=json.loads((stage/ref['ref']).read_text())
    if len(controls['rows'])!=4 or {r['scene'] for r in controls['rows']}!={r['name'] for r in c['requests']}:
        raise ValueError('All four original S26 controls required')
    for row in controls['rows']:
        for key in ('final_artifact','video_artifact'):
            asset=row[key];p=Path(asset['path'])
            if sha(p)!=asset['sha256'] or p.stat().st_size!=asset['bytes']:
                raise ValueError('Original accepted front26 endpoint changed')
    return c,reg,old,inputs,tables,previous


def full_rows(actual,scenes):
    expected=matrix(scenes);lookup={r['id']:r for r in actual}
    if len(lookup)!=len(actual) or any(k not in {p['id'] for p in expected} for k in lookup):
        raise ValueError('Duplicate or foreign path')
    return [lookup.get(p['id'],{**p,'status':'NOT_REACHED_FULL_SCOPE_RETAINED'}) for p in expected]


def summaries(rows,scenes):
    if [r['id'] for r in rows]!=[p['id'] for p in matrix(scenes)]:
        raise ValueError('All18 positions required')
    valid={(r['scene'],r['method']):r for r in rows if r['section']=='TIMED'
        and r.get('endpoint_audit')=='PASS' and 'LPIPS' in r}
    from statistics import mean
    methods=[]
    for method in METHODS:
        rr=[dict(scene=s,status='SCORED',LPIPS=valid[(s,method)]['LPIPS']['mean_LPIPS'],
            main_seconds=valid[(s,method)]['core_seconds'],counts=valid[(s,method)]['counts'])
            if (s,method) in valid else dict(scene=s,status='MISSING_OR_REJECTED_RETAINED') for s in scenes]
        done=[r for r in rr if r['status']=='SCORED']
        methods.append(dict(method=method,denominator=4,scored_scenes=len(done),scene_rows=rr,
            complete_four_scene_mean_LPIPS=mean(r['LPIPS'] for r in done) if len(done)==4 else None))
    contrasts=[]
    for candidate,baseline in [('S25-A','S25-C'),('S25-A','S26-C'),('S25-C','S26-C')]:
        pairs=[]
        for scene in scenes:
            a,b=valid.get((scene,candidate)),valid.get((scene,baseline))
            if a is None or b is None:
                pairs.append(dict(scene=scene,status='MISSING_OR_REJECTED_RETAINED'));continue
            la,lb=a['LPIPS']['mean_LPIPS'],b['LPIPS']['mean_LPIPS']
            pairs.append(dict(scene=scene,status='SCORED',candidate_LPIPS=la,baseline_LPIPS=lb,
                absolute_change=la-lb,change_percent=100*(la/lb-1) if lb else None,
                candidate_seconds=a['core_seconds'],baseline_seconds=b['core_seconds'],
                speedup_baseline_over_candidate=b['core_seconds']/a['core_seconds'],
                actual_candidate_counts=a['counts'],actual_baseline_counts=b['counts']))
        contrasts.append(dict(candidate=candidate,baseline=baseline,denominator=4,scene_rows=pairs,
            scored_scenes=sum(p['status']=='SCORED' for p in pairs)))
    return dict(methods=methods,contrasts=contrasts,full_scope_slots=18,scientific_slots=12,
        timing_claim=TIMING,independent_input_confirmation=False,net_acceleration_claim=False,
        no_scenario_winner_splicing=True,same_D_quota_does_not_mean_equal_A_or_total_cost=True)

