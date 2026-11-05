"""Compile the approved A/light-C scope and price it without dispatching."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from plans.cara_next_stage_20261105.g17_minitest.prepare import policy
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.policy_generator_r1.interval_grammar import digest

OLD='reports/cara_g17_minitest_nonfast_r1_20261105'
PRED='plans/cara_next_stage_20261105/prereg_next.json'
MASKS={
    'G17_ATAIL':'DDDDDDDDDDDDDADADAADAAAAAAAAAAAAAAAD',
    'G17_CALL':'DDDDDDDDDDDDDCDCDCCDCCCCCCCCCCCCCCCD',
    'G17_A21_24':'DDDDDDDDDDDDDADADAADAAAACCCCCCCCCCCD',
    'R18C':'DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD',
    'R17A':'DDDDDDDDADADADADADADAADAAADCCCCCCCCD'}
COUNTS={'G17_ATAIL':(17,19,0),'G17_CALL':(17,0,19),
    'G17_A21_24':(17,8,11),'R18C':(18,0,18),'R17A':(17,11,8)}
T_DD={'G17_ATAIL':139.43,'G17_CALL':123.28,'G17_A21_24':130.08,'R18C':130.09,'R17A':132.63}
read=lambda name:json.loads((ROOT/name).read_text())


def build():
    old=read('plans/cara_next_stage_20261105/g17_minitest/manifest_with_nonfast.json')
    scores=read(OLD+'/scores.json');analysis=read(OLD+'/complete_analysis.json')
    assert scores['status']=='COMPLETE_PENDING_ANALYSIS' and analysis['status']=='COMPLETE'
    assert analysis['scope_sha256']==scores['scope_sha256']==old['scope_sha256']
    profile=profile_from(old['profile']);roles={}
    for name,mask in MASKS.items():
        assert tuple(mask.count(c) for c in 'DAC')==COUNTS[name]
        alpha=[1.0 if c=='A' else None for c in mask]
        roles[name]=dict(kind='speed_policy',requested_steps=35,policy=policy(profile,mask,alpha),
            light_C=True,partial_updates=[],light_C_semantics=old['roles']['G17']['light_C_semantics'],
            delta_semantics=old['roles']['G17']['delta_semantics'])
    matrix=[];members=list(old['inputs_by_alias'].values());order=list(roles)
    def add(member,role,section):
        matrix.append(dict(id=f'AVSLC_{len(matrix)+1:03d}',member=member,role=role,section=section,
            seed=0,target_update=None,audit=False,eligible_clean_time=section!='warm'))
    add(members[0],'G17_CALL','warm');add(members[0],'G17_ATAIL','warm')
    for i,member in enumerate(members):
        for role in order[i:]+order[:i]:add(member,role,'c')
    anchors={k:copy.deepcopy(old['quote']['anchors'][k]) for k in ('basis','CAL35_ref','measured_clean','marginal_seconds')}
    cost=anchors['marginal_seconds']
    prices={name:cost['shared']+cost['D']*counts[0]+cost['A']*counts[1] for name,counts in COUNTS.items()}
    raw=sum(prices[s['role']] for s in matrix);formal=4*sum(prices.values())
    center=(1.1*raw+1200)/3600
    quote=dict(anchors=anchors,request_prices_seconds=prices,request_sum_seconds=raw,
        formal_request_seconds=formal,warm_request_seconds=raw-formal,
        forecast_GPUh=center,range_GPUh=[(.9*raw+1200)/3600,(1.2*raw+1200)/3600],
        hard_GPUh=1.5,expected_wall_hours=center,model_load_seconds=600,release_margin_seconds=600,
        without_warm_center_GPUh=(1.1*formal+1200)/3600,
        formal_requests=20,warm_requests=2,total_requests=22,
        feasible_under_approved_hard_limit=center<=1.5)
    controls=[copy.deepcopy(r) for r in scores['rows'] if r['slot']['role'] in ('F17_A2_LIGHT_C','G17')]
    sources=[OLD+'/scores.json',OLD+'/complete_analysis.json',PRED,
        'plans/cara_next_stage_20261105/principle_refit_report.md',
        'plans/cara_next_stage_20261105/g17_minitest/postprocess.py']
    card=dict(schema='CARA_AVSLC_MINITEST_R1',run_id='cara-avslc-minitest-r1-20261105',
        phase='FORMAL_QUOTE_AWAITING_APPROVAL',GPU_dispatch_ready=False,
        dispatch_blocker='CAL35 mandatory quote center exceeds approved hard1.5; no reserve/stage/launch.',
        authority=dict(execution_authorized=True,ledger_reservation_authorized=True,sync_launch_authorized=True,
            user_quote='User-approved AVSLC scope, center about1.2 GPUh, hard1.5 GPUh; no authority to increase hard limit.'),
        reservation_event='AVSLC_MINITEST_WHOLE1_5_RESERVE',
        **{k:copy.deepcopy(old[k]) for k in ('inputs','inputs_by_alias','profile','schedule','settings','native_references','storage')},
        roles=roles,matrix=matrix,mask_summary={name:dict(mask=MASKS[name],D=COUNTS[name][0],A=COUNTS[name][1],C=COUNTS[name][2]) for name in roles},
        counts=dict(a=0,b=0,c=20,warm=2,controls=0,total_requests=22,LPIPS_pairs=20,quality_positions=0),
        generated_A_alpha=1.0,indexing='1-based update t = mask[t-1]; 36 updates, terminal graph node37',
        fresh_Native_timing_requests=0,fresh_control_requests=0,reused_control_count=8,
        reuse_control_report=OLD,reused_controls=controls,
        reused_control_source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},
        frozen_predictions=read(PRED),predicted_T_DD=T_DD,
        contrasts=[dict(candidate=name,reference=ref,members=members) for name in roles for ref in ('F17_A2_LIGHT_C','G17')]
            +[dict(candidate=x,reference=y,members=members) for x,y in
                [('R17A','R18C'),('G17_CALL','R18C'),('G17_ATAIL','G17_A21_24')]],
        primary_prediction_arms=['G17_CALL','R18C'],model_comparison='Mean absolute error of two primary arms equal-input mean LPIPS/F17 ratios; descriptive preference only, no refit or significance test.',
        runtime_entry=old['runtime_entry'],loaded_request_entry=old['loaded_request_entry'],
        runtime_setup_ref=old['runtime_setup_ref'],runtime_torch_version=old['runtime_torch_version'],
        postrelease_CPU_entry='plans/cara_next_stage_20261105/avslc_minitest/postprocess.py',
        postrelease_CPU_resources=old['postrelease_CPU_resources'],postrelease_inputs=sources,
        preregistration_ref='plans/cara_next_stage_20261105/avslc_minitest/PREREGISTRATION.md',
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/cara-avslc-minitest-r1-20261105',quote=quote)
    card['scope_sha256']=digest(card)
    return card


if __name__=='__main__':
    card=build()
    for name,value in [('manifest.json',card),('quote.json',dict(**card['quote'],mask_summary=card['mask_summary'],GPU_submissions=0,ledger_reservations=0,blocked=True))]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(center=card['quote']['forecast_GPUh'],range=card['quote']['range_GPUh'],hard=1.5,mask_summary=card['mask_summary'],blocked=True)))
