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


LAUNCH = Path('reports/wc_current_birth_full64_r1_GPU_launch_20261010.json')
PREFIX = 'reports/wc_current_birth_full64_r1_terminal_20261010_'
SOURCE_REG = Path('manifests/wc_current_birth_full64_capture_source_r1_preregistration_20261010.json')


def independent_native_check(launch, objects, artifact_path_bindings):
    from wc_current_birth_full64_independent_r1 import COUNTS, STRATEGIES, METHODS, NAMES, costs_from_runner, slots_from_pairing
    c, gpu, cpu = (objects[k] for k in ('config', 'supervisor', 'CPU_receipt'))
    budget = objects['budget']
    assert gpu['budget_before'] == launch['budget_before'] and budget == gpu['budget_after']
    assert not any('inflight' in k for k in budget) and budget['cap_gpu_hours'] == 77.89524658965853
    assert math.isclose(budget['used_gpu_hours'], launch['budget_before']['used_gpu_hours'] + gpu['wall_seconds']/3600, abs_tol=1e-12)
    assert budget['gpu_jobs_launched'] == launch['budget_before']['gpu_jobs_launched'] + 1
    assert not gpu['legacy_seconds_deadline_active'] and c['preregistration']['scope_counts'] == launch['planned_scope'] == COUNTS
    assert len(c['payload_sha256']) == launch['payload_files'] == 620
    assert c['GPU_execution_selected'] and launch['GPU_submissions_by_launch'] == 1
    approval = objects['single_job_exception_authority']
    assert approval['direct_user_authorization'] is True and approval['card'] == 'WC-CURRENT-BIRTH-CAPD-FULL64-R1-20261010-A'
    assert approval['run_id'] == launch['run_id'] == 'wc-current-birth-capd-full64-r1'
    assert approval['scope_counts'] == COUNTS and approval['preregistration_sha256'] == c['preregistration_sha256']
    assert approval['forecast_complete_GPUh'] == c['preregistration']['forecast']['forecast_complete_GPUh'] == launch['forecast_complete_GPUh']
    source_config = subprocess.check_output(['git', 'show', launch['source_revision'] + ':configs/wc_current_birth_full64_selected_r1_20261010.json'])
    assert hashlib.sha256(source_config).hexdigest() == launch['config_sha256'] and json.loads(source_config) == c
    source_authority = subprocess.check_output(['git', 'show', launch['source_revision'] + ':' + c['single_job_exception_authority']['ref']])
    assert hashlib.sha256(source_authority).hexdigest() == c['single_job_exception_authority']['sha256'] and json.loads(source_authority) == approval
    if gpu.get('exit_code') != 0 or cpu.get('exit_code') != 0:
        return {'native_accounting_and_complete_scope_verified': True, 'success': False,
                'partial_outputs_not_accepted_as_complete': True}
    raw, runner = objects['CPU_result'], objects['runner']
    assert raw['status'] == 'CURRENT_BIRTH_FULL64_RAW_CPU_PASS_NOT_FIDELITY_SCORE' and raw['exit_code'] == 0
    assert runner['status'] == 'CURRENT_BIRTH_REAL_FULL64_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    assert runner['config'] == c and raw['planned_scope'] == runner['planned_scope'] == COUNTS
    assert raw['source_revision'] == runner['source_revision'] == launch['source_revision']
    assert runner['run_id'] == launch['run_id'] and runner['completed_strategies'] == list(STRATEGIES)
    assert not any(raw[k] for k in ('CUDA_initialized', 'GPU_submissions', 'budget_written', 'clean_speed_or_physics_or_new_fidelity_claim'))
    assert (raw['actual_all_guided_tensors_reloaded'], raw['actual_all_final_latents_reloaded'],
            raw['accepted_new_videos'], raw['Native_videos_rechecked']) == (2304, 64, 64, 4)
    assert raw['no_P_RA_and_OFF_exact_and_full_GEMM_reference_verified'] and raw['all_unpaired_slots_retained']
    costs = costs_from_runner(runner); slots = slots_from_pairing(raw['pairing'])
    assert len(costs) == len(slots) == len(raw['decoded_videos']) == 64
    assert raw['compatible_pairs'] + raw['incompatible_pairs'] == 64
    assert raw['compatible_pairs'] == sum(s['compatible'] for s in slots)
    refs = runner['matched_Native_metadata']; assert [r['sample_name'] for r in refs] == list(NAMES)
    assert all(r['outcome'] == 'ACCEPTED' and r['solver_steps'] == 36 and r['CFG_calls'] == 72 for r in refs)
    assert len(artifact_path_bindings) == 132  # 64 tensors, 64 new videos, four original Native videos.
    def bind(kind, label, artifact):
        b = artifact_path_bindings[kind + ':' + label]
        assert b['recorded_path'] == artifact['path'] and b['bytes'] == artifact['bytes'] and b['sha256'] == artifact['sha256']
    for strategy in STRATEGIES:
        batch = runner['batches'][strategy]; audit = raw['raw_audits'][strategy]
        assert batch['planned_parent_paths'] == 32 and batch['planned_origins'] == batch['planned_post_RF_branch_tensors'] == 0
        assert batch['selected_steps'] == [] and [r['sample_name'] for r in batch['requests']] == list(NAMES)
        assert (audit['actual_guided_reloaded'], audit['actual_latents_reloaded'],
            audit['full_GEMM_partial_trajectory_references'], audit['original_RA_trajectory_references'],
            audit['A_OFF_trajectory_references']) == (1152, 32, 4, 4, 4)
        assert len(audit['files']) == 32
        for request, ref in zip(batch['requests'], refs):
            rows = request['paths']; prepared = request['prepared_input_calls']
            assert [r['collect'] for r in rows] == list(METHODS) and len(prepared) == 8
            assert all(p['prepared'] == prepared[0]['prepared'] for p in prepared)
            for row, entry in zip(rows, prepared):
                assert len(row['guided_sha256']) == len(row['solver_returns']) == 36
                assert row['counters'] == list(range(0,70,2)) + [0]
                assert row['actions'][:7] == ['DD']*7 and row['actions'][-1] == 'DD'
                assert row['origins'] == [] and len(row['P0_roundtrips']) == 4
                assert all(v['complete_additional_state_restored'] and v['physical_state_restored'] for v in row['P0_roundtrips'])
                assert row['conditions_before'] == row['conditions_after'] and row['condition_fields_before'] == row['condition_fields_after']
                assert row['all_modules_eval'] and row['parameter_versions_unchanged']
                key = strategy + ':' + request['sample_name'] + ':' + row['collect']
                bind('tensor', key, row['vector_artifact']); bind('video', key, row['video_artifact'])
                actual = next(v for v in audit['files'] if v['path'] == artifact_path_bindings['tensor:'+key]['resolved_path'])
                assert actual['bytes'] == row['vector_artifact']['bytes'] and actual['sha256'] == row['vector_artifact']['sha256']
                checks = {'complete36_guided':len(row['guided_sha256']) == 36,
                    'same_prepared_call_arguments':entry.get('request') == ref['prepared_input_calls'][0]['request'],
                    'same_prepared_data':entry.get('prepared') == ref['prepared_input_calls'][0]['prepared'],
                    'same_condition_fields_before':row.get('condition_fields_before') == ref['condition_fields_before'],
                    'same_condition_fields_after':row.get('condition_fields_after') == ref['condition_fields_after'],
                    'same_conditions_before':row.get('conditions_before') == ref['conditions_before'],
                    'same_conditions_after':row.get('conditions_after') == ref['conditions_after'],
                    'same_actual_solver_configuration':row.get('actual_raw_solver_configuration') == ref['actual_raw_solver_configuration'],
                    'same_first_seven_dense_guided':row['guided_sha256'][:7] == ref['guided_sha256'][:7]}
                slot = next(s for s in slots if (s['strategy'],s['sample_name'],s['method']) == (strategy,request['sample_name'],row['collect']))
                assert slot['checks'] == checks and slot['compatible'] == all(checks.values())
                assert slot['incompatible_fields'] == [k for k,v in checks.items() if not v]
                assert slot['video_artifact'] == row['video_artifact'] and slot['Native_artifact'] == ref['artifact']
                d = row['collection_complete'].get('deployment')
                if d is not None:
                    assert d['working_epoch_strategy'] == strategy and not d['P_future_drift_empirically_calibrated']
                    assert len(d['history']) == len(d['source_policy_history']) == 36
                    assert [h['action'] for h in d['history']] == row['actions']
                    assert not d['fixed_schedule_used_for_dynamic_choice'] and d['teacher_calls'] == 0
                    for h in d['history']:
                        p = h['source_policy']; decision = p['decision']; action = h['action']
                        assert decision['action']*2 == action and decision['step'] == h['step']
                        if action != 'DD': assert h['true_D_before'] == h['true_D_after']
                        if action == 'PP':
                            assert decision['predicted_creation_floor'] > 0 and decision['added_risk'] == decision['gain']*decision['predicted_creation_floor']
                            assert p['creation_floor_proxy_after'] > 0 and p['dense_anchor_after'] == decision['state_before'][0]
                            expected = decision['state_before'][4]+decision['added_risk'] if strategy == STRATEGIES[0] else decision['added_risk']
                            assert p['accumulated_interval_proxy_after'] == expected and expected > 0
                            assert all(v['kind'] == 'P' and not v['RA_zero_risk_reset_allowed'] for v in h['working_sources'])
                        elif action == 'CC':
                            assert decision['added_risk'] == decision['gain']*(decision['state_before'][3]+decision['local_proxy'])
                        else:
                            assert p['creation_floor_proxy_after'] == p['accumulated_interval_proxy_after'] == 0 and p['dense_anchor_after'] == h['step']
    for ref in refs: bind('Native_video', ref['sample_name'], ref['artifact'])
    return {'native_accounting_and_complete_scope_verified': True, 'success': True,
        'complete64_method_paths_and_four_original_reference_slots_reconstructed': True,
        'actual_all_guided_tensors_server_reloaded':2304,'actual_all_final_latents_server_reloaded':64,
        'actual_new_videos_rechecked':64,'original_Native_videos_rechecked':4,
        'all64_costs_and_pairing_checks_independently_reconstructed':True,
        'compatible_pairs':raw['compatible_pairs'],'incompatible_pairs_retained':raw['incompatible_pairs'],
        'actual_alias_path_bytes_and_sha_bindings_verified':len(artifact_path_bindings),
        'local_second_tensor_loading':False,'endpoint_quality_scoring_pending':True,'clean_latency_claim':False}


