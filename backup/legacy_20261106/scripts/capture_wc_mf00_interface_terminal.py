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


LAUNCH = Path('reports/wc_mf00_interface_r1_GPU_launch_20261010.json')
PREFIX = 'reports/wc_mf00_interface_r1_terminal_20261010_'


def independent_native_check(launch, objects, artifact_path_bindings):
    c,gpu,cpu=(objects[k] for k in ('config','supervisor','CPU_receipt'));budget=objects['budget']
    assert gpu['budget_before']==launch['budget_before'] and budget==gpu['budget_after']
    assert not any('inflight' in k for k in budget) and budget['cap_gpu_hours']==77.89524658965853
    assert math.isclose(budget['used_gpu_hours'],launch['budget_before']['used_gpu_hours']+gpu['wall_seconds']/3600,abs_tol=1e-12)
    assert budget['gpu_jobs_launched']==launch['budget_before']['gpu_jobs_launched']+1
    assert not gpu['legacy_seconds_deadline_active'] and c['preregistration']['scope_counts']==launch['planned_scope']
    if gpu.get('exit_code')!=0 or cpu.get('exit_code')!=0:
        return {'native_accounting_and_complete_scope_verified':True,'success':False}
    result,runner=objects['CPU_result'],objects['runner'];state=runner['batch']
    assert result['status']=='REAL_MF00_INTERFACE_RAW_CPU_AUDIT_NOT_NEW_POLICY_OR_QUALITY'
    assert runner['status']=='REAL_MF00_INTERFACE_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    assert runner['config']==c and result['run_id']==runner['run_id']==launch['run_id']
    assert result['source_revision']==runner['source_revision']==launch['source_revision']
    assert result['actual_tensor_audit']['actual_guided_tensors_reloaded']==144
    assert result['actual_tensor_audit']['actual_final_latents_reloaded']==4 and result['actual_tensor_audit']['all_direct_equal']
    assert result['all_4_full93_videos_and_actual_raw_tensors_verified'] and not result['CUDA_initialized'] and result['GPU_submissions']==0
    assert not result['clean_latency_or_new_policy_or_quality_claim'] and result['endpoint_labels']==result['future_cost_labels']==0
    assert state['planned_paths']==state['planned_videos']==4 and len(state['requests'])==2 and state['initial_state_restored']
    parity=('guided_sha256','guided_list_tensor_sha256','solver_returns','actions','block_visits','counters','checkpoints','final_components','final_latent_sha256','final_solver_sha256','conditions_before','conditions_after','rng_after','sample_return_sha256','flags_before','flags_after','pipeline')
    for request in state['requests']:
        rows=request['paths'];assert len(rows)==2
        assert {(r['order'],r['observers'],r['repetition']) for r in rows}=={(o,b,n) for o in ('ORIGINAL','PAIRED') for b in (False,) for n in ('first',)}
        for row in rows:
            assert row['status']=='COMPLETE_PATH' and len(row['guided_sha256'])==len(row['solver_returns'])==36
            assert row['counters']==list(range(0,70,2))+[0] and len(row['actions'])==len(row['block_visits'])==36
            assert [x['step'] for x in row['checkpoints']]==[13,21,33,35,36]
            assert all(len(x['components'])==1216 for x in row['checkpoints']) and len(row['final_components'])==1216
            assert all(row[k]==rows[0][k] for k in parity)
            assert row['conditions_before']==row['conditions_after'] and row['parameter_versions_unchanged'] and row['all_modules_eval']
            if row['observers']:
                assert len(row['net_events'])==144
                event_key=lambda e:(e['call'],e['kind'])
                assert sorted(row['net_events'],key=event_key)==sorted(next(r for r in rows if r['observers'])['net_events'],key=event_key)
            else:assert not row['net_events']
            if row['order']=='PAIRED':
                assert len(row['prefix_decisions'])==28 and row['prefix_decisions'][-1]['paid_counters']==[68,69]
                assert row['native_policy_compiler']['inverse_AST_equal']
            for kind,key,items in [('tensor','vector_artifact',result['actual_tensor_audit']['files']),('video','video_artifact',result['videos'])]:
                a=row[key];item=next(x for x in items if x['label']==row['label']);alias=artifact_path_bindings[kind+':'+row['label']]
                assert item['sha256']==a['sha256']==alias['sha256'] and item['bytes']==a['bytes']==alias['bytes']
                assert alias['recorded_path']==a['path'] and alias['resolved_path']==item['path']
        group=[v for v in result['videos'] if v['sample_name']==request['sample_name']]
        assert len(group)==2 and all(v['all_frames_shape']==[93,432,768,3] for v in group)
        assert all(v['sha256']==group[0]['sha256'] and v['decoded_RGB_SHA']==group[0]['decoded_RGB_SHA'] for v in group)
    assert len(artifact_path_bindings)==8
    return {'native_accounting_and_complete_scope_verified':True,'success':True,
        'complete_4_path_state_observer_tensor_video_reconstruction':True,
        'server_actual_144_guided_and_4_latent_tensor_reload_verified':True,
        'actual_alias_path_bytes_and_sha_bindings_verified':8,'local_second_tensor_loading':False,
        'new_policy_or_endpoint_or_clean_latency_claim':False}


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
assert sha(stage/'native-policy-config.json')==L['config_sha256'] and sha(post/'driver.py')==L['post_driver_sha256']
c=json.loads((stage/'native-policy-config.json').read_text());payload={n:sha(stage/n) for n in c['payload_sha256']}
assert payload==c['payload_sha256']==cpu['payload_after_sha256'] and len(payload)==L['payload_files']
assert {n:sha(root/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
budget=json.loads((root/'reports/budget.json').read_text())
assert budget==gpu['budget_after'] and not any('inflight' in k for k in budget)
assert gpu['budget_before']==L['budget_before'] and budget['cap_gpu_hours']==77.89524658965853 and budget['gpu_jobs_launched']==L['budget_before']['gpu_jobs_launched']+1
assert math.isclose(budget['used_gpu_hours'],L['budget_before']['used_gpu_hours']+gpu['wall_seconds']/3600,abs_tol=1e-12)
# Capture the original failure as well when another owner's process appears
# after our empty-GPU admission. Its context is not our unreleased runner.
assert gpu['child_pid'] not in gpu['release']['pids']
with (root/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
observation=subprocess.check_output(['nvidia-smi','-i',c['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
assert not any(x.split(',')[0].strip()==c['gpu_uuid'] and int(x.split(',')[1])==gpu['child_pid'] for x in apps.splitlines())
success=gpu.get('exit_code')==cpu.get('exit_code')==0
if success:
 assert cpu['status']=='REAL_MF00_INTERFACE_COMPLETE_CPU_AUDIT_NOT_NEW_POLICY' and cpu['child_exit_code']==0
 assert sha(post/'result.json')==cpu['result_sha256']
 assert cpu['budget_before_sha256']==cpu['budget_after_sha256']==sha(root/'reports/budget.json')
 result=json.loads((post/'result.json').read_text())
 assert result['runner_receipt_sha256']==sha(out/'diagnostic/receipt.json') and result['config_sha256']==L['config_sha256']
bindings={}
if success:
 runner=json.loads((out/'diagnostic/receipt.json').read_text())
 for request in runner['batch']['requests']:
  for row in request['paths']:
   for kind,key,items in [('tensor','vector_artifact',result['actual_tensor_audit']['files']),('video','video_artifact',result['videos'])]:
    art=row[key];path=pathlib.Path(art['path']).resolve();assert path.is_relative_to((out/'diagnostic').resolve())
    item=next(x for x in items if x['label']==row['label'])
    assert str(path)==item['path'] and path.stat().st_size==art['bytes']==item['bytes'] and sha(path)==art['sha256']==item['sha256']
    bindings[kind+':'+row['label']]={'recorded_path':art['path'],'resolved_path':str(path),'bytes':art['bytes'],'sha256':art['sha256']}
files={'supervisor':out/'supervisor.json','CPU_receipt':post/'receipt.json','CPU_driver':post/'driver.py','CPU_driver_log':post/'driver.log','GPU_log':out/'run.log','GPU_monitor':out/'gpu-monitor.jsonl','budget':root/'reports/budget.json','config':stage/'native-policy-config.json','launch':post/'launch.json'}
for key,path in [('runner',out/'diagnostic/receipt.json'),('CPU_result',post/'result.json'),('CPU_log',post/'CPU-audit.log')]:
 if path.exists():files[key]=path
native={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
capture={'status':'REAL_MF00_INTERFACE_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS' if success else 'REAL_MF00_INTERFACE_ORIGINAL_TERMINAL_FAILURE_COMPLETE_SCOPE_RETAINED','observed_unix':time.time(),'run_id':L['run_id'],'source_revision':L['source_revision'],'original_PIDs_absent':[p for p in pids if p],'GPU_exit_code':gpu.get('exit_code'),'CPU_exit_code':cpu.get('exit_code'),'planned_scope':L['planned_scope'],'config_sha256':L['config_sha256'],'payload_after_sha256':payload,'post_driver_sha256':sha(post/'driver.py'),'lock_released':True,'GPU_observation':observation,'compute_apps':apps,'budget_settled':budget,'actual_GPU_wall_seconds':gpu['wall_seconds'],'GPU_submissions_by_capture':0,'artifact_path_bindings':bindings}
print(json.dumps({'capture':capture,'native':native}))
'''
    process = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', 'python3 -'], input=remote, text=True, capture_output=True, timeout=55)
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
