#!/usr/bin/env python3
"""Read completed original receipts; separate current, future and total costs."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


SCOPE={'Native_parents':2,'WC_parents':2,'complete_suffixes':12,'new_videos':10,'signed_policy_pairs':2}


def read(path):
    raw=Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def counts(row, child):
    prefix=row['deep'][:44];events=child['record']['action_report']['suffix_events']
    assert len(row['deep'])==72 and len(child['deep'])==28 and [e['call'] for e in events]==list(range(45,73))
    assert all(d in (0,26) for d in row['deep']+child['deep'])
    assert all(e['cfg_slot']==(e['call']-1)%2 and (e['actual_action']=='D')==(d==26) for e,d in zip(events,child['deep']))
    def slots(selected):
        return [sum(e['actual_action']=='D' and e['cfg_slot']==slot for e in selected) for slot in (0,1)]
    before=[sum(d==26 for d in prefix[slot::2]) for slot in (0,1)]
    suffix=slots(events);future=slots([e for e in events if e['call']>46]);target=events[1]
    return {'prefix_before_snapshot':before,'suffix_calls45_to72':suffix,
        'whole_calls1_to72':[a+b for a,b in zip(before,suffix)],
        'current_call46_full':int(target['actual_action']=='D'),
        'future_calls47_to72':future,'native_skip_at46':target['native_skip'],
        'suffix_event_calls':[e['call'] for e in events],
        'same_adaptive_continuation':child['record']['action_report']['remaining_policy']=='ORIGINAL_WC_ADAPTIVE'}


def mean(values):
    return math.fsum(values)/len(values) if values else None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('runner','score','supervisor','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--failure-audit',type=Path,action='append',default=[])
    args=parser.parse_args();assert not args.output.exists()
    runner,score,supervisor=map(read,(args.runner,args.score,args.supervisor))
    assert supervisor['exit_code']==0 and supervisor['source_revision']==runner['source_revision']
    assert runner['status']=='D46_TWO_SEEDS_GPU_CORE_COMPLETE_AUDIT_AND_SCORE_PENDING'
    assert score['status']=='D46_TWO_REGISTERED_SEEDS_FULL_CPU_AUDIT_AND_AVAILABLE_LOSSES_COMPLETE_NOT_CONF'
    assert runner['planned_scope']==score['planned_scope']==SCOPE and score['CUDA_initialized'] is False
    raw=Path(args.runner).read_bytes();raw=gzip.decompress(raw) if str(args.runner).endswith('.gz') else raw
    assert hashlib.sha256(raw).hexdigest()==score['runner_sha256']
    assert [c['seed'] for c in runner['cases']]==[c['seed'] for c in score['cases']]==[1,2]
    rows=[]
    for case,measurement in zip(runner['cases'],score['cases']):
        parent=case['WC']['requests'][0];children={c['label']:c for c in parent['children']}
        base=counts(parent,children['BASE_first']);refresh=counts(parent,children['REFRESH_first'])
        assert base==counts(parent,children['BASE_second']) and refresh==counts(parent,children['REFRESH_second'])
        eligible=bool(base['native_skip_at46']);assert eligible==measurement['verdict']['eligible_original_C46']
        assert refresh['current_call46_full']==1 and base['current_call46_full']==int(not eligible)
        assert base['same_adaptive_continuation'] and refresh['same_adaptive_continuation']
        if not eligible:assert base==refresh
        row={'seed':case['seed'],'name':case['name'],'eligible_original_C46':eligible,
             'original_D46_noop':not eligible,'Native_outcome':measurement['Native_outcome'],
             'BASE_counts':base,'REFRESH_counts':refresh,
             'current_full_added':refresh['current_call46_full']-base['current_call46_full'],
             'future_full_saved':sum(base['future_calls47_to72'])-sum(refresh['future_calls47_to72']),
             'whole_full_saved':sum(base['whole_calls1_to72'])-sum(refresh['whole_calls1_to72']),
             'diagnostic_seconds':measurement['control_costs'],'score_status':measurement['score_status']}
        assert row['whole_full_saved']==row['future_full_saved']-row['current_full_added']
        if measurement['Native_outcome']=='ACCEPTED':
            a,b=measurement['losses']['BASE'],measurement['losses']['REFRESH']
            assert len(a['frame_distances'])==len(b['frame_distances'])==93 and a['pts']==b['pts']
            quality=a['mean_LPIPS']-b['mean_LPIPS']
            cost=mean(row['diagnostic_seconds']['BASE'])-mean(row['diagnostic_seconds']['REFRESH'])
            assert math.isclose(quality,measurement['signed_quality'],abs_tol=1e-12)
            assert math.isclose(cost,measurement['signed_diagnostic_seconds'],abs_tol=1e-12)
            row.update(BASE_LPIPS=a['mean_LPIPS'],REFRESH_LPIPS=b['mean_LPIPS'],
                signed_quality_BASE_minus_REFRESH=quality,
                relative_LPIPS_improvement_percent=100*quality/a['mean_LPIPS'] if a['mean_LPIPS'] else None,
                signed_diagnostic_seconds_BASE_minus_REFRESH=cost,
                improved_frames=sum(x<y for x,y in zip(b['frame_distances'],a['frame_distances'])),
                worse_frames=sum(x>y for x,y in zip(b['frame_distances'],a['frame_distances'])),
                tied_frames=sum(x==y for x,y in zip(b['frame_distances'],a['frame_distances'])))
            if not eligible:assert quality==0 and row['tied_frames']==93
        rows.append(row)
    available=[r for r in rows if r['Native_outcome']=='ACCEPTED'];eligible=[r for r in available if r['eligible_original_C46']]
    eligible_all=[r for r in rows if r['eligible_original_C46']]
    failures=[read(p) for p in args.failure_audit]
    result={'status':'COMPLETED_D46_FRESH_SEEDS_DESCRIPTIVE_SIGNED_SUMMARY_NOT_CONF',
        'source_revision':runner['source_revision'],'scope_counts':SCOPE,
        'registered_seed_denominator':2,'quality_available':len(available),'eligible_original_C46':len(eligible_all),
        'eligible_quality_available':len(eligible),
        'original_D46_noops':sum(r['original_D46_noop'] for r in rows),'cases':rows,
        'all_available_equal_seed_mean_quality':mean([r['signed_quality_BASE_minus_REFRESH'] for r in available]),
        'all_available_equal_seed_mean_relative_improvement_percent':mean([r['relative_LPIPS_improvement_percent'] for r in available if r['relative_LPIPS_improvement_percent'] is not None]),
        'eligible_equal_seed_mean_quality':mean([r['signed_quality_BASE_minus_REFRESH'] for r in eligible]),
        'eligible_equal_seed_mean_diagnostic_seconds':mean([r['signed_diagnostic_seconds_BASE_minus_REFRESH'] for r in eligible]),
        'new_GPU_wall_seconds':supervisor['wall_seconds'],
        'retained_prior_failure_wall_seconds':math.fsum(f['supervisor']['wall_seconds'] for f in failures),
        'budget_after':supervisor['budget_after'],'independent_CONF':False,
        'clean_speed_measurement':False,'physics_or_semantic_acceptance':False,'formal_RV_training_labels':False,
        'cost_boundary':'Whole wall includes imports, model load, all controls, diagnostics, cleanup and release; diagnostic arm time is not clean end-to-end latency',
        'sample_boundary':'Two fresh seeds of one exposed prompt; frames and exact repeats are not independent scene samples',
        'input_file_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.runner,args.score,args.supervisor]+args.failure_audit}}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'registered_seed_denominator':2,'quality_available':len(available),'eligible_original_C46':len(eligible_all),'eligible_quality_available':len(eligible)}))


if __name__=='__main__':main()
