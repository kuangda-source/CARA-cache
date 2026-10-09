#!/usr/bin/env python3
"""Read the original completed GPU/CPU handles and preserve complete native evidence.

No dispatch, remote writes, tensor loading, source changes or acceptance of a subset.
"""
import base64
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess


LAUNCH = Path('reports/wc_ra_comparison_r2_GPU_launch_20261010.json')
PREFIX = 'reports/wc_ra_comparison_r2_terminal_20261010_'


def independent_native_check(launch, objects, artifact_path_bindings):
    c,gpu,cpu=(objects[k] for k in ('config','supervisor','CPU_receipt'))
    budget=objects['budget']
    assert gpu['budget_before']==launch['budget_before'] and budget==gpu['budget_after']
    assert not any('inflight' in k for k in budget) and budget['cap_gpu_hours']==77.89524658965853
    assert math.isclose(budget['used_gpu_hours'],launch['budget_before']['used_gpu_hours']+gpu['wall_seconds']/3600,abs_tol=1e-12)
    assert budget['gpu_jobs_launched']==launch['budget_before']['gpu_jobs_launched']+1
    assert not gpu['legacy_seconds_deadline_active'] and c['preregistration']['scope_counts']==launch['planned_scope']
    if gpu.get('exit_code')!=0 or cpu.get('exit_code')!=0:
        return {'native_accounting_and_complete_scope_verified':True,'success':False}
    result,runner=objects['CPU_result'],objects['runner'];state=runner['comparison'];batch=state['batch']
    assert result['status']=='REAL_RA_COMPARISON_FULL_RAW_CPU_AUDIT_NOT_QUALITY_OR_CLEAN_LATENCY'
    assert runner['status']=='REAL_RA_COMPARISON_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    assert runner['config']==c and result['run_id']==runner['run_id']==launch['run_id']
    assert result['source_revision']==runner['source_revision']==launch['source_revision']
    assert state['reference_initial_state_restored'] and batch['initial_state_restored']
    assert state['planned_paths']==8 and len(batch['requests'])==len(state['references'])==2
    assert batch['planned_paths']==6 and batch['teacher_calls']==0
    assert batch['RA_threshold']==0.070744235098772
    assert batch['calibration_fingerprint']=='9ab1d77c303560823ed2f32f43b2982318cdd9835828a46da4835a1b95ea7d7a'
    assert not result['CUDA_initialized'] and result['GPU_submissions']==0 and not result['clean_latency_claim']
    raw=result['actual_tensor_audit'];accepted=result['verdict']['accepted_reference_slots']
    assert raw['actual_guided_tensors_reloaded']==216 and raw['actual_final_latents_reloaded']==6
    assert raw['actual_initial_7_DD_guided_direct_equal']
    assert raw['actual_reference_guided_reloaded']==36*accepted and raw['actual_reference_latents_reloaded']==accepted
    assert raw['actual_reference_initial7_direct_equal']
    assert result['actual_total_guided_reloaded']==216+36*accepted and result['actual_total_latents_reloaded']==6+accepted
    assert len(result['videos'])==6+accepted and len(result['matched_fidelity_pairs'])==3*accepted
    assert len(artifact_path_bindings)==2*(6+accepted)
    def bind(kind,label,art,items):
        alias=artifact_path_bindings[kind+':'+label]
        item=next(x for x in items if x['path']==alias['resolved_path'])
        assert item['sha256']==art['sha256']==alias['sha256'] and item['bytes']==art['bytes']==alias['bytes']
        assert alias['recorded_path']==art['path']
    methods=references=0
    for request,ref in zip(batch['requests'],state['references']):
        rows=request['paths'];assert len(rows)==3 and [r['method'] for r in rows]==['WC','JOINT_NATIVE','RA']
        for row in rows:
            methods+=1
            assert row['status']=='COMPLETE_PATH' and len(row['guided_sha256'])==len(row['solver_returns'])==36
            assert row['counters']==list(range(0,70,2))+[0] and row['actions'][:7]==['DD']*7 and row['actions'][-1]=='DD'
            assert [x['step'] for x in row['checkpoints']]==[13,21,33,35,36]
            assert all(len(x['components'])==1216 for x in row['checkpoints'])
            assert row['conditions_before']==row['conditions_after']==rows[0]['conditions_before']
            assert row['first_velocity_input_sha256']==rows[0]['first_velocity_input_sha256']
            assert row['rng_after']==rows[0]['rng_after'] and row['all_modules_eval'] and row['parameter_versions_unchanged']
            for action,visits in zip(row['actions'],row['block_visits']):
                assert visits==[[1,1]+[int(a=='D')]*(row['layers']-2) for a in action]
            if row['method']=='WC':assert not row['prefix_decisions'] and not row['policy_history']
            else:
                assert [h['step'] for h in row['policy_history']]==list(range(1,37))
                assert [h['action'] for h in row['policy_history']]==row['actions']
                assert [x['step'] for x in row['prefix_decisions']]==list(range(8,36))
                for d in row['prefix_decisions']:
                    assert d['prefix_visits_before_deep']==[[1,1]+[0]*26]*2
                    assert [(p['slot'],p['counter']) for p in d['paid_probes']]==[(0,2*(d['step']-1)),(1,2*(d['step']-1)+1)]
                    assert d['action']==row['actions'][d['step']-1]
                    if row['method']=='JOINT_NATIVE':assert d['action']==('CC' if all(p['native_cache'] for p in d['paid_probes']) else 'DD')
            bind('tensor',row['label'],row['vector_artifact'],raw['files']);bind('video',row['label'],row['video_artifact'],result['videos'])
        if ref['outcome']=='ACCEPTED':
            references+=1
            assert ref['CFG_calls']==ref['block_counts']['full_calls']==72 and ref['solver_steps']==36
            assert len(ref['guided_sha256'])==len(ref['solver_returns'])==36
            assert ref['first_velocity_input_sha256']==rows[0]['first_velocity_input_sha256']
            assert ref['conditions_before']==ref['conditions_after']==rows[0]['conditions_before']
            bind('tensor',ref['sample_name']+':NATIVE',ref['vector_artifact'],raw['reference_files'])
            bind('video',ref['sample_name']+':NATIVE',ref['artifact'],result['videos'])
        else:assert ref['outcome'] in ('TEXT_REJECTED','VIDEO_REJECTED') and ref['artifact'] is None
    assert methods==6 and references==accepted
    return {'native_accounting_and_complete_scope_verified':True,'success':True,
        'complete_six_method_paths_and_two_reference_slots_reconstructed':True,
        'accepted_reference_slots':accepted,'server_actual_full_vectors_and_videos_reloaded_verified':True,
        'actual_alias_path_bytes_and_sha_bindings_verified':len(artifact_path_bindings),
        'local_second_tensor_loading':False,'endpoint_quality_scoring_pending':True,'clean_latency_claim':False}


