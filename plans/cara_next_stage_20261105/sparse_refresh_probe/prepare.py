"""Freeze the requested sparse-P scope and CAL35 quote; never dispatch."""
import copy
from decimal import Decimal
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


def quote_scope(summary):
    D=Decimal('6.772260');P=Decimal('0.5')*D
    prices={name:Decimal('70.734852')+D*counts['D']+P*counts['P'] for name,counts in summary.items()}
    raw=4*sum(prices.values());requests=4*len(summary)
    center_seconds=Decimal('1.1')*raw+1200+S1_SECONDS
    range_seconds=[factor*raw+1200+S1_SECONDS for factor in (Decimal('0.9'),Decimal('1.2'))]
    center=float(center_seconds/3600);bounds=[float(s/3600) for s in range_seconds]
    feasible=center_seconds<=3600 and range_seconds[1]<=3600
    return dict(basis='Requested rounded CAL35 T_request coefficients; light-C term zero; provisional P=0.5*D.',
        provisional=True,arms=list(summary),input_count=4,P_cost_ratio=P_COST_RATIO,
        coefficients_seconds=dict(shared=70.734852,D=D_SECONDS,A=.993956,C=.637948,light_C=0,P=P_COST_RATIO*D_SECONDS),
        S1=dict(allowance_seconds=S1_SECONDS,GPUh=S1_SECONDS/3600,
            measured=False,includes='Unchanged design 0.15 GPUh allowance for one parent-prefix/local probe, including its estimated load.'),
        S2=dict(request_sum_seconds=float(raw),GPUh=float(raw/3600),requests=requests,request_prices_seconds={k:float(v) for k,v in prices.items()}),
        model_load_seconds=600,release_margin_seconds=600,
        S1_load_overlap='Unchanged conservative accounting: full design S1 allowance plus common 600s load and 600s release; no load subtraction.',
        exact_seconds=dict(S2=str(raw),center=str(center_seconds),range=[str(s) for s in range_seconds],
            hard='3600',upper_exceeds_hard=str(range_seconds[1]-3600)),
        request_sum_seconds=float(raw),forecast_GPUh=center,range_GPUh=bounds,hard_GPUh=1.,
        formal_requests=requests,warm_video_requests=0,total_requests=requests+1,S1_parent_requests=1,
        S1_local_evaluations=20,S1_next_step_comparisons=['raw','sync'],
        request_count_note=f'{requests+1} parent/video requests = one S1 prefix (no video) + {requests} S2 videos; S1 also has 20 local evaluations plus paired step30 comparison.',
        center_within_limit=center_seconds<=3600,upper_within_limit=range_seconds[1]<=3600,
        feasible_under_approved_hard_limit=feasible,
        GPU_submissions=0,ledger_reservations=0,blocked=not feasible,
        block_reason='Upper quote exceeds the approved 1.0 GPUh hard limit; stop without admission, reservation, or dispatch.' if not feasible else None)


def build():
    read=lambda name:json.loads((ROOT/name).read_text())
    old=read(BASE);scores=read(SCORES)
    assert scores['status']=='COMPLETE_PENDING_ANALYSIS'
    assert scores['scope_sha256']==old['scope_sha256']
    roles={};summary={}
    for name,positions,sync in [('b',(29,32),True),('c',(22,24),True)]:
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
        phase='BLOCKED_QUOTE_UPPER_EXCEEDS_HARD_LIMIT',GPU_dispatch_ready=False,
        authority=dict(user_quote='P 探针去掉 b0，硬限 1.0 GPUh，精确重报后在空闲卡上跑',
            hard_GPUh=1.,idle_card_only=True,mainline_confirm10_has_priority=True,
            current_instruction='Only launch after center and upper quote <=1.0 GPUh and fresh idle-card admission; otherwise stop. No routines.',
            execution_authorized=True,ledger_reservation_authorized=True,reservation_only_at_launch=True),
        **{k:copy.deepcopy(old[k]) for k in ('inputs','inputs_by_alias','profile','schedule','settings','native_references','storage')},
        roles=roles,matrix=matrix,mask_summary=summary,quote=quote,
        counts=dict(S1_parent=1,S1_local_timed=15,S1_local_warm=5,S2=8,total_requests=9,LPIPS_pairs=8),
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
        launch_block='Selected b/c four-input scope has upper quote 1.006057765333 GPUh > hard1.0 by 21.8079552s; stop before idle-card admission or ledger reservation.',
        runtime_status='Sampling hooks and callable S1 gate CPU-tested only; S1 GPU collector/ops staging remains unprepared.')
    card['scope_sha256']=digest(card)
    return card


if __name__=='__main__':
    card=build()
    for name,value in [('manifest.json',card),('quote.json',card['quote'])]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(card['quote'],ensure_ascii=False))
