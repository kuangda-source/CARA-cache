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


LAUNCH = Path('reports/wc_real_paired_interface_r1_GPU_launch_20261009.json')
PREFIX = 'reports/wc_real_paired_interface_r1_terminal_20261009_'


def independent_native_check(launch, objects, artifact_path_bindings=None):
    c, gpu, cpu = (objects[k] for k in ('config', 'supervisor', 'CPU_receipt'))
    budget = objects['budget']
    assert gpu['budget_before'] == launch['budget_before']
    assert budget == gpu['budget_after'] and not any('inflight' in k for k in budget)
    assert math.isclose(budget['used_gpu_hours'], launch['budget_before']['used_gpu_hours'] + gpu['wall_seconds']/3600, abs_tol=1e-12)
    assert budget['cap_gpu_hours'] == 50
    assert budget['gpu_jobs_launched'] == launch['budget_before']['gpu_jobs_launched'] + 1
    assert not gpu['legacy_seconds_deadline_active']
    assert c['preregistration']['scope_counts'] == launch['planned_scope']
    if gpu.get('exit_code') != 0 or cpu.get('exit_code') != 0:
        return {'native_accounting_and_complete_planned_scope_verified': True, 'success': False}
    result, runner = objects['CPU_result'], objects['runner']
    assert result['status'] == 'REAL_PAIRED_INTERFACE_COMPLETE_RAW_CPU_AUDIT_NOT_ENDPOINT_OR_POLICY'
    assert runner['status'] == 'REAL_PAIRED_INTERFACE_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    assert runner['config'] == c
    assert result['run_id'] == runner['run_id'] == launch['run_id']
    assert result['source_revision'] == runner['source_revision'] == launch['source_revision']
    assert (result['complete_comparisons'], result['complete_local_pairs'], result['actual_FP32_tensors_reconstructed'], result['full_state_components']) == (8, 16, 48, 1216)
    assert not result['CUDA_initialized'] and result['GPU_submissions'] == 0
    for key in ('clean_deployment_latency_claim', 'candidate_full_sampler_policy_claim', 'endpoint_labels', 'future_cost_labels'):
        assert not result[key]
    assert all(result['full_parent_parity'].values())
    state = runner['teacher']
    assert len(state['parents']) == 2 and state['planned_local_pairs'] == 16
    off, on = state['parents']
    assert off['origin'] is None and on['origin']['status'] == 'COMPLETE_INTERFACE_ORIGIN'
    for row in (off, on):
        assert row['status'] == 'COMPLETE_PARENT'
        assert len(row['inputs']) == len(row['net_measurements']) == 72
        assert len(row['solver_outputs']) == len(row['solver_measurements']) == 36
    rows = on['origin']['pairs']
    expected = [(a, o, r, order) for a in ('CC', 'DD') for o in (False, True) for r in ('first', 'second') for order in ('ORIGINAL', 'PAIRED')]
    assert [(r['action'], r['observers'], r['repetition'], r['order']) for r in rows] == expected
    assert len(rows) == len(result['artifacts']) == len(result['local_instrumented_costs']) == 16
    keys = ('origin_components', 'origin_fingerprint', 'origin_solver_configuration', 'pair_end_components', 'pair_end_fingerprint', 'pair_end_solver_configuration', 'branch_sha256', 'guided_sha256', 'block_visits')
    for action in ('CC', 'DD'):
        group = [r for r in rows if r['action'] == action]
        assert len(group) == 8 and all(all(r[k] == group[0][k] for k in keys) for r in group)
        for r in group:
            assert r['status'] == 'COMPLETE_LOCAL_INTERFACE_REQUIRES_AUDIT'
            assert r['parent_restored'] and r['bindings_restored']
            assert r['origin_components'] == r['parent_after_components']
            assert len(r['origin_components']) == len(r['pair_end_components']) == 1216
            assert r['block_visits'] == ([2, 2] + [0]*26 if action == 'CC' else [2]*28)
            assert not r['endpoint_label'] and not r['future_cost_label']
            a = r['artifact']
            assert a['tensor_sha256']['guided'] == r['guided_sha256']
            assert [a['tensor_sha256'][k] for k in ('conditional', 'unconditional')] == r['branch_sha256']
            captured = next(x for x in result['artifacts'] if x['label'] == r['label'])
            assert all(captured[k] == a[k] for k in ('bytes', 'sha256', 'tensor_sha256'))
            if artifact_path_bindings is None:
                assert captured['path'] == a['path']
            else:
                alias = artifact_path_bindings[r['label']]
                assert alias['recorded_path'] == a['path']
                assert alias['resolved_path'] == captured['path']
                assert alias['bytes'] == a['bytes'] and alias['sha256'] == a['sha256']
        for observers in (False, True):
            for repetition in ('first', 'second'):
                old, new = [r for r in group if r['observers'] == observers and r['repetition'] == repetition]
                assert old['selector_calls'] == 0 and new['selector_calls'] == 1 and len(new['paid_probes']) == 2
                if observers:
                    normalize = lambda es: {(e['kind'], e['slot']): e for e in es}
                    assert len(old['observer_events']) == len(new['observer_events']) == 4
                    assert normalize(old['observer_events']) == normalize(new['observer_events'])
                else:
                    assert not old['observer_events'] and not new['observer_events']
    assert len(result['videos']) == 2
    for video, parent in zip(result['videos'], state['parents']):
        assert video['sha256'] == parent['artifact']['sha256']
        assert video['all_frames_shape'] == [93, 432, 768, 3] and video['fps'] == 16
    assert result['videos'][0]['sha256'] == result['videos'][1]['sha256']
    assert result['videos'][0]['decoded_RGB_SHA'] == result['videos'][1]['decoded_RGB_SHA']
    return {'native_accounting_and_complete_planned_scope_verified': True, 'success': True,
            'independent_JSON_state_observer_artifact_and_parent_reconstruction': True,
            'server_actual_raw_tensor_CPU_audit_verified': True,
            'local_second_tensor_loading': False, 'endpoint_or_policy_claim': False}


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
assert sha(stage/'teacher-config.json')==L['config_sha256'] and sha(post/'driver.py')==L['post_driver_sha256']
c=json.loads((stage/'teacher-config.json').read_text());payload={n:sha(stage/n) for n in c['payload_sha256']}
assert payload==c['payload_sha256']==cpu['payload_after_sha256'] and len(payload)==L['payload_files']==156
assert {n:sha(root/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
budget=json.loads((root/'reports/budget.json').read_text())
assert budget==gpu['budget_after'] and not any('inflight' in k for k in budget)
assert gpu['budget_before']==L['budget_before'] and budget['cap_gpu_hours']==50 and budget['gpu_jobs_launched']==L['budget_before']['gpu_jobs_launched']+1
assert math.isclose(budget['used_gpu_hours'],L['budget_before']['used_gpu_hours']+gpu['wall_seconds']/3600,abs_tol=1e-12)
assert not gpu['release']['pids'] and gpu['release']['memory_used_mib']<=1024
with (root/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
observation=subprocess.check_output(['nvidia-smi','-i',c['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
assert not any(x.split(',')[0].strip()==c['gpu_uuid'] for x in apps.splitlines())
success=gpu.get('exit_code')==cpu.get('exit_code')==0
if success:
 assert cpu['status']=='REAL_PAIRED_INTERFACE_COMPLETE_CPU_AUDIT_NOT_ENDPOINT_OR_POLICY' and cpu['child_exit_code']==0
 assert sha(post/'result.json')==cpu['result_sha256']
 assert cpu['budget_before_sha256']==cpu['budget_after_sha256']==sha(root/'reports/budget.json')
 result=json.loads((post/'result.json').read_text())
 assert result['runner_receipt_sha256']==sha(out/'diagnostic/receipt.json') and result['config_sha256']==L['config_sha256']
files={'supervisor':out/'supervisor.json','CPU_receipt':post/'receipt.json','CPU_driver':post/'driver.py','CPU_driver_log':post/'driver.log','GPU_log':out/'run.log','GPU_monitor':out/'gpu-monitor.jsonl','budget':root/'reports/budget.json','config':stage/'teacher-config.json','launch':post/'launch.json'}
for key,path in [('runner',out/'diagnostic/receipt.json'),('CPU_result',post/'result.json'),('CPU_log',post/'CPU-audit.log')]:
 if path.exists():files[key]=path
native={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
capture={'status':'REAL_PAIRED_INTERFACE_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS' if success else 'REAL_PAIRED_INTERFACE_ORIGINAL_TERMINAL_FAILURE_COMPLETE_SCOPE_RETAINED','observed_unix':time.time(),'run_id':L['run_id'],'source_revision':L['source_revision'],'original_PIDs_absent':[p for p in pids if p],'GPU_exit_code':gpu.get('exit_code'),'CPU_exit_code':cpu.get('exit_code'),'planned_scope':L['planned_scope'],'config_sha256':L['config_sha256'],'payload_after_sha256':payload,'post_driver_sha256':sha(post/'driver.py'),'lock_released':True,'GPU_observation':observation,'compute_apps':apps,'budget_settled':budget,'actual_GPU_wall_seconds':gpu['wall_seconds'],'GPU_submissions_by_capture':0}
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
        proof['independent_checks'] = independent_native_check(launch, objects)
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
