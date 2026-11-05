"""Freeze the requested sparse-P scope and CAL35 quote; never dispatch."""
import argparse
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

BASE='plans/cara_next_stage_20261105/avslc_minitest/manifest.json'
SCORES='reports/cara_avslc_minitest_r1_20261105/scores.json'
R18C='DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD'
S1_SECONDS=540
D_SECONDS=6.772260
P_COST_RATIO=.5


def quote_scope(summary,*,arms=('b','b0','c'),input_count=4,hard_GPUh=1.):
    prices={name:70.734852+D_SECONDS*summary[name]['D']+P_COST_RATIO*D_SECONDS*summary[name]['P'] for name in arms}
    raw=input_count*sum(prices.values());requests=input_count*len(arms)
    center=(1.1*raw+1200+S1_SECONDS)/3600
    bounds=[(f*raw+1200+S1_SECONDS)/3600 for f in (.9,1.2)]
    return dict(basis='Requested rounded CAL35 T_request coefficients; light-C term zero; provisional P=0.5*D.',
        provisional=True,arms=list(arms),input_count=input_count,P_cost_ratio=P_COST_RATIO,
        coefficients_seconds=dict(shared=70.734852,D=D_SECONDS,A=.993956,C=.637948,light_C=0,P=P_COST_RATIO*D_SECONDS),
        S1=dict(allowance_seconds=S1_SECONDS,GPUh=S1_SECONDS/3600,
            measured=False,includes='Unchanged design 0.15 GPUh allowance for one parent-prefix/local probe, including its estimated load.'),
        S2=dict(request_sum_seconds=raw,GPUh=raw/3600,requests=requests,request_prices_seconds=prices),
        model_load_seconds=600,release_margin_seconds=600,
        S1_load_overlap='Unchanged conservative accounting: full design S1 allowance plus common 600s load and 600s release; no load subtraction.',
        zero_S1_lower_bound=dict(center_GPUh=(1.1*raw+1200)/3600,upper_GPUh=(1.2*raw+1200)/3600),
        request_sum_seconds=raw,forecast_GPUh=center,range_GPUh=bounds,hard_GPUh=hard_GPUh,
        formal_requests=requests,warm_video_requests=0,total_requests=requests+1,S1_parent_requests=1,
        S1_local_evaluations=20,S1_next_step_comparisons=['raw','sync'],
        request_count_note=f'{requests+1} parent/video requests = one S1 prefix (no video) + {requests} S2 videos; S1 also has 20 local evaluations plus paired step30 comparison.',
        center_within_limit=center<=hard_GPUh,upper_within_limit=bounds[1]<=hard_GPUh,
        feasible_under_approved_hard_limit=center<=hard_GPUh and bounds[1]<=hard_GPUh,
        GPU_submissions=0,ledger_reservations=0,blocked=True,
        block_reason='Zero-GPU amendment only; scope/limit decision and GPU staging remain pending regardless of quote feasibility.')


def quote_options(summary):
    options={}
    for name,arms,count in [('full_3_arms',('b','b0','c'),4),('drop_b0',('b','c'),4),('drop_one_input',('b','b0','c'),3)]:
        q=quote_scope(summary,arms=arms,input_count=count)
        options[name]={k:q[k] for k in ('arms','input_count','formal_requests','total_requests','request_sum_seconds','forecast_GPUh','range_GPUh')}
        options[name].update(fits_1_0_GPUh=q['feasible_under_approved_hard_limit'],
            fits_1_3_GPUh=q['forecast_GPUh']<=1.3 and q['range_GPUh'][1]<=1.3)
    return dict(provisional=True,scope_selected=False,current_manifest='full_3_arms; four inputs; hard1.0; blocked',
        P_cost_ratio=P_COST_RATIO,S1_GPUh=S1_SECONDS/3600,common_load_release_seconds=1200,
        input_drop_identity='Not selected; all inputs have identical quote cost.',options=options)


