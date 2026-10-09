#!/usr/bin/env python3
"""Preserve original CPU evidence and independently compare the complete paths."""
import base64
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=('r1','r2'),default='r1');args=parser.parse_args()
    prefix='reports/wc_cfg_complete_native_policy_sampling_cpu_'+args.attempt+'_terminal_20261009_'
    launch=json.loads(Path('reports/wc_cfg_complete_native_policy_sampling_cpu_'+args.attempt+'_launch_20261009.json').read_text())
    remote='L='+repr(launch)+'\n'+r'''
import json,pathlib,hashlib,gzip,base64,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_COMPLETE_NATIVE_POLICY_SAMPLING_CPU_STILL_LIVE','original_live_PIDs':live,'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((stage/'complete-native-policy-sampling-preregistration.json').read_text())
assert sha(stage/'complete-native-policy-sampling-preregistration.json')==L['registration_sha256']
assert r['planned_scope']==reg['CPU_scope']==L['CPU_scope']
assert r['payload_after_sha256']==reg['payload_sha256']=={n:sha(stage/n) for n in reg['payload_sha256']}
assert r['runtime_after_sha256']==reg['runtime_source_sha256']=={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
files={n:stage/n for n in ('receipt.json','core.log','driver.log','launch.json','complete-native-policy-sampling-preregistration.json')}
for n in ('result.json','result.failure.json'):
 if (stage/n).exists():files[n]=stage/n
if r['exit_code']==0:
 assert r['status']=='COMPLETE_NATIVE_POLICY_SAMPLING_CPU_NOT_REAL_MODEL' and r['child_exit_code']==0
 assert sha(stage/'result.json')==r['result_sha256']
items={}
for n,p in files.items():
 raw=p.read_bytes();z=gzip.compress(raw,mtime=0);items[n]={'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(z).hexdigest(),'base64':base64.b64encode(z).decode()}
capture={'status':'COMPLETE_NATIVE_POLICY_SAMPLING_CPU_TERMINAL_SUCCESS' if r['exit_code']==0 else 'COMPLETE_NATIVE_POLICY_SAMPLING_CPU_FAILURE_COMPLETE_SCOPE_RETAINED','source_revision':r['source_revision'],'exit_code':r['exit_code'],'original_PIDs_absent':pids,'CPU_wall_seconds':r['CPU_wall_seconds'],'payload_files':len(reg['payload_sha256']),'runtime_sources':len(reg['runtime_source_sha256']),'planned_scope':reg['CPU_scope'],'budget_before_sha256':r['budget_before_sha256'],'budget_after_sha256':r['budget_after_sha256'],'CPU_never_writes_ledger':r['ledger_written_by_this_driver'] is False,'GPU_submissions':0,'observed_unix':time.time()}
print(json.dumps({'capture':capture,'native':items}))
'''
    run=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=remote,text=True,capture_output=True,timeout=55)
    if run.returncode:raise RuntimeError(run.stderr[-4000:])
    result=json.loads(run.stdout);proof=result['capture']
    if not result['native']:print(json.dumps(proof));return 2
    target=Path(prefix+'capture_and_independent_audit.json');assert not target.exists()
    proof['files']={};objects={}
    for name,item in result['native'].items():
        z=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(z)
        assert hashlib.sha256(z).hexdigest()==item['compressed_sha256']
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        p=Path(prefix+name+'.native.gz');assert not p.exists();p.write_bytes(z)
        proof['files'][name]={k:v for k,v in item.items() if k!='base64'};proof['files'][name]['local_path']=str(p)
        if name.endswith('.json'):objects[name]=json.loads(raw)
    if proof['exit_code']==0:
        core=objects['result.json'];reg=objects['complete-native-policy-sampling-preregistration.json'];rows=core['checks']
        assert core['planned_scope']==reg['CPU_scope'] and core['payload_sha256']==reg['payload_sha256']
        assert not core['CUDA_initialized'] and core['GPU_submissions']==0 and len(rows)==4
        assert {(r['flow'],r['scenario']) for r in rows}=={(f,s) for f in (False,True) for s in ('complete','last_vector_writer_failure')}
        parity=('guided_sha256','guided_list_tensor_sha256','solver_returns','actions','block_visits','counters','checkpoints','final_components','final_latent_sha256','final_solver_sha256','conditions_before','conditions_after','rng_after','sample_return_sha256','flags_before','flags_after','pipeline')
        for row in rows:
            state=row['receipt'];assert state['planned_paths']==state['planned_videos']==16
            assert state['initial_state_restored'] and len(state['requests'])==2
            assert all(len(r['paths'])==8 for r in state['requests'])
            if row['scenario']=='complete':
                assert row['status']=='PASS' and len(row['semantic_mutation_refusals'])==12
                assert row['actual_artifact_truncation_refused']
                assert row['actual_tensor_audit']['actual_guided_tensors_reloaded']==576
                assert row['actual_tensor_audit']['actual_final_latents_reloaded']==16
                assert row['actual_tensor_audit']['all_direct_equal'] and len(row['actual_tensor_audit']['files'])==16
                for request in state['requests']:
                    paths=request['paths'];assert {(p['order'],p['observers'],p['repetition']) for p in paths}=={(o,b,r) for o in ('ORIGINAL','PAIRED') for b in (False,True) for r in ('first','second')}
                    assert len(request['prepared_input_calls'])==8
                    assert all(p['prepared']==request['prepared_input_calls'][0]['prepared'] for p in request['prepared_input_calls'])
                    for path in paths:
                        assert path['status']=='COMPLETE_PATH' and len(path['guided_sha256'])==len(path['solver_returns'])==36
                        assert path['counters']==list(range(0,70,2))+[0]
                        assert [c['step'] for c in path['checkpoints']]==[13,21,33,35,36]
                        assert all(len(c['components'])==50 for c in path['checkpoints']) and len(path['final_components'])==50
                        assert path['conditions_before']==path['conditions_after'] and path['all_modules_eval'] and path['parameter_versions_unchanged']
                        assert all(path[k]==paths[0][k] for k in parity)
                        assert path['video_artifact']['sha256']==paths[0]['video_artifact']['sha256']
                        if path['observers']:
                            assert len(path['net_events'])==144
                            assert path['net_events']==next(p for p in paths if p['observers'])['net_events']
                        else:assert not path['net_events']
                        if path['order']=='PAIRED':
                            assert len(path['prefix_decisions'])==28 and path['prefix_decisions'][-1]['paid_counters']==[68,69]
                            assert path['native_policy_compiler']['inverse_AST_equal']
            else:
                assert row['status']=='EXPECTED_FAILURE' and row['complete_scope_retained'] and row['initial_full_state_restored']
                last=state['requests'][-1]['paths'][-1]
                assert last['status']=='TECH_BLOCKED_COMPLETE_SCOPE_RETAINED' and len(last['guided_sha256'])==len(last['solver_returns'])==36
                assert 'vector_artifact' not in last
        proof.update(complete_rows=4,complete_successful_paths=32,complete_executed_paths_including_last_writer_failures=64,
            solver_updates=2304,net_calls=4608,actual_Toy_guided_tensors_reloaded=1152,actual_final_latents_reloaded=32,
            complete_new_actual_batch_matrix_and_last_writer_failures_verified=True,
            semantic_mutation_refusals=24,actual_truncation_refusals=2,
            local_second_tensor_loading=False,real_model_or_endpoint_or_policy_benefit_claim=False)
    target.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k not in ('files','all_registered_rows','planned_scope')}))
    return proof['exit_code']


if __name__=='__main__':raise SystemExit(main())
