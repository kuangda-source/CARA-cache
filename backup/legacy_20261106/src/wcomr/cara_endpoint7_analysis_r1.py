"""Complete E1 metadata analysis; never decode, rescore, select or freeze a method."""
import copy
from .cara_fast_b36_analysis_r1 import CLOCKS,METRICS,MEAN_METRICS,mean
from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_scores_r1 import accept_scores
from .cara_s_uniform_endpoint_execution_r1 import check_collection
from .policy_price_terminal_r1 import require

ROLES=('F19_C','UNIFORM19_C','F19_A1','SU19_BR_DIAG_C','SU19_CFG_C','BUDGET_SEARCH19_C','F19_RISKSWAP_C')
COMPARISONS=(('SU19_CFG_C','SU19_BR_DIAG_C'),('F19_RISKSWAP_C','F19_C'),
             ('SU19_CFG_C','F19_A1'),('BUDGET_SEARCH19_C','F19_A1'),('SU19_CFG_C','BUDGET_SEARCH19_C'))

def analyze(card,collection,accepted,*,packet,config,manifest_sha256,result,execution,cpu_validation=False):
    require(card.get('endpoint7') is True and packet['manifest'].get('endpoint7') is True,
            'Selected seven-role interface required')
    validated=accept_scores(packet,config,manifest_sha256,result,execution,cpu_validation=cpu_validation)
    require(accepted==validated and accepted['formal_logical_positions']==28,
            'Original complete28 accepted scores required')
    require(packet['release']['CPU_fixture_only'] is cpu_validation
            and packet['release']['physical_paths']==46
            and packet['release']['scope_sha256']==card['scope_sha256']==config['analysis_scope_sha256']
            and packet['release']['collection_sha256']==check_collection(card,collection,cpu_validation=cpu_validation),
            'Original complete46 released collection required')
    timing={}
    for row in collection['rows']:
        slot=row['slot']
        if not slot['eligible_clean_time']:continue
        timing.setdefault((slot['member'],slot['role']),[]).append(dict(slot_id=slot['id'],
            section=slot['section'],**{c:row['result'][c] for c in CLOCKS}))
    require(sum(map(len,timing.values()))==38,'All38 registered clean timings required')
    native={m:{c:mean([r[c] for r in timing[(m,'NATIVE35')]]) for c in CLOCKS} for m in card['FIT']+card['CHECK']}
    rows=[]
    for position in accepted['positions']:
        m,r=position['member'],position['role'];score=accepted['source_rows'][position['score_id']]
        samples=timing.get((m,r),[])
        require(bool(samples)==(r!='UNIFORM19_C'),'Only Uniform retains historical-only timing')
        times={c:mean([s[c] for s in samples]) for c in CLOCKS} if samples else None
        rows.append(dict(member=m,role=r,partition='FIT' if m in card['FIT'] else 'CHECK',
            score_id=position['score_id'],score_mode=position['mode'],
            metrics={k:copy.deepcopy(score[k]) for k in METRICS},timing_samples=samples,time_mean=times,
            timing_source='SAME_ALLOCATION' if samples else 'HISTORICAL_ONLY_NOT_POOLED',
            speedup={c:native[m][c]/times[c] for c in CLOCKS} if times else None))
    groups={};comparisons={}
    for partition,members in [('ALL',card['FIT']+card['CHECK']),('FIT',card['FIT']),('CHECK',card['CHECK'])]:
        summaries=[]
        native_means={c:mean([native[m][c] for m in members]) for c in CLOCKS}
        for role in ROLES:
            selected=[r for r in rows if r['role']==role and r['member'] in members]
            require(len(selected)==len(members),'Complete per-role prompt denominator required')
            times={c:mean([r['time_mean'][c] for r in selected]) for c in CLOCKS} if role!='UNIFORM19_C' else None
            undefined=[r['member'] for r in selected if r['metrics']['gradient_energy_ratio'] is None]
            summaries.append(dict(role=role,members=members,prompt_count=len(members),
                metrics={k:mean([r['metrics'][k] for r in selected]) for k in MEAN_METRICS},
                time_mean=times,speedup={c:native_means[c]/times[c] for c in CLOCKS} if times else None,
                PSNR_per_member={r['member']:r['metrics']['PSNR_video_dB'] for r in selected},
                gradient_energy_ratio=None if undefined else mean([r['metrics']['gradient_energy_ratio'] for r in selected]),
                undefined_gradient_members=undefined))
        groups[partition]=summaries
        by={(r['member'],r['role']):r for r in rows};deltas=[]
        for left,right in COMPARISONS:
            values={m:by[(m,left)]['metrics']['Alex']-by[(m,right)]['metrics']['Alex'] for m in members}
            deltas.append(dict(left=left,right=right,metric='Alex',lower_is_better=True,
                mean_difference=mean(list(values.values())),per_member_difference=values,
                improved_members=[m for m,d in values.items() if d<0],equal_members=[m for m,d in values.items() if d==0],
                worsened_members=[m for m,d in values.items() if d>0],worst_difference=max(values.values())))
        comparisons[partition]=deltas
    return dict(schema='CARA_ENDPOINT7_COMPLETE_ANALYSIS_R1',
        status='CPU_FIXTURE_ONLY' if cpu_validation else 'COMPLETE_ACCEPTED_E1_ANALYSIS',CPU_fixture_only=cpu_validation,
        scope_sha256=card['scope_sha256'],launch_id=config['launch_id'],run_id=config['run_id'],
        formal_logical_positions=28,new_scored_pairs=16,reused_original_rows=12,clean_timing_samples=38,
        source_receipt_sha256=dict(collection=digest(collection),packet=digest(packet),accepted=digest(accepted),execution=digest(execution)),
        per_member=rows,prompt_equal_summaries=groups,comparisons=comparisons,native_time_per_member=native,
        timing_rule='Average registered formal/replay and repeat per prompt, then equal prompt means; ratio of means',
        historical_Uniform_timing_pooled=False,PSNR_rule='Per-video values preserved, including +inf; no pooled mean',
        all93_frame_curves_preserved=True,independent_TEST=False,new_selection=False,new_freeze=False,
        GPU_submissions=0,ledger_written=False,metrics_computed=False)
