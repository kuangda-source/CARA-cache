#!/usr/bin/env python3
"""Recover executed CPU controls from frozen raw records; retain exit1 summary."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def audit(root):
    started=time.perf_counter(); read=lambda p:json.loads((root/p).read_text())
    m=read('manifests/wc_w3_placement_tail_core_cpu_r1_20261007.json')
    native=read('reports/wc_w3_placement_tail_core_cpu_r1_native_capture_20261007.json')
    supervisor=read('reports/wc_w3_placement_tail_core_cpu_r1_supervisor_native_20261007.json')
    raw=gzip.decompress((root/'reports/wc_w3_placement_tail_core_cpu_r1_attempts_native_20261007.json.gz').read_bytes())
    attempts=json.loads(raw)
    log=(root/'reports/wc_w3_placement_tail_core_cpu_r1_log_native_20261007.txt').read_text()
    for item in native['local_artifacts'].values():
        data=(root/item['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==item['local_sha256']
        if item['path'].endswith('.gz'):data=gzip.decompress(data)
        assert hashlib.sha256(data).hexdigest()==item['native_sha256'] and len(data)==item['native_bytes']
    assert supervisor['exit_code']==1 and 'assert len(result[\'checks\'])==7' in log
    assert log.rstrip().endswith('AssertionError') and len(attempts)==8
    original_test=subprocess.check_output(['git','show',supervisor['source_revision']+':tests/check_rv0_placement_tail_v2_cpu.py'],cwd=root)
    assert hashlib.sha256(original_test).hexdigest()==m['new_payload_sha256']['tests/check_rv0_placement_tail_v2_cpu.py']
    assert original_test.count(b"assert len(result['checks'])==7")==1
    assert original_test.replace(b"assert len(result['checks'])==7",b"assert len(result['checks'])==8")==(root/'tests/check_rv0_placement_tail_v2_cpu.py').read_bytes()
    assert supervisor['native_before']==supervisor['native_after']
    assert supervisor['base_payload_sha256']==supervisor['base_payload_after_sha256']==m['base_payload_sha256']
    expected={**m['base_payload_sha256'],**m['new_payload_sha256']}
    assert supervisor['stage_payload_after_sha256']==expected
    assert supervisor['upstream_after_sha256']==m['upstream_source_sha256']
    assert native['original_CPU_pids_absent']
    for name in ['src/wcomr/rv0_fixed_mask_v2.py','src/wcomr/rv0_placement_v2_scope.py',
                 'src/wcomr/rv0_placement_v2_causal.py','src/wcomr/rv0_placement_v2_evaluation.py']:
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==m['new_payload_sha256'][name]
    sys.path.insert(0,str(root/'src'))
    from wcomr.rv0_placement_v2_evaluation import audit_trajectories,verify_placement_row,validate_frozen_scope
    config=read('configs/wc_w3_placement_tail_aligned_r2_scope_draft_20261007.json')
    scope=validate_frozen_scope(config['scope'])
    cases=[(a['flow'],a['failure']) for a in attempts]
    assert cases==[(False,None),(True,None),(True,'tail_proposal_difference'),(True,'child_writer'),
                  (True,'child_guardrail'),(True,'prefix_mask'),(True,'own_CFG_history'),(True,'protected_native_action')]
    successes=[];failures=[];mutation_refusals=0;tail_differences=[];pending_records=[]
    for attempt in attempts:
        state,cfg=attempt['receipt'],attempt['fixture_config']
        assert [state[k] for k in ['planned_parent_phases','planned_suffix_controls','planned_encoded_outputs']]==[2,16,10]
        if attempt['failure'] in (None,'tail_proposal_difference'):
            assert attempt['error'] is None
            audit_trajectories(state,cfg,3)
            for row,scene in zip(state['requests'],cfg['scope']['scenes']):
                assert row['historical_WC_encoded_bridge_pass']=='CPU_TOY_NOT_REAL_REFERENCE'
                assert all(c['record']['parent_restored'] is True for c in row['children'])
                if attempt['failure']=='tail_proposal_difference':
                    for child in row['children'][2:]:
                        report=child['record']['action_report']
                        event=next(e for e in report['suffix_events'] if e['call']==70)
                        assert event['tail_native_proposal_disagreement'] is True
                        assert ('C' if event['native_skip'] else 'D')!=event['actual_action']
                        assert event['actual_action']==scene['parent_action_mask'][69]
                        tail_differences.append({'scene':row['sample_name'],'label':child['label'],
                            'call':70,'native':'C' if event['native_skip'] else 'D','actual':event['actual_action']})
                for mutation in ['missing_repeat','quota','action','swap_input','protected_override',
                                 'final_state','pipeline','encoding','own_age','restore']:
                    damaged=copy.deepcopy(row);child=damaged['children'][3]
                    if mutation=='missing_repeat':damaged['children'].pop()
                    elif mutation=='quota':child['record']['action_report']['per_CFG_full_counts'][0]+=1
                    elif mutation=='action':child['deep'][0]=99
                    elif mutation=='swap_input':child['inputs'][0]={'corrupted':True}
                    elif mutation=='protected_override':
                        event=child['record']['action_report']['suffix_events'][-3]
                        event['actual_native_override']=not event.get('actual_native_override',False)
                    elif mutation=='final_state':child['record']['final_state_components']={}
                    elif mutation=='pipeline':damaged['decoded_children'][0]['pipeline'].pop()
                    elif mutation=='encoding':damaged['decoded_children'][1]['artifact']['sha256']='0'*64
                    elif mutation=='own_age':next(e for e in child['record']['action_report']['suffix_events'] if e['actual_action']=='C')['age_solver_steps']=34
                    elif mutation=='restore':child['record']['parent_restored']=False
                    try:verify_placement_row(damaged,scene,3)
                    except ValueError:mutation_refusals+=1
                    else:raise AssertionError('Frozen corrupted CPU evidence accepted: '+mutation)
            successes.append({'flow':attempt['flow'],'scenario':attempt['failure'],
                'parents':len(state['requests']),'suffixes':sum(len(r['children']) for r in state['requests']),
                'mock_outputs':sum(1+len(r['decoded_children']) for r in state['requests'])})
        else:
            assert attempt['error']
            row=state['requests'][0];child=row['children'][-1]
            assert row['status']=='TECH_BLOCKED' and child['status']=='TECH_BLOCKED'
            assert child['record']['parent_restored'] is True
            if attempt['failure'] in ('own_CFG_history','protected_native_action'):
                pending=child['record']['failure_router_before_restore']['pending']
                assert pending is not None and pending['call']>=45
                pending_records.append({'failure':attempt['failure'],'call':pending['call']})
            failures.append({'failure':attempt['failure'],'error':attempt['error'],'restored':True})
    assert len(successes)==3 and len(failures)==5 and mutation_refusals==60 and len(tail_differences)==12
    assert sum(s['parents'] for s in successes)==6 and sum(s['suffixes'] for s in successes)==48
    assert sum(s['mock_outputs'] for s in successes)==30 and len(pending_records)==2
    return {'status':'R2_CORE_FROZEN_RAW_TRACE_CPU_AUDIT_PASS_ORIGINAL_SUMMARY_FAILURE_RETAINED',
        'source_revision':supervisor['source_revision'],'raw_cpu_original_exit_code':1,
        'raw_CPU_wall_seconds':supervisor['CPU_wall_seconds'],'CPU_audit_wall_seconds':time.perf_counter()-started,
        'original_failure':'summary assertion expected7 after an eighth deliberately added case',
        'corrected_fixture_difference':'only aggregate expected count 7 to 8; executed core unchanged',
        'new_model_execution':0,'GPU_submissions':0,'original_CPU_pids_absent':True,
        'old_stage_files_unchanged':140,'stage_files_native_sha_checked':149,'upstream_files_unchanged':9,
        'budget_and_original_GPU_receipts_unchanged':True,'scope':scope,
        'successful_CPU_scenarios':successes,'complete_CPU_parents':6,'complete_CPU_suffixes':48,'mock_outputs_not_videos':30,
        'tail_proposal_differences_preserve_executed_masks':tail_differences,
        'failure_cases':failures,'failure_pending_saved_before_restore':pending_records,
        'independent_mutation_refusals':mutation_refusals,
        'real_four_pair_GPU_feasibility':'UNKNOWN_UNTIL_NEW_R2_REAL_RUN',
        'production_entry_or_GPU_approval':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=audit(args.root)
    if args.output.exists():raise ValueError('Keep prior raw-trace audit')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','CPU_audit_wall_seconds','complete_CPU_parents','complete_CPU_suffixes','mock_outputs_not_videos','independent_mutation_refusals','GPU_submissions']}))
