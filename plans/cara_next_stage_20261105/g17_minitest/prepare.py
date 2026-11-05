"""Build the two quote-only scopes using the existing CAL35 policy grammar."""
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.policy_generator_r1.interval_grammar import Edge,compile_policy,digest

read=lambda name:json.loads((ROOT/name).read_text())
CAL='plans/cara_next_stage_20261103/f19_speed190_cal/CAL35_MANIFEST_R1.json'
ANALYSIS='reports/cara_f19_speed190_complete_r1_20261103/complete_analysis.json'
CONFIRM='reports/cara_f17_confirm4_r1_20261104/collection.json'
GENERATED='reports/cara_principle_fit_20261105/gen_results_M5f.json'
MEMBERS=['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','misc_13398218_3840_2160_60fps',
    'av_cc90f226-5312-4e0f-959a-39cd4eb4d90d','misc_9699390-uhd_3840_2160_30fps']
MAIN=['G17','G17_TAIL','F17_A2_LIGHT_C']
DIAGNOSTIC=['F19_A1_LIGHT_C','F17_ORIGINAL_C','F19_A2_LATE4_LIGHT_C','F17_D27_LIGHT_C']


def policy(profile,mask,alpha):
    assert len(mask)==36 and set(mask)<=set('DAC')
    dense=[i+1 for i,c in enumerate(mask) if c=='D']+[37]
    edges=[]
    for start,end in zip(dense,dense[1:]):
        active=[t for t in range(start+1,end) if mask[t-1]=='A']
        window=(active[0],active[-1]) if active else ()
        edges.append(Edge(start,end,window,alpha[active[0]-1] if active else 0.0))
    result=compile_policy(profile,edges)
    assert ''.join(result['actions'])==mask and result['shared_alpha']==alpha
    return result