def main():
    if not LAUNCH.exists():
        print(json.dumps({'status':'WAIT_ORIGINAL_FULL64_LAUNCH_NO_CAPTURE_WRITTEN','GPU_submissions':0}));return 2
    reg=json.loads(SOURCE_REG.read_text())
    assert {n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in reg['source_sha256']}==reg['source_sha256']
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
assert sha(stage/'current-birth-full64-config.json')==L['config_sha256'] and sha(post/'driver.py')==L['post_driver_sha256']
c=json.loads((stage/'current-birth-full64-config.json').read_text());payload={n:sha(stage/n) for n in c['payload_sha256']}
assert payload==c['payload_sha256']==cpu['payload_after_sha256'] and len(payload)==L['payload_files']
assert {n:sha(root/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
budget=json.loads((root/'reports/budget.json').read_text())
assert budget==gpu['budget_after'] and not any('inflight' in k for k in budget)
assert gpu['budget_before']==L['budget_before'] and budget['cap_gpu_hours']==77.89524658965853 and budget['gpu_jobs_launched']==L['budget_before']['gpu_jobs_launched']+1
assert math.isclose(budget['used_gpu_hours'],L['budget_before']['used_gpu_hours']+gpu['wall_seconds']/3600,abs_tol=1e-12)
# Capture the original failure as well when another owner's process appears
# after our empty-GPU admission. Its context is not our unreleased runner.
assert gpu['child_pid'] not in gpu['release'].get('pids',[])
with (root/'.sync/f1.lock').open('r') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
observation=subprocess.check_output(['nvidia-smi','-i',c['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip()
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
assert not any(x.split(',')[0].strip()==c['gpu_uuid'] and int(x.split(',')[1])==gpu['child_pid'] for x in apps.splitlines())
success=gpu.get('exit_code')==cpu.get('exit_code')==0
if success:
 assert cpu['status']=='CURRENT_BIRTH_FULL64_COMPLETE_CPU_AUDIT_NOT_FIDELITY_SCORE' and cpu['child_exit_code']==0
 assert sha(post/'result.json')==cpu['result_sha256']
 assert cpu['budget_before_sha256']==cpu['budget_after_sha256']==sha(root/'reports/budget.json')
 result=json.loads((post/'result.json').read_text())
 assert result['runner_sha256']==sha(out/'diagnostic/receipt.json') and result['planned_scope']==L['planned_scope']
bindings={}
if success:
 runner=json.loads((out/'diagnostic/receipt.json').read_text())
 for strategy in c['preregistration']['strategies']:
  for request in runner['batches'][strategy]['requests']:
   for row in request['paths']:
    label=strategy+':'+request['sample_name']+':'+row['collect']
    for kind,key in [('tensor','vector_artifact'),('video','video_artifact')]:
     art=row[key];path=pathlib.Path(art['path']).resolve()
     assert path.is_relative_to((out/'diagnostic'/strategy).resolve())
     assert path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
     bindings[kind+':'+label]={'recorded_path':art['path'],'resolved_path':str(path),'bytes':art['bytes'],'sha256':art['sha256']}
 for ref in runner['matched_Native_metadata']:
  art=ref['artifact'];path=pathlib.Path(art['path']).resolve()
  assert path.is_relative_to((root/'outputs').resolve()) and path.stat().st_size==art['bytes'] and sha(path)==art['sha256']
  bindings['Native_video:'+ref['sample_name']]={'recorded_path':art['path'],'resolved_path':str(path),'bytes':art['bytes'],'sha256':art['sha256']}
files={'supervisor':out/'supervisor.json','CPU_receipt':post/'receipt.json','CPU_driver':post/'driver.py','CPU_driver_log':post/'driver.log','GPU_supervisor_log':post/'GPU-supervisor.log','GPU_log':out/'run.log','GPU_monitor':out/'gpu-monitor.jsonl','budget':root/'reports/budget.json','config':stage/'current-birth-full64-config.json','launch':post/'launch.json'}
for key,path in [('runner',out/'diagnostic/receipt.json'),('CPU_result',post/'result.json'),('CPU_log',post/'CPU-audit.log')]:
 if path.exists():files[key]=path
if c['single_job_exception_authority'] is not None:
 authority=c['single_job_exception_authority'];assert sha(stage/authority['ref'])==authority['sha256']
 files['single_job_exception_authority']=stage/authority['ref']
native={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
capture={'status':'CURRENT_BIRTH_FULL64_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS' if success else 'CURRENT_BIRTH_FULL64_ORIGINAL_TERMINAL_FAILURE_COMPLETE_SCOPE_RETAINED','observed_unix':time.time(),'run_id':L['run_id'],'source_revision':L['source_revision'],'original_PIDs_absent':[p for p in pids if p],'GPU_exit_code':gpu.get('exit_code'),'CPU_exit_code':cpu.get('exit_code'),'planned_scope':L['planned_scope'],'config_sha256':L['config_sha256'],'payload_after_sha256':payload,'post_driver_sha256':sha(post/'driver.py'),'lock_released':True,'GPU_observation':observation,'compute_apps':apps,'budget_settled':budget,'actual_GPU_wall_seconds':gpu['wall_seconds'],'GPU_submissions_by_capture':0,'artifact_path_bindings':bindings}
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
    proof['independent_capture_source_preregistration_sha256']=hashlib.sha256(SOURCE_REG.read_bytes()).hexdigest()
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
    target.write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({k: v for k, v in proof.items() if k not in ('files', 'payload_after_sha256', 'budget_settled')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