def main():
    launch = json.loads(LAUNCH.read_text())
    remote = 'L=' + repr(launch) + '\n' + r'''
import base64,fcntl,gzip,hashlib,json,math,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=pathlib.Path(L['stage']);post=pathlib.Path(L['post_CPU_stage']);out=root/'outputs'/L['run_id']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
gpu=json.loads((out/'supervisor.json').read_text());cpu=json.loads((post/'receipt.json').read_text())
pids=[L['supervisor_pid'],gpu.get('child_pid'),L['post_CPU_pid'],cpu.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_HANDLES_STILL_LIVE_NO_TERMINAL_CAPTURE','original_live_PIDs':live,'GPU_status':gpu['status'],'CPU_status':cpu['status'],'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert gpu['pid']==L['supervisor_pid'] and cpu['pid']==L['post_CPU_pid'] and cpu['supervisor_pid']==gpu['pid']
assert gpu['source_revision']==cpu['source_revision']==L['source_revision']
assert gpu['status']=='EXITED_REQUIRES_RESULT_AUDIT' and not gpu['legacy_seconds_deadline_active']
assert sha(stage/'ra-comparison-config.json')==L['config_sha256'] and sha(post/'driver.py')==L['post_driver_sha256']
c=json.loads((stage/'ra-comparison-config.json').read_text());payload={n:sha(stage/n) for n in c['payload_sha256']}
assert payload==c['payload_sha256']==cpu['payload_after_sha256'] and len(payload)==L['payload_files']
assert {n:sha(root/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
budget=json.loads((root/'reports/budget.json').read_text())
assert budget==gpu['budget_after'] and not any('inflight' in k for k in budget)
assert gpu['budget_before']==L['budget_before'] and budget['cap_gpu_hours']==77.89524658965853 and budget['gpu_jobs_launched']==L['budget_before']['gpu_jobs_launched']+1
assert math.isclose(budget['used_gpu_hours'],L['budget_before']['used_gpu_hours']+gpu['wall_seconds']/3600,abs_tol=1e-12)
# Capture the original failure as well when another owner's process appears
# after our empty-GPU admission. Its context is not our unreleased runner.
assert gpu['child_pid'] not in gpu['release'].get('pids',[])
with (root/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
observation=subprocess.check_output(['nvidia-smi','-i',c['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
assert not any(x.split(',')[0].strip()==c['gpu_uuid'] and int(x.split(',')[1])==gpu['child_pid'] for x in apps.splitlines())
success=gpu.get('exit_code')==cpu.get('exit_code')==0
if success:
 assert cpu['status']=='REAL_RA_COMPARISON_COMPLETE_CPU_AUDIT_NOT_POLICY_QUALITY' and cpu['child_exit_code']==0
 assert sha(post/'result.json')==cpu['result_sha256']
 assert cpu['budget_before_sha256']==cpu['budget_after_sha256']==sha(root/'reports/budget.json')
 result=json.loads((post/'result.json').read_text())
 assert result['runner_receipt_sha256']==sha(out/'diagnostic/receipt.json') and result['config_sha256']==L['config_sha256']
bindings={}
if success:
 runner=json.loads((out/'diagnostic/receipt.json').read_text())
 for request,ref in zip(runner['comparison']['batch']['requests'],runner['comparison']['references']):
  artifacts=[(kind,row['label'],row[key],items) for row in request['paths'] for kind,key,items in [('tensor','vector_artifact',result['actual_tensor_audit']['files']),('video','video_artifact',result['videos'])]]
  if ref['outcome']=='ACCEPTED':
   artifacts += [('tensor',ref['sample_name']+':NATIVE',ref['vector_artifact'],result['actual_tensor_audit']['reference_files']),('video',ref['sample_name']+':NATIVE',ref['artifact'],result['videos'])]
  for kind,label,art,items in artifacts:
   path=pathlib.Path(art['path']).resolve();assert path.is_relative_to((out/'diagnostic').resolve())
   item=next(x for x in items if x['path']==str(path))
   assert path.stat().st_size==art['bytes']==item['bytes'] and sha(path)==art['sha256']==item['sha256']
   bindings[kind+':'+label]={'recorded_path':art['path'],'resolved_path':str(path),'bytes':art['bytes'],'sha256':art['sha256']}
files={'supervisor':out/'supervisor.json','CPU_receipt':post/'receipt.json','CPU_driver':post/'driver.py','CPU_driver_log':post/'driver.log','GPU_supervisor_log':post/'GPU-supervisor.log','GPU_log':out/'run.log','GPU_monitor':out/'gpu-monitor.jsonl','budget':root/'reports/budget.json','config':stage/'ra-comparison-config.json','launch':post/'launch.json'}
for key,path in [('runner',out/'diagnostic/receipt.json'),('CPU_result',post/'result.json'),('CPU_log',post/'CPU-audit.log')]:
 if path.exists():files[key]=path
native={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
capture={'status':'REAL_RA_COMPARISON_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS' if success else 'REAL_RA_COMPARISON_ORIGINAL_TERMINAL_FAILURE_COMPLETE_SCOPE_RETAINED','observed_unix':time.time(),'run_id':L['run_id'],'source_revision':L['source_revision'],'original_PIDs_absent':[p for p in pids if p],'GPU_exit_code':gpu.get('exit_code'),'CPU_exit_code':cpu.get('exit_code'),'planned_scope':L['planned_scope'],'config_sha256':L['config_sha256'],'payload_after_sha256':payload,'post_driver_sha256':sha(post/'driver.py'),'lock_released':True,'GPU_observation':observation,'compute_apps':apps,'budget_settled':budget,'actual_GPU_wall_seconds':gpu['wall_seconds'],'GPU_submissions_by_capture':0,'artifact_path_bindings':bindings}
print(json.dumps({'capture':capture,'native':native}))
'''
    process = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'], input=remote, text=True, capture_output=True, timeout=55)
    if process.returncode:
        raise RuntimeError(process.stderr[-5000:])
    value = json.loads(process.stdout)
    if not value['native']:
        print(json.dumps(value['capture']))
        return 2
    target = Path(PREFIX + 'capture_and_independent_audit.json')
    assert not target.exists()
    objects, verified = {}, {}
    for key, item in value['native'].items():
        compressed = base64.b64decode(item['gzip_base64'], validate=True)
        raw = gzip.decompress(compressed)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
        path = Path(PREFIX + key + '_native.gz'); assert not path.exists()
        verified[key] = (path, compressed, raw)
        if item['path'].endswith('.json'):
            objects[key] = json.loads(raw)
    proof = value['capture']; proof['files'] = {}
    # Save failure/evidence bytes before independent checks; an audit error retains originals.
    for key, (path, compressed, raw) in verified.items():
        path.write_bytes(compressed)
        proof['files'][key] = {k: v for k, v in value['native'][key].items() if k != 'gzip_base64'}
        proof['files'][key]['local_path'] = str(path)
    try:
        proof['independent_checks'] = independent_native_check(launch, objects, proof['artifact_path_bindings'])
    except BaseException as error:
        proof['independent_check_failure'] = {'type': type(error).__name__, 'error': str(error)}
        target.write_text(json.dumps(proof, indent=2)+'\n')
        raise
    Path('reports/budget.json').write_bytes(verified['budget'][2])
    target.write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({k: v for k, v in proof.items() if k not in ('files', 'payload_after_sha256', 'budget_settled')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
