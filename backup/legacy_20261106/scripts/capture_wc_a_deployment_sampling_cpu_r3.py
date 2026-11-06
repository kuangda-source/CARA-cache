#!/usr/bin/env python3
"""Capture original full-sampling CPU evidence, without redispatch or GPU work."""
import ast
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-retained',action='store_true',help='Verify saved original bytes without rerunning the CPU batch')
    args=parser.parse_args()
    launch_path = Path('reports/wc_a_deployment_sampling_cpu_r3_launch_20261010.json')
    launch = json.loads(launch_path.read_text())
    code = 'L=' + repr(launch) + '\n' + r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4<<20),b''):h.update(b)
 return h.hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_FULL_SAMPLING_CPU_STILL_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(stage/'driver.py')==L['driver_sha256'] and sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
assert {n:sha(stage/n) for n in reg['payload_sha256']}==r['payload_after_sha256']==reg['payload_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
assert r['GPU_submissions']==0 and not r['ledger_written'] and not r['GPU_lock_acquired']
artifacts=[]
for p in sorted((stage/'CPU-artifacts').rglob('*')):
 if p.is_file():artifacts.append({'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)})
aliases={}
if r['exit_code']==0:
 value=json.loads((stage/'result.json').read_text())
 for check in value['checks']:
  state=check['receipt']
  for request in state['batch']['requests']:
   for row in request['paths']:
    art=row['vector_artifact'];path=pathlib.Path(art['path']).resolve()
    assert (stage/'CPU-artifacts').resolve() in path.parents and path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
    aliases[art['path']]=str(path)
  for ref in state['references']:
   if 'vector_artifact' in ref:
    art=ref['vector_artifact'];path=pathlib.Path(art['path']).resolve()
    assert (stage/'CPU-artifacts').resolve() in path.parents and path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
    aliases[art['path']]=str(path)
files=['receipt.json','registration.json','launch.json','driver.py','driver.log','test.log']
files.extend(n for n in ('result.json','result.failure.json') if (stage/n).exists())
native={}
for n in files:
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(stage/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'status':'FULL_SAMPLING_ORIGINAL_CPU_TERMINAL','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'GPU_submissions':0,'ledger_written':False,'actual_CPU_artifacts':artifacts,'recorded_to_resolved_tensor_paths':aliases,'observed_unix':time.time()},'native':native}))
'''
    call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
                          input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:
        raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout)
    if not value['native']:
        print(json.dumps(value['capture'])); return 2
    prefix='reports/wc_a_deployment_sampling_cpu_r3_terminal_20261010_'
    original_dest=Path(prefix+'capture.json')
    dest=Path(prefix+('capture_reaudit.json' if args.audit_retained else 'capture.json')); assert not dest.exists()
    retained=json.loads(original_dest.read_text()) if args.audit_retained else None
    if retained is not None:
        assert retained['exit_code']==0 and retained['independent_check_error']['type']=='KeyError'
        assert retained['actual_CPU_artifacts']==value['capture']['actual_CPU_artifacts']
    proof=value['capture']; proof['files']={}; objects={}
    for n,item in value['native'].items():
        packed=base64.b64decode(item['base64'],validate=True); raw=gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(packed).hexdigest()==item['compressed_sha256']
        p=Path(prefix+n+'.native.gz')
        if retained is None:
            assert not p.exists(); p.write_bytes(packed)
        else:
            assert p.read_bytes()==packed and retained['files'][n]['sha256']==item['sha256']
        proof['files'][n]={k:v for k,v in item.items() if k!='base64'}
        proof['files'][n]['local_path']=str(p)
        if n.endswith('.json'): objects[n]=json.loads(raw)
    if retained is not None:
        proof['original_failed_capture_ref']=str(original_dest)
        proof['original_failed_capture_sha256']=hashlib.sha256(original_dest.read_bytes()).hexdigest()
        proof['original_native_bytes_unchanged']=True
        proof['repair_current_capture_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    try:
        assert objects['launch.json']==launch
        gitreg=subprocess.check_output(['git','show',launch['source_revision']+':manifests/wc_a_deployment_sampling_cpu_r3_preregistration_20261010.json'])
        assert hashlib.sha256(gitreg).hexdigest()==launch['registration_sha256']
        assert json.loads(gitreg)==objects['registration.json']
        for n,digest in objects['registration.json']['payload_sha256'].items():
            assert hashlib.sha256(subprocess.check_output(['git','show',launch['source_revision']+':'+n])).hexdigest()==digest
        deploy=subprocess.check_output(['git','show',launch['source_revision']+':scripts/deploy_wc_a_deployment_sampling_cpu_r3.py'])
        tree=ast.parse(deploy)
        drivers=[n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DRIVER' for t in n.targets)]
        assert len(drivers)==1 and hashlib.sha256(ast.literal_eval(drivers[0]).encode()).hexdigest()==launch['driver_sha256']
        if proof['exit_code']==0:
            receipt=objects['receipt.json']; result=objects['result.json']
            assert receipt['child_exit_code']==0 and proof['files']['result.json']['sha256']==receipt['result_sha256']
            assert result['status']=='A_DEPLOYMENT_COMPLETE_SAMPLING_CPU_NOT_REAL_MODEL'
            assert result['planned_scope']==objects['registration.json']['CPU_scope']
            assert (result['solver_updates'],result['net_calls'],result['actual_guided_tensors_reloaded'],result['actual_final_latents_reloaded'])==(4608,9216,2304,64)
            assert result['semantic_mutation_refusals']==32 and result['actual_truncation_refusals']==result['last_path_writer_failure_controls']==2
            assert not result['CUDA_initialized'] and result['GPU_submissions']==0 and not result['real_model_or_latency_or_endpoint_claim']
            assert len(result['A_sampler_source_compilers'])==6 and all(p['inverse_AST_equal'] for p in result['A_sampler_source_compilers'])
            good=[c for c in result['checks'] if c['status']=='PASS'];bad=[c for c in result['checks'] if c['status']=='EXPECTED_FAILURE']
            assert len(good)==len(bad)==2 and {c['flow'] for c in good}=={False,True}
            actual={x['path']:x for x in proof['actual_CPU_artifacts']}
            seen=set()
            methods=['WC','JOINT_NATIVE','RA','W1_GLOBAL_1','BETA1_GLOBAL_1','W1_ONE_PHASE','BETA1_ONE_PHASE']
            for check in good:
                raw=check['actual_tensor_audit'];state=check['receipt']
                assert (raw['actual_guided_tensors_reloaded'],raw['actual_final_latents_reloaded'],raw['actual_reference_guided_reloaded'],raw['actual_reference_latents_reloaded'])==(1008,28,144,4)
                assert raw['actual_initial_7_DD_guided_direct_equal'] and raw['actual_reference_initial7_direct_equal']
                assert len(raw['files'])==28 and len(raw['reference_files'])==4 and len(check['semantic_mutation_refusals'])==16 and check['actual_final_method_truncation_refused']
                for item in raw['files']+raw['reference_files']:
                    assert actual[item['path']]['bytes']==item['bytes'] and actual[item['path']]['sha256']==item['sha256'];seen.add(item['path'])
                assert state['planned_paths']==32 and state['planned_method_paths']==28 and state['planned_reference_paths']==4
                assert state['batch']['initial_state_restored'] and state['reference_initial_state_restored'] and len(state['references'])==len(state['batch']['requests'])==4
                for request,ref in zip(state['batch']['requests'],state['references']):
                    rows=request['paths'];assert [row['method'] for row in rows]==methods
                    assert len(request['prepared_input_calls'])==7 and all(p['prepared']==request['prepared_input_calls'][0]['prepared'] for p in request['prepared_input_calls'])
                    assert ref['outcome']=='ACCEPTED' and ref['CFG_calls']==72 and ref['solver_steps']==36 and ref['block_counts']['full_calls']==72
                    assert len(ref['guided_sha256'])==len(ref['solver_returns'])==36
                    assert ref['condition_fields_before']==ref['condition_fields_after']==rows[0]['condition_fields_before']
                    assert ref['first_velocity_input_sha256']==rows[0]['first_velocity_input_sha256']
                    assert ref['prepared_input_calls'][0]['prepared']==request['prepared_input_calls'][0]['prepared']
                    for row in rows:
                        assert row['status']=='COMPLETE_PATH' and len(row['guided_sha256'])==len(row['solver_returns'])==len(row['actions'])==len(row['block_visits'])==36
                        assert row['actions'][:7]==['DD']*7 and row['actions'][-1]=='DD' and row['counters']==list(range(0,70,2))+[0]
                        assert [x['step'] for x in row['checkpoints']]==[13,21,33,35,36]
                        assert row['condition_fields_before']==row['condition_fields_after']==rows[0]['condition_fields_before'] and row['actual_raw_solver_configuration']['raw_values']
                        assert row['parameter_versions_unchanged'] and row['all_modules_eval']
                        assert all(v==[[1,1]+[int(a=='D')]*(row['layers']-2) for a in action] for v,action in zip(row['block_visits'],row['actions']))
                        if row['method'] in methods[3:]:
                            a=row['A_readout'];assert a['completed_pairs']==len(a['history'])==36 and a['teacher_calls']==a['extra_candidate_deep_blocks']==0
                            assert len(row['policy_history'])==36 and [x['action'] for x in row['policy_history']]==row['actions']
                            dense=[]
                            for step,(h,action) in enumerate(zip(a['history'],row['actions']),1):
                                if action=='DD':dense.append(step)
                                alpha=.5 if row['method'].endswith('ONE_PHASE') and step>=25 else 1
                                assert h['step']==step and h['action']==action and h['shared_alpha']==alpha and h['past_D_steps']==[dense[-2:]]*2
                                assert h['teacher_calls']==h['extra_deep_blocks']==0 and h['post_RF_fusion'] and not h['C_readout_updates_D_anchor']
                                assert h['extra_heads']==sum(s in ('scalar','BETA1') for s in h['branch_status'])
                            assert a['extra_candidate_heads']==sum(h['extra_heads'] for h in a['history']) and all(x['anchor_steps']==dense[-2:] for x in a['D_only_final_history'])
            for check in bad:
                assert check['complete_scope_retained'] and check['initial_full_state_restored']
                state=check['receipt'];assert state['planned_paths']==32 and len(state['references'])==4 and len(state['batch']['requests'])==4
                last=state['references'][-1];assert last['status']=='MATCHED_NATIVE_FAILED_COMPLETE_SCOPE_RETAINED'
                assert len(last['guided_sha256'])==len(last['solver_returns'])==36 and 'vector_artifact' not in last
                for request in state['batch']['requests']:
                    for row in request['paths']:
                        art=row['vector_artifact'];resolved=proof['recorded_to_resolved_tensor_paths'][art['path']];seen.add(resolved)
                        assert actual[resolved]['sha256']==art['sha256']
                for ref in state['references'][:-1]:
                    art=ref['vector_artifact'];resolved=proof['recorded_to_resolved_tensor_paths'][art['path']];seen.add(resolved)
                    assert actual[resolved]['sha256']==art['sha256']
            tensorpaths={p for p in actual if p.endswith('.pt')}
            assert len(tensorpaths)==126 and seen==tensorpaths
            assert len([p for p in actual if p.endswith('.mp4')])==128
        proof['independent_source_complete_results_and_actual_artifact_hashes_verified']=True
    except BaseException as error:
        proof['independent_check_error']={'type':type(error).__name__,'message':str(error)}
        dest.write_text(json.dumps(proof,indent=2)+'\n'); raise
    dest.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('files','actual_CPU_artifacts')})); return 0


if __name__=='__main__': raise SystemExit(main())
