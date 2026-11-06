#!/usr/bin/env python3
"""Exact historical identity audit and whole-card quote; never dispatches."""
import argparse, gzip, hashlib, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.interval_grammar import Profile, Edge, compile_policy
from wcomr.policy_generator_r1.historical_bridge import historical_policies, DEPLOYMENT_LIMIT_SECONDS

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    capture=ROOT/'reports/cara_PG_P1_original_terminal_codec_recovered_20261024_0035.json'
    v=json.loads(capture.read_text());consumer=json.loads(v['files']['consumer']['raw_utf8']);batch=json.loads(v['files']['runner']['raw_utf8'])['batch']
    params=dict(consumer['profile']);params['protected_dense']=tuple(params['protected_dense']);params['alpha_candidates']=tuple(params['alpha_candidates']);profile=Profile(**params)
    policies=historical_policies(profile)
    analysis=json.loads((ROOT/'reports/wc_CAL12_independent_A_factorial_and_shared_plan_analysis_20261019.json').read_text())
    originals={
        'S26_C':('reports/wc_drop1_window24_full24_terminal_collection_20261019.json.gz','S26-C'),
        'S26_A_PHASE':('reports/wc_simple26d_memory_full36_collection_20261016_0455.json.gz','FRONT_DENSE_A'),
        'SHARED26_C':('reports/wc_scout_CAL12_full12_terminal_recovered_collection_20261019_1830.json.gz','VARIATION26_C')}
    bindings={}
    for role,(name,method) in originals.items():
        assert sha(ROOT/name)==analysis['source_bindings'][name]['sha256']
        old=json.loads(gzip.decompress((ROOT/name).read_bytes()))
        rows=[r for r in old['final']['rows'] if r['method']==method and r['section']=='TIMED'];assert len(rows)==4
        for r in rows:
            assert r['semantic_plan']==policies[role]['actions']
            for h in r['source_history']:
                if h['A_readout']['readout_action']=='A':
                    assert h['A_readout']['shared_alpha']==policies[role]['shared_alpha'][h['step']-1]
        bindings[role]=dict(capture=name,sha256=sha(ROOT/name),all_four_original_masks_and_A_alpha_equal=True)
    graph=next(c['proposal']['policy'] for c in batch['candidates'] if 'GRAPH_DIVERSE' in c['roles'])
    policies={'NATIVE':None,'PG_ALL_D':compile_policy(profile,[Edge(t,t+1) for t in range(1,37)]),'GRAPH_DIVERSE_ORIGINAL':graph,**policies}
    members=consumer['CAL_FIT_members'];roles=list(policies);assert len(roles)==10 and len(members)==4
    matrix=[]
    def add(section,role,member,repeat):
        matrix.append(dict(id=f'{section}_{role}_{members.index(member)}_{repeat}',section=section,role=role,member=member,seed=0,repeat=repeat))
    for repeat in (1,2):
        for role in (roles if repeat==1 else roles[::-1]):add('WARM',role,members[0],repeat)
    for repeat in (1,2):
        for i,member in enumerate(members):
            order=roles[i:]+roles[:i]
            if repeat==2:order=order[::-1]
            for role in order:add('CALIBRATION' if repeat==1 else 'VALIDATION',role,member,repeat)
    for role in ('NATIVE','PG_ALL_D','S26_C','S26_A_PHASE'):add('DIAGNOSTIC',role,members[0],1)
    assert len(matrix)==len({r['id'] for r in matrix})==104
    rows=[r for r in batch['rows'] if r['status']=='COMPLETE']
    native=max(r['full_request_seconds'] for r in rows if r['id'].startswith('native_fit'))
    plain=max(r['full_request_seconds'] for r in rows if r['id'].startswith('q0_fit'))
    diverse=max(r['full_request_seconds'] for r in rows if r['id'].startswith('q3_fit'))
    seconds={r:(native if r=='NATIVE' else native*1.15 if r=='PG_ALL_D' else diverse if r=='GRAPH_DIVERSE_ORIGINAL' else plain*1.03 if r.endswith('A_PHASE') else plain*1.05 if r=='SHARED26_C' else plain) for r in roles}
    components=dict(formal_GPUh=8*sum(seconds.values())/3600,warm_GPUh=2*1.10*sum(seconds.values())/3600,diagnostic_GPUh=1.5*sum(seconds[r] for r in ('NATIVE','PG_ALL_D','S26_C','S26_A_PHASE'))/3600,model_load_GPUh=.10,save_cleanup_and_release_GPUh=.40)
    forecast=sum(components.values())*1.25
    result=dict(status='HISTORICAL_STRONG_BASELINE_BOUNDARY104_SCOPE_AND_QUOTE_NOT_GPU_ADMISSION',original_bindings=bindings,P1_capture_sha256=sha(capture),profile=params,policies=policies,CAL_FIT_members=members,matrix=matrix,
        scope=dict(roles=10,CAL_FIT=4,seeds=[0],formal_repeats=2,formal_paths=80,warm_paths=20,diagnostic_paths=4,total_paths=104,guided_pairs=3744,CFG_calls=7488,loads=1,post_CPU_score_pairs=72,post_CPU_frames=6696,SELECT_paths=0,DEV_paths=0,TEST_paths=0),
        quote=dict(measured_basis='Original P1 per-arm maximum formal full request; unmeasured costs are explicit planning multipliers',arm_seconds=seconds,components=components,uncertainty_margin_fraction=.25,forecast_GPUh=forecast,billed_limit_GPUh=11.9,strict_under12=True,within_limit=forecast<11.9,cumulative_cap_GPUh=226,post_GPU_release_CPU=dict(score_pairs=72,seconds_per_pair_allowance=60,additional_seconds=1080,wall_limit_hours=1.5,cpus=2,vCPU_hours_upper=3,GPU_held=False),source_revision_binds_all_files_required=True),
        budget=dict(deployment_seconds=DEPLOYMENT_LIMIT_SECONDS,relative_native=.8,new_run_rule='min(original_absolute_limit, 0.8 * fresh_Native_mean)',relaxed=False),
        timing=dict(model='T = Native_same_prompt + b0 + bD*(nD-36) + bA*nA',fit='First clean round only, equal weights across four prompts and nine non-Native roles; Native same round provides offset',validation='Second round only; no refit from validation',fixed_margin_seconds=6.,primary_error_targets=dict(mean_absolute_relative_error_max=.01,maximum_underestimate_seconds_max=2.),no_predicted_feasible_measured_infeasible_required=True,minimum_training_rank=3,require_bD_positive=True,precision_claim='Two repeats are not a guarantee of resolving 3-4 seconds; preserve paired raw clocks and report uncertainty',diagnostic_clocks_excluded=True),
        execution=dict(quality_scoring_after_GPU_release=True,numerical_identity_checked_before_release=True,final_acceptance_after_CPU_scores=True,source_stage_immutable=True,actual_exclusive_GPU_required=True,old_bundle_unchanged=True,all_failures_and_costs_retained=True),
        GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False,old_44_draft_superseded_not_deleted=True)
    assert result['quote']['within_limit']
    with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(scope=result['scope'],quote=result['quote']),ensure_ascii=False))
if __name__=='__main__':main()
