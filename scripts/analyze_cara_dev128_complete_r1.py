"""Frozen DEV128 decision on fully accepted originals only; no selection or GPU."""
import argparse
import hashlib
import json
import math
import random
import statistics as st
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.paired_budget_design import paired_budget
from wcomr.policy_generator_r1.dev128_terminal import accept
from wcomr.policy_price_terminal_r1 import record
LIMITS={'MUSIQ_LONGER512':1.,'subject_consistency':.01,'motion_smoothness':.01}
CONTRACT='plans/cara_policy_generator_20261020/SHARED25_DEV128_DUAL_HOST_PREPARATION_R1_20261026.md'
CAL_CONTRACT='plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def interval(values):
    assert len(values)==16 and all(math.isfinite(x) for x in values)
    rng=random.Random(20261025)
    draws=sorted(st.mean(values[rng.randrange(16)] for _ in values) for _ in range(20000))
    return dict(mean=st.mean(values),lower95=draws[math.floor(.05*19999)],
                upper95=draws[math.ceil(.95*19999)],prompts=16,resamples=20000,
                seed=20261025,lower_quantile='lower',upper_quantile='higher')

def decision(points,uncertainty):
    if not all(points.values()):return 'STOP_OR_NARROW_FIXED_CONFIGURATION'
    if not all(uncertainty.values()):return 'INCONCLUSIVE_ONE_PREREGISTERED_EXTENSION_REQUIRES_AUTHORIZATION'
    return 'CONTINUE_REGISTER_INDEPENDENT_CONFIRMATION_NO_AUTO_GPU'