def build():
    original=read(CAL);generated=read(GENERATED);profile=profile_from(original['profile'])
    f17=original['roles']['F17_A2_LIGHT_C'];f19=original['roles']['F19_A1_LIGHT_C']
    roles={k:copy.deepcopy(original['roles'][k]) for k in ('F17_A2_LIGHT_C','F19_A1_LIGHT_C')}
    masks={k:''.join(v['policy']['actions']) for k,v in roles.items()}
    g17=generated['layouts']['17']['mask'];assert g17=='DDDDDDDDDDDDDADADAADAAAAAAACCCCCCCCD'
    assert (g17[12],g17[26])==('D','A')
    tail=list(g17);tail[12]='A';tail[26]='D'
    masks.update(G17=g17,G17_TAIL=''.join(tail),G19=generated['layouts']['19']['mask'],G22=generated['layouts']['22']['mask'])
    masks['F17_ORIGINAL_C']=masks['F17_A2_LIGHT_C']
    late=list(masks['F19_A1_LIGHT_C'])
    for t in (22,23,25,26):assert late[t-1]=='C';late[t-1]='A'
    masks['F19_A2_LATE4_LIGHT_C']=''.join(late)
    restored=list(masks['F17_A2_LIGHT_C']);assert restored[26]=='C';restored[26]='D'
    masks['F17_D27_LIGHT_C']=''.join(restored)
    for name,mask in masks.items():
        if name in roles:continue
        alpha=[(f17['policy']['shared_alpha'][i] if name in ('F17_ORIGINAL_C','F19_A2_LATE4_LIGHT_C','F17_D27_LIGHT_C') else 1.0) if c=='A' else None for i,c in enumerate(mask)]
        roles[name]=dict(kind='speed_policy',requested_steps=35,policy=policy(profile,mask,alpha),
            light_C=name!='F17_ORIGINAL_C',partial_updates=[],
            light_C_semantics=f17['light_C_semantics'],delta_semantics=f17['delta_semantics'])
    expected={'G17':(17,11,8),'G17_TAIL':(17,11,8),'F17_A2_LIGHT_C':(17,10,9),
        'F19_A1_LIGHT_C':(19,6,11),'F17_ORIGINAL_C':(17,10,9),'F19_A2_LATE4_LIGHT_C':(19,10,7),
        'F17_D27_LIGHT_C':(18,10,8),'G19':(19,17,0),'G22':(22,14,0)}
    for name,role in roles.items():assert tuple(role['policy']['counts'][k] for k in 'DAC')==expected[name]
    # Fit full-request cost to four measured CAL35 clean means, not to LPIPS.
    measured={r['role']:r for r in read(ANALYSIS)['rows']}
    native=measured['NATIVE35']['T_request'];f=measured['F17_A2_LIGHT_C']['T_request'];l=measured['F19_A1_LIGHT_C']['T_request']
    d=((native-l)-1.5*(l-f))/14;a=(2*d-(l-f))/4
    shared=native-36*d;c=(measured['F19_A1']['T_request']-l)/11
    prices={k:shared+d*v['policy']['counts']['D']+a*v['policy']['counts']['A']+(0 if v['light_C'] else c*v['policy']['counts']['C']) for k,v in roles.items()}
    confirm=read(CONFIRM);clean_confirm=[r for r in confirm['rows'] if r['slot']['section']=='c' and r['slot']['role']=='F17_A2_LIGHT_C']
    methods=['src/wcomr/cara_f19_speed190_requests_r1.py','src/wcomr/cara_f19_speed190_sampling_r1.py','src/wcomr/policy_generator_r1/production_sampling.py','src/wcomr/paper_latency_r1.py']
    revisions=['ee105ecb3f3ab8a7e7e348ef275f5d4bf3cd34c9','6e33ee31544225802cbb07a7084de8d2cc8e14a1']
    comparison={rev:{name:hashlib.sha256(subprocess.check_output(['git','show',rev+':'+name],cwd=ROOT)).hexdigest()==hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in methods} for rev in revisions}
    anchor=dict(basis='CAL35 full clean T_request means; four-parameter exact cost interpolation. Center+10%, engineering range -10%/+20%,600s load+600s release. CPU scoring excluded from GPU bill.',
        CAL35_ref=ANALYSIS,measured_clean={k:dict(T_DD=measured[k]['T_DD'],T_request=measured[k]['T_request']) for k in ('NATIVE35','F19_A1','F19_A1_LIGHT_C','F17_A2_LIGHT_C')},
        marginal_seconds=dict(shared=shared,D=d,A=a,original_C=c),
        confirm4_F17_T_request_seconds=[r['result']['T_request'] for r in clean_confirm],
        confirm4_F17_T_request_mean=statistics.mean(r['result']['T_request'] for r in clean_confirm),
        historical_code_equal=comparison,same_hardware='two_card RTX A6000 GPU-cebf7119-cf03-23b9-e192-cd196332b704',
        F17_control_decision='Include4: historical paths are functionally comparable, but belong to different batches; small marginal cost buys same-batch paired T_DD/LPIPS.',
        unmeasured='Long-A placement and guardrail variability; range is engineering, not confidence interval.',remote_calls=0)
    natives={}
    sources=[('reports/cara_f19_speed190_complete_r1_20261103/original_collection.json',MEMBERS[:2]),(CONFIRM,MEMBERS[2:])]
    for source,names in sources:
        collection=read(source)
        for member in names:
            row=next(r for r in collection['rows'] if r['slot']['member']==member and r['slot']['role']=='NATIVE35' and r['slot']['eligible_clean_time'])
            natives[member]=dict(collection_ref=source,slot_id=row['slot']['id'],video_artifact=row['result']['video_artifact'],scope_sha256=collection['scope_sha256'])
    old_scores=read('reports/cara_f17_confirm4_r1_20261104/scores.json')
    historical={m:next(r for r in old_scores['LPIPS'] if r['slot']['member']==m and r['slot']['role']=='F19_A1') for m in MEMBERS[2:]}
    assert all(r['result']['reference']['sha256']==natives[m]['video_artifact']['sha256'] for m,r in historical.items())
    inputs=read('plans/cara_next_stage_20261104/sensitivity/manifest.json')['inputs']
    def make(with_nonfast):
        matrix=[]
        def add(member,role,section):matrix.append(dict(id=f'G17MINI_{len(matrix)+1:03d}',member=member,role=role,section=section,seed=0,target_update=None,audit=False,eligible_clean_time=section!='warm'))
        add(MEMBERS[0],'F17_A2_LIGHT_C','warm');add(MEMBERS[0],'F17_ORIGINAL_C','warm')
        for i,member in enumerate(MEMBERS):
            for role in MAIN[i%3:]+MAIN[:i%3]:add(member,role,'c')
            if member in MEMBERS[2:]:
                diag=DIAGNOSTIC if member==MEMBERS[2] else DIAGNOSTIC[2:]+DIAGNOSTIC[:2]
                for role in diag:add(member,role,'c')
        if with_nonfast:
            for i,member in enumerate(MEMBERS):
                for role in (['G19','G22'] if i%2==0 else ['G22','G19']):add(member,role,'c')
        raw=sum(prices[r['role']] for r in matrix);center=(1.1*raw+1200)/3600
        interval=[(.9*raw+1200)/3600,(1.2*raw+1200)/3600]
        quote=dict(anchors=anchor,request_prices_seconds=prices,request_sum_seconds=raw,
            forecast_GPUh=center,range_GPUh=interval,hard_GPUh=math.ceil(interval[1]*4)/4,
            expected_wall_hours=center,model_load_seconds=600,release_margin_seconds=600,
            F17_controls_marginal_center_GPUh=4*prices['F17_A2_LIGHT_C']*1.1/3600,
            formal_requests=28 if with_nonfast else 20,warm_requests=2,total_requests=len(matrix))
        run='cara-g17-minitest-'+('with-nonfast' if with_nonfast else 'base')+'-r1-20261105'
        card=dict(schema='CARA_G17_MINITEST_QUOTE_R1',run_id=run,phase='FORMAL_QUOTE_AWAITING_APPROVAL',
            authority=dict(execution_authorized=False,ledger_reservation_authorized=False,sync_launch_authorized=False),GPU_dispatch_ready=False,
            inputs=[copy.deepcopy(next(r for r in inputs if r['name']==m)) for m in MEMBERS],
            inputs_by_alias=dict(zip(('O1','O3','N1','N3'),MEMBERS)),
            profile=original['profile'],schedule=original['schedule'],settings=original['settings'],roles=roles,matrix=matrix,
            counts=dict(a=0,b=0,c=quote['formal_requests'],warm=2,controls=4,total_requests=len(matrix),LPIPS_pairs=quote['formal_requests'],quality_positions=0),
            mask_summary={name:dict(mask=masks[name],**roles[name]['policy']['counts']) for name in roles},
            indexing=dict(human_steps='1-based actual update; mask[step-1]',terminal=36,terminal_graph_node=37,zero_based_G17_tail_rejected_counts=dict(D=18,A=11,C=7)),
            base_CAL35_manifest_ref=CAL,base_CAL35_scope_sha256=original['scope_sha256'],
            runtime_setup_ref='configs/f1_setup.json',runtime_torch_version='2.7.1+cu128',
            generated_source=GENERATED,generated_A_alpha=1.0,F17_A2_gains=dict(other_A=1.0,step25=.5,step26=.5),
            native_references=natives,fresh_Native_timing_requests=0,
            historical_F19_A1=historical,
            contrasts=[dict(candidate=x,reference=y,members=members) for x,y,members in
                [('G17','F17_A2_LIGHT_C',MEMBERS),('G17_TAIL','F17_A2_LIGHT_C',MEMBERS),('G17_TAIL','G17',MEMBERS),
                 ('F19_A1_LIGHT_C','F19_A1_HISTORY',MEMBERS[2:]),('F17_ORIGINAL_C','F17_A2_LIGHT_C',MEMBERS[2:]),
                 ('F19_A2_LATE4_LIGHT_C','F19_A1_LIGHT_C',MEMBERS[2:]),('F17_D27_LIGHT_C','F17_A2_LIGHT_C',MEMBERS[2:])]]
                 +([dict(candidate=k,reference='F17_A2_LIGHT_C',members=MEMBERS) for k in ('G19','G22')] if with_nonfast else []),
            runtime_entry='plans/cara_next_stage_20261104/sensitivity/runner.py',
            loaded_request_entry='wcomr.cara_f19_speed190_requests_r1.Requests',
            postrelease_CPU_entry='plans/cara_next_stage_20261105/g17_minitest/postprocess.py',
            postrelease_CPU_resources=dict(cpus=2,RAM_GiB=8,wall_seconds=3600,max_vCPUh=2),
            future_admission='Separate frozen stage/binding and Linux production CPU acceptance required; no ops/dispatch invoked by this quote.',
            storage=dict(private_output_GiB=16,RAM_GiB=40,minimum_host_available_GiB=50,temperature_stop_C=90,minimum_output_free_bytes=4*2**30,state_saves=0,outputs='MP4, terminal latent, ordinary request history; no Native state recording'),
            quote=quote,preregistration_ref='plans/cara_next_stage_20261105/g17_minitest/PREREGISTRATION.md',
            output_root='/data20t/gaokuangda/worldcache_workspace/outputs/'+run)
        card['scope_sha256']=digest(card)
        return card
    return make(False),make(True)


if __name__=='__main__':
    base,extended=build()
    for name,value in [('manifest.json',base),('manifest_with_nonfast.json',extended),('quote.json',dict(base=base['quote'],base_plus_19D_22D=extended['quote'],GPU_submissions=0,ledger_reservations=0,sync_launch=False))]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    for c in (base,extended):print(json.dumps(dict(run_id=c['run_id'],requests=len(c['matrix']),center=c['quote']['forecast_GPUh'],range=c['quote']['range_GPUh'],hard=c['quote']['hard_GPUh'])))