def build():
    read=lambda name:json.loads((ROOT/name).read_text())
    old=read(BASE);scores=read(SCORES)
    assert scores['status']=='COMPLETE_PENDING_ANALYSIS'
    assert scores['scope_sha256']==old['scope_sha256']
    roles={};summary={}
    for name,positions,sync in [('b',(29,32),True),('b0',(29,32),False),('c',(22,24),True)]:
        mask=list(R18C)
        for t in positions:mask[t-1]='P'
        scientific=''.join(mask)
        # The existing grammar selects the full path; SparseOwner makes it DC.
        executable=scientific.replace('P','D')
        roles[name]=dict(kind='sparse_policy',policy=policy(profile_from(old['profile']),executable,[None]*36),
            mask=scientific,partial_updates=list(positions),sync_residual=sync,
            light_C=True,requested_steps=35)
        summary[name]=dict(mask=scientific,**{c:scientific.count(c) for c in 'DACP'},
            delta_sources=[26,26] if name!='c' else [19,19],
            delta_ages=[3,6] if name!='c' else [3,5])
    matrix=[]
    for alias in ('O1','O3','N1','N3'):
        for name in roles:
            matrix.append(dict(id=f'SPARSE_{len(matrix)+1:03d}',member=old['inputs_by_alias'][alias],
                alias=alias,role=name,section='c',seed=0,target_update=None,audit=False,eligible_clean_time=True))
    quote=quote_scope(summary)
    refs=[r for r in scores['rows'] if r['slot']['role']=='R18C']
    assert len(refs)==4
    sources=[BASE,SCORES,'reports/cara_avslc_minitest_r1_20261105/complete_analysis.json',
        'plans/cara_next_stage_20261105/g17_minitest/manifest_with_nonfast.json']
    card=dict(schema='CARA_SPARSE_REFRESH_PROBE_R1',run_id='cara-sparse-refresh-probe-r1-20261105',
        phase='ZERO_GPU_AMENDMENT_PENDING_SCOPE_DECISION',GPU_dispatch_ready=False,
        authority=dict(user_quote='可以，gpu 探针如果服务器卡空闲也能做，有两张卡',
            hard_GPUh=1.,idle_card_only=True,mainline_confirm10_has_priority=True,
            current_instruction='Zero-GPU amendment only; no GPU jobs, ledger reservation, or routines.',
            execution_authorized=False,ledger_reservation_authorized=False),
        **{k:copy.deepcopy(old[k]) for k in ('inputs','inputs_by_alias','profile','schedule','settings','native_references','storage')},
        roles=roles,matrix=matrix,mask_summary=summary,quote=quote,
        counts=dict(S1_parent=1,S1_local_timed=15,S1_local_warm=5,S2=12,total_requests=13,LPIPS_pairs=12),
        S1=dict(alias='O1',state_step=29,parent_mask=R18C,modes=['D','C','P_sync','P14','P20'],
            warmup_each=1,timed_each=3,delta_source_step=26,delta_age=3,next_step=30,
            metric='guided FP64-reduction MSE vs same-state D',
            provisional=True,
            gate='median(P_sync timed seconds) / median(D timed seconds) <= 0.5 AND amplitude kappa < 0.45; otherwise release without S2',
            gate_entry='wcomr.cara_sparse_refresh_probe_r1.s1_gate',
            gate_thresholds=dict(max_cost_ratio=.5,kappa_strict_upper=.45),
            kappa_definition='lambda=drift(P29,next30)/drift(DD26,next30); kappa=(sqrt(sync_C_next_MSE/C_next_MSE)-lambda)/(1-lambda); no clipping or gamma power',
            kappa_control='Both C errors and their D teacher use the same next30 state after sync P29; no-P C control restores latest-DD caches/anchors. Raw continuation is reported separately.',
            next_step_teacher='For each raw/sync P29 continuation, compare C30 with D30 at that continuation own identical solver state.',
            Pk_layers='Execute first k of 28 blocks on both branches; reuse remaining layer residuals from latest D. No video.'),
        reused_R18C=refs,reused_sources_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
        indexing='1-based; 35 requested solver steps yield 36 updates, including terminal D36',
        guardian=dict(min_host_available_GiB=50,max_temperature_C=90,disk_low_water_GiB=4),
        ledger=dict(reserve_only_at_launch_GPUh=1.,old_unknown_reserve_GPUh=16.5,transactions_this_preparation=0),
        postrelease_CPU_entry=str(HERE.relative_to(ROOT)/'postprocess.py'),
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/cara-sparse-refresh-probe-r1-20261105',
        report_root='reports/cara_sparse_refresh_probe_r1_20261105',
        provisional_amendment=dict(same_age_uncond_A_anchor=True,
            anchor_probe='probe_c_at_P - (probe_c_DD - probe_u_DD)',
            synthetic_anchor_is_true_DD=False,update_uncond_regression=False),
        launch_block='Zero-GPU only; scope/hard-limit decision pending. Keep full three-arm/four-input design and hard1.0; no remote stage, reservation, or dispatch.',
        runtime_status='Sampling hooks and callable S1 gate CPU-tested only; S1 GPU collector/ops staging remains unprepared.')
    card['scope_sha256']=digest(card)
    return card


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--quote-option',choices=('full_3_arms','drop_b0','drop_one_input'))
    parser.add_argument('--hard-gpuh',type=float,default=1.,help='Quote-only comparison; never changes the canonical manifest limit.')
    args=parser.parse_args()
    card=build()
    options=quote_options(card['mask_summary'])
    if args.quote_option:
        scope=options['options'][args.quote_option]
        print(json.dumps(quote_scope(card['mask_summary'],arms=scope['arms'],input_count=scope['input_count'],hard_GPUh=args.hard_gpuh),ensure_ascii=False))
        sys.exit(0)
    for name,value in [('manifest.json',card),('quote.json',card['quote']),('quote_options.json',options)]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(card['quote'],ensure_ascii=False))