def analyze(capture,accepted,settlement):
    v,a,s=[json.loads(Path(p).read_text()) for p in (capture,accepted,settlement)]
    v['central_settlement']=s
    replay=accept(v)
    assert replay['full_protocol_accepted'] and all(a.get(k)==val for k,val in replay.items())
    assert a['capture_sha256']==sha(capture) and a['central_settlement_sha256']==sha(settlement)
    card=record(v,'card');members=card['DEV_members'];roles=list(card['roles'])
    assert len(members)==16 and card['selection']==dict(role='SHARED25_C',S_reference='S25_A_PHASE',native='NATIVE26')
    clocks={}
    for r in replay['scientific']['clocks']:
        if r['section'] in ('QUALITY','TIMING_REPEAT'):
            key=(r['role'],r['member'],r['repeat']);assert key not in clocks;clocks[key]=r['seconds']
    assert len(clocks)==120
    lp={(role,r['member']):r['LPIPS'] for role,rows in replay['scientific']['quality'].items() for r in rows if r['repeat']==1}
    assert len(lp)==80
    for m in members:lp['NATIVE35',m]=0.
    qs={}
    for row in record(v,'quality_progress')['rows']:
        p,r=row['planned'],row['result'];key=(p['role'],p['case_id'],p['dimension'])
        assert key not in qs and r['status']=='SCORED' and math.isfinite(r['value']);qs[key]=r['value']
    assert len(qs)==288
    summaries={}
    for role in roles:
        time_rows=[]
        for i,m in enumerate(members):
            reps=(1,2) if i<4 else (1,)
            time_rows.append(dict(prompt=m,candidate=[clocks[role,m,r] for r in reps],native=[clocks['NATIVE35',m,r] for r in reps]))
        summaries[role]=dict(LPIPS=st.mean(lp[role,m] for m in members),budget=paired_budget(time_rows),
            quality={d:st.mean(qs[role,m,d] for m in members) for d in LIMITS},
            per_prompt=[dict(member=m,LPIPS=lp[role,m],seconds=st.mean(time_rows[i]['candidate']),
                quality={d:qs[role,m,d] for d in LIMITS}) for i,m in enumerate(members)])
    chosen,reference,native='SHARED25_C','S25_A_PHASE','NATIVE26'
    comparisons=[]
    for left,right in [(chosen,reference),(chosen,'S25_C'),('S25_A_PHASE','S25_C'),('SHARED25_A_PHASE_AGE3',chosen),(chosen,native)]:
        delta=[lp[left,m]-lp[right,m] for m in members]
        comparisons.append(dict(candidate=left,reference=right,LPIPS_delta=interval(delta),
            relative_gain=1-summaries[left]['LPIPS']/summaries[right]['LPIPS'],
            improved_prompts=sum(x<0 for x in delta),worst_increase=max(delta),per_prompt_delta=delta,
            quality_deltas={d:interval([qs[left,m,d]-qs[right,m,d] for m in members]) for d in LIMITS}))
    primary=comparisons[0];c=summaries[chosen];n=summaries[native]
    quality_gates={b:{d:interval([qs[chosen,m,d]-qs[b,m,d] for m in members]) for d in LIMITS}
                   for b in (reference,'NATIVE35')}
    # Same frozen CAL66 dominance rule: measured time no greater than +3%,
    # no worse reference fidelity and no worse in any registered quality dimension.
    native_dominates=(n['budget']['mean_candidate']<=c['budget']['mean_candidate']*1.03
        and n['LPIPS']<=c['LPIPS'] and all(n['quality'][d]>=c['quality'][d] for d in LIMITS))
    points=dict(absolute_gain=-primary['LPIPS_delta']['mean']>=.002,
        relative_gain=primary['relative_gain']>=.05,budget=c['budget']['V']<=1,
        not_dominated_by_native=not native_dominates)
    uncertainty=dict(LPIPS_upper_below_zero=primary['LPIPS_delta']['upper95']<0,budget_upper=c['budget']['V_upper95']<=1)
    for b,ds in quality_gates.items():
        for d,ci in ds.items():
            points[b+':'+d]=ci['mean']>=-LIMITS[d]
            uncertainty[b+':'+d]=ci['lower95']>=-LIMITS[d]
    return dict(status='DEV128_COMPLETE_ACCEPTED_FROZEN_DECISION',created_unix=time.time(),
        launch_id=v['launch']['launch_id'],source_revision=v['launch']['source_revision'],
        evidence={k:dict(path=str(p),sha256=sha(p)) for k,p in [('capture',capture),('acceptance',accepted),('central_settlement',settlement),('contract',ROOT/CONTRACT),('CAL_contract',ROOT/CAL_CONTRACT),('analysis_source',Path(__file__))]},
        cohort=dict(prompts=16,seeds=[0],quality_paths=96,timing_repeat_paths=24,all_paths=128,repeats_are_not_new_prompts=True),
        fixed_candidate=chosen,fixed_reference=reference,summaries=summaries,comparisons=comparisons,
        quality_gates=quality_gates,point_checks=points,uncertainty_checks=uncertainty,
        failed_point_checks=[k for k,x in points.items() if not x],failed_interval_checks=[k for k,x in uncertainty.items() if not x],
        native_dominates=native_dominates,next_branch=decision(points,uncertainty),
        actual_GPUh=replay['actual_GPUh'],selection_performed=False,GPU_submissions=0,
        final_deployment_accepted=False,independent_final_confirmation_performed=False,
        original_alpha_thresholds_and_baselines_unchanged=True)

def self_test():
    assert interval([2.]*16)['lower95']==interval([2.]*16)['upper95']==2.
    assert interval([-1.]*16)['upper95']==-1.
    assert decision({'x':False},{'x':True}).startswith('STOP')
    assert decision({'x':True},{'x':False}).startswith('INCONCLUSIVE')
    assert decision({'x':True},{'x':True}).startswith('CONTINUE')
    b=paired_budget([dict(prompt=str(i),candidate=[240.,240.] if i<4 else [240.],native=[300.,300.] if i<4 else [300.]) for i in range(16)])
    assert b['prompts']==16 and b['V']==b['V_upper95']==1.
    return dict(passed=True,checks=['constant_paired_intervals','direction','three_frozen_branches','repeats_do_not_change_prompt_weight'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true')
    for n in ('capture','acceptance','settlement'):p.add_argument('--'+n,type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    result=self_test() if a.self_test else analyze(a.capture,a.acceptance,a.settlement)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','next_branch','failed_point_checks','failed_interval_checks','actual_GPUh','passed') if k in result}))
