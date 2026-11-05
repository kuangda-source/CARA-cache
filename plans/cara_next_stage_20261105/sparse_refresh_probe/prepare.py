"""Freeze the requested sparse-P scope and CAL35 quote; never dispatch."""
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


def build():
    read=lambda name:json.loads((ROOT/name).read_text())
    old=read(BASE);scores=read(SCORES)
    assert scores['status']=='COMPLETE_PENDING_ANALYSIS'
    assert scores['scope_sha256']==old['scope_sha256']
    roles={};prices={};summary={}
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
        prices[name]=70.734852+D_SECONDS*summary[name]['D']+.55*D_SECONDS*summary[name]['P']
    matrix=[]
    for alias in ('O1','O3','N1','N3'):
        for name in roles:
            matrix.append(dict(id=f'SPARSE_{len(matrix)+1:03d}',member=old['inputs_by_alias'][alias],
                alias=alias,role=name,section='c',seed=0,target_update=None,audit=False,eligible_clean_time=True))
    raw=sum(prices[s['role']] for s in matrix)
    center=(1.1*raw+1200+S1_SECONDS)/3600
    bounds=[(f*raw+1200+S1_SECONDS)/3600 for f in (.9,1.2)]
    quote=dict(basis='Requested rounded CAL35 T_request coefficients; light-C term zero; P=0.55*D.',
        coefficients_seconds=dict(shared=70.734852,D=D_SECONDS,A=.993956,C=.637948,light_C=0,P=.55*D_SECONDS),
        S1=dict(allowance_seconds=S1_SECONDS,GPUh=S1_SECONDS/3600,
            measured=False,includes='Design 0.15 GPUh allowance for one parent-prefix/local probe, including its estimated load.'),
        S2=dict(request_sum_seconds=raw,GPUh=raw/3600,requests=12,request_prices_seconds=prices),
        model_load_seconds=600,release_margin_seconds=600,
        S1_load_overlap='Conservatively add the full design S1 allowance to the explicitly required common 600s load and 600s release; no load subtraction is needed to establish refusal.',
        zero_S1_lower_bound=dict(center_GPUh=(1.1*raw+1200)/3600,upper_GPUh=(1.2*raw+1200)/3600),
        request_sum_seconds=raw,forecast_GPUh=center,range_GPUh=bounds,hard_GPUh=1.,
        formal_requests=12,warm_video_requests=0,total_requests=13,S1_parent_requests=1,
        S1_local_evaluations=20,S1_next_step_comparisons=['raw','sync'],
        request_count_note='13 parent/video requests = one S1 prefix (no video) + 12 S2 videos. S1: five modes x (one warmup + three timed), plus paired step30 diagnostic.',
        center_within_limit=center<=1.,upper_within_limit=bounds[1]<=1.,
        feasible_under_approved_hard_limit=center<=1. and bounds[1]<=1.,
        GPU_submissions=0,ledger_reservations=0,blocked=True)
    refs=[r for r in scores['rows'] if r['slot']['role']=='R18C']
    assert len(refs)==4
    sources=[BASE,SCORES,'reports/cara_avslc_minitest_r1_20261105/complete_analysis.json',
        'plans/cara_next_stage_20261105/g17_minitest/manifest_with_nonfast.json']
    card=dict(schema='CARA_SPARSE_REFRESH_PROBE_R1',run_id='cara-sparse-refresh-probe-r1-20261105',
        phase='BLOCKED_QUOTE_EXCEEDS_HARD_LIMIT',GPU_dispatch_ready=False,
        authority=dict(user_quote='可以，gpu 探针如果服务器卡空闲也能做，有两张卡',
            hard_GPUh=1.,idle_card_only=True,mainline_confirm10_has_priority=True),
        **{k:copy.deepcopy(old[k]) for k in ('inputs','inputs_by_alias','profile','schedule','settings','native_references','storage')},
        roles=roles,matrix=matrix,mask_summary=summary,quote=quote,
        counts=dict(S1_parent=1,S1_local_timed=15,S1_local_warm=5,S2=12,total_requests=13,LPIPS_pairs=12),
        S1=dict(alias='O1',state_step=29,parent_mask=R18C,modes=['D','C','P_sync','P14','P20'],
            warmup_each=1,timed_each=3,delta_source_step=26,delta_age=3,next_step=30,
            metric='guided FP64-reduction MSE vs same-state D',
            gate='median(P_sync timed seconds) / median(D timed seconds) <= 0.55; otherwise release without S2',
            next_step_teacher='For each raw/sync P29 continuation, compare C30 with D30 at that continuation own identical solver state.',
            Pk_layers='Execute first k of 28 blocks on both branches; reuse remaining layer residuals from latest D. No video.'),
        reused_R18C=refs,reused_sources_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
        indexing='1-based; 35 requested solver steps yield 36 updates, including terminal D36',
        guardian=dict(min_host_available_GiB=50,max_temperature_C=90,disk_low_water_GiB=4),
        ledger=dict(reserve_only_at_launch_GPUh=1.,old_unknown_reserve_GPUh=16.5,transactions_this_preparation=0),
        postrelease_CPU_entry=str(HERE.relative_to(ROOT)/'postprocess.py'),
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/cara-sparse-refresh-probe-r1-20261105',
        report_root='reports/cara_sparse_refresh_probe_r1_20261105',
        launch_block='Quote center and upper exceed 1.0 GPUh even with zero S1 allowance. No remote stage, reservation, or dispatch.',
        runtime_status='Sampling hooks and CPU fixture only; S1 GPU collector/ops staging deliberately not prepared after failed quote gate.')
    card['scope_sha256']=digest(card)
    return card


if __name__=='__main__':
    card=build()
    for name,value in [('manifest.json',card),('quote.json',card['quote'])]:
        (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(card['quote'],ensure_ascii=False))
