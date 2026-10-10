#!/usr/bin/env python3
"""Read the original completed GPU/CPU handles and preserve complete native evidence.

No dispatch, remote writes, tensor loading, source changes or acceptance of a subset.
"""
import base64
import argparse
import ast
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess


LAUNCH = Path('reports/wc_action_cost_real_r1_GPU_launch_20261010.json')
PREFIX = 'reports/wc_action_cost_real_r1_terminal_20261010_'


def same_registered_moments(x,y):
    # The deployed raw tensor auditor has always used these FP64 reduction
    # tolerances. Tensor bytes/hashes and all nonnumeric metadata remain exact.
    if isinstance(x,dict):return x.keys()==y.keys() and all(same_registered_moments(x[k],y[k]) for k in x)
    if isinstance(x,list):return len(x)==len(y) and all(same_registered_moments(a,b) for a,b in zip(x,y))
    if type(x) is float:return isinstance(y,(int,float)) and math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12)
    return x==y


def independent_native_check(launch,objects,artifact_path_bindings):
    c,gpu,cpu=(objects[k] for k in ('config','supervisor','CPU_receipt'));budget=objects['budget']
    assert gpu['budget_before']==launch['budget_before'] and budget==gpu['budget_after']
    assert not any('inflight' in k for k in budget) and budget['cap_gpu_hours']==77.89524658965853
    assert math.isclose(budget['used_gpu_hours'],launch['budget_before']['used_gpu_hours']+gpu['wall_seconds']/3600,abs_tol=1e-12)
    assert budget['gpu_jobs_launched']==launch['budget_before']['gpu_jobs_launched']+1
    assert not gpu['legacy_seconds_deadline_active'] and c['preregistration']['scope_counts']==launch['planned_scope']
    if gpu.get('exit_code')!=0 or cpu.get('exit_code')!=0:
        return {'native_accounting_and_complete_scope_verified':True,'success':False}
    result,runner=objects['CPU_result'],objects['runner'];state=runner['batch'];raw=result['actual_tensor_audit']
    assert result['status']=='REAL_ACTION_COST_GROUP_FULL_RAW_CPU_AUDIT_NOT_POLICY_QUALITY'
    assert runner['status']=='REAL_ACTION_COST_GROUP_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    assert runner['config']==c and result['run_id']==runner['run_id']==launch['run_id']
    assert result['source_revision']==runner['source_revision']==launch['source_revision']
    assert (raw['actual_parent_guided_reloaded'],raw['actual_parent_latents_reloaded'],raw['actual_post_RF_branch_tensors_reloaded'])==(288,8,112)
    assert raw['actual_full36_OFF_ON_direct_equal'] and raw['actual_original_CFG_recovery_direct_equal'] and raw['actual_full_D_control_direct_equal']
    assert result['all_8_full93_videos_and_16_raw_vector_artifacts_verified']
    assert not result['CUDA_initialized'] and result['GPU_submissions']==0 and not result['new_policy_or_video_quality_or_clean_latency_claim']
    assert state['planned_parent_paths']==state['planned_origins']==8 and len(state['requests'])==4
    assert state['initial_state_restored'] and state['video_quality_labels']==state['future_time_labels']==0
    modes=['C','A_W1_ONE_PHASE','A_BETA1_ONE_PHASE','ROTATION_050','DENSE_REFERENCE','DENSE_WITH_P0']
    methods=['ORIGINAL']+modes
    parity=('guided_sha256','guided_list_sha256','solver_returns','actions','counters','checkpoints','conditions_before','conditions_after','rng_after','flags_before','flags_after','own_history','own_fingerprint','final_latent_sha256','pipeline','sample_return_sha256','condition_fields_before','condition_fields_after','actual_condition_masks','actual_raw_solver_configuration')
    parents=origins=0;moments={k:[] for k in modes};costs=[];dense=list(range(1,8))+[13,19,25,31,36]
    def bind(kind,label,art,items):
        alias=artifact_path_bindings[kind+':'+label];item=next(x for x in items if x['path']==alias['resolved_path'])
        assert item['sha256']==art['sha256']==alias['sha256'] and item['bytes']==art['bytes']==alias['bytes']
        assert alias['recorded_path']==art['path']
    for request in state['requests']:
        rows=request['paths'];assert len(rows)==2 and [r['collect'] for r in rows]==[False,True]
        assert request['prepared_input_calls'][0]['prepared']==request['prepared_input_calls'][1]['prepared']
        for row in rows:
            parents+=1
            assert row['status']=='COMPLETE_PARENT_PATH' and len(row['guided_sha256'])==len(row['solver_returns'])==36
            assert row['counters']==list(range(0,70,2))+[0] and row['actions']==['DD' if t in dense else 'CC' for t in range(1,37)]
            assert [x['step'] for x in row['checkpoints']]==[12,30,35,36] and all(len(x['components'])==1216 for x in row['checkpoints'])
            assert all(row[k]==rows[0][k] for k in parity)
            assert row['conditions_before']==row['conditions_after'] and row['condition_fields_before']==row['condition_fields_after']
            assert row['parameter_versions_unchanged'] and row['all_modules_eval']
            assert row['vector_artifact']['tensor_sha256']['guided']==row['guided_list_sha256']
            assert row['vector_artifact']['tensor_sha256']['final_latent']==row['final_latent_sha256']
            bind('tensor',row['label'],row['vector_artifact'],raw['files']);bind('video',row['label'],row['video_artifact'],result['videos'])
            assert [o['step'] for o in row['origins']]==([12,30] if row['collect'] else [])
            for o in row['origins']:
                origins+=1;t=o['step'];assert o['scene']==request['sample_name'] and o['action']=='CC'
                assert o['actual_post_RF_original_direct_equal'] and not o['teacher_updates_deployment_anchor']
                assert list(o['velocity_sha256'])==methods and o['methods']==methods
                assert o['past_actual_D_projection_step']==(7 if t==12 else 25)
                assert o['layers']==[4,10,16,22] and o['block_size']==128 and o['actual_probe_shapes']==[[1,24,27,48,2048]]*2
                assert o['full_D_same_origin_direct_equal'] and o['complete_external_and_P0_restored'] and o['warmups']==1 and o['repeats']==3
                assert not o['new_policy_OR_partial_video_OR_clean_end_to_end_latency_claim']
                assert set(o['group_cost_seconds'])==set(modes) and all(len(v)==3 and all(math.isfinite(x) and x>0 for x in v) for v in o['group_cost_seconds'].values())
                for mode in modes:
                    rows0=o['warmup_Linear_and_projection_records'][mode]
                    if mode=='C' or mode.startswith('A_'):
                        assert rows0=={'Linear_inputs':[],'projection_records':[]}
                        assert o['C_recomputed_direct_equal'] and o['cached_readout_source_proof']['cached_body_inverse_AST_equal']
                        assert o['incremental_post_probe_cost_not_full_pair_or_clean_pipeline']
                        if mode=='C':assert o['warmup_actual_output_head_calls'][mode]==2
                        else:
                            read=o['warmup_A_readouts'][mode]
                            assert o['warmup_actual_output_head_calls'][mode]==2+read['extra_heads']
                            assert read['shared_alpha']==(1 if t<25 else .5)
                            assert read['extra_deep_blocks']==read['teacher_calls']==0 and read['post_RF_fusion']
                            assert not read['C_readout_updates_D_anchor']
                            assert all(a<t for branch in read['past_D_steps'] for a in branch)
                    else:
                        n=31104 if mode.startswith('DENSE') else 15488
                        assert len(rows0['Linear_inputs'])==16 and all(r['rows']==n for r in rows0['Linear_inputs'])
                        assert o['warmup_actual_output_head_calls'][mode]==2
                        if mode!='DENSE_REFERENCE':
                            assert len(rows0['projection_records'])==8
                            assert all(r['actual_MLP_rows']==n and not r['fallback'] and r['current_Block_gate_preserved'] and not r['is_WorldCache_D_anchor_or_RA_zero_risk_source'] for r in rows0['projection_records'])
                    moments[mode].append(o['moments'][mode])
                costs.append({'scene':request['sample_name'],'step':t,'costs':o['group_cost_seconds'],'peaks':o['group_peak_bytes'],'warmup_real_Linear_inputs_and_sources':o['warmup_Linear_and_projection_records'],'warmup_actual_output_head_calls':o['warmup_actual_output_head_calls'],'warmup_A_readouts':o['warmup_A_readouts'],'source_exact_C_proof':o['cached_readout_source_proof'],'incremental_post_paid_probe_cost_not_full_pair':o['incremental_post_probe_cost_not_full_pair_or_clean_pipeline']})
                bind('tensor',request['sample_name']+':step'+str(t),o['artifact'],raw['files'])
        group=[v for v in result['videos'] if v['sample_name']==request['sample_name']]
        assert len(group)==2 and all(v['all_frames_shape']==[93,432,768,3] for v in group)
        assert all(v['sha256']==group[0]['sha256'] and v['decoded_RGB_SHA']==group[0]['decoded_RGB_SHA'] for v in group)
    assert (parents,origins)==(8,8) and len(raw['files'])==16 and len(artifact_path_bindings)==25
    assert all(len(v)==8 for v in moments.values()) and same_registered_moments(moments,raw['moments'])
    assert raw['moments']==result['all_modes_direct_guided_moments']
    original_sampling=subprocess.check_output(['git','show',launch['source_revision']+':src/wcomr/partial_mlp_sampling.py'])
    nested=[n for n in ast.walk(ast.parse(original_sampling)) if isinstance(n,ast.FunctionDef) and n.name=='same']
    assert len(nested)==1
    close=[n for n in ast.walk(nested[0]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='isclose']
    assert len(close)==1 and {k.arg:ast.literal_eval(k.value) for k in close[0].keywords}=={'rel_tol':1e-10,'abs_tol':1e-12}
    table=objects['calibration_table'];assert same_registered_moments(table['all_modes_direct_guided_moments'],moments)
    assert table['all_modes_direct_guided_moments']==raw['moments']
    assert table['all_group_cost_seconds']==costs==result['all_group_cost_seconds']
    assert hashlib.sha256(table['fingerprint_context'].encode()).hexdigest()==table['context_sha256']
    assert table['actual_same_state_teacher_and_post_RF_bundles_verified'] and not table['teacher_updates_deployment_anchor']
    return {'native_accounting_and_complete_scope_verified':True,'success':True,'complete_8_parent_8_origin_6_mode_reconstruction':True,'actual_288_guided_8_latent_112_branch_reload_verified':True,'all_real_Linear_rows_source_and_full_group_repetitions_verified':True,'actual_alias_path_bytes_and_sha_bindings_verified':25,'local_second_tensor_loading':False,'new_policy_or_endpoint_or_clean_latency_claim':False}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audit-retained',action='store_true');args=parser.parse_args()
    if not LAUNCH.exists():
        sequence=json.loads(Path('reports/wc_action_cost_real_r1_sequence_launch_20261010.json').read_text())
        code='import pathlib; p=pathlib.Path('+repr(sequence['sequence_stage'])+')/"GPU-launch.json"; print(p.read_text() if p.exists() else "null")'
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,timeout=40)
        assert call.returncode==0,call.stderr
        if call.stdout.strip()=='null':
            print(json.dumps({'status':'ACTION_COST_SEQUENTIAL_WAITER_NOT_GPU_SUBMITTED','GPU_submissions_by_capture':0}));return 2
        actual=json.loads(call.stdout);assert actual['GPU_submissions_by_launch']==1
        assert actual['source_revision']==sequence['source_revision'] and actual['payload_files']==271
        LAUNCH.write_text(json.dumps(actual,indent=2)+'\n')
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
assert sha(stage/'action-cost-config.json')==L['config_sha256'] and sha(post/'driver.py')==L['post_driver_sha256']
c=json.loads((stage/'action-cost-config.json').read_text());payload={n:sha(stage/n) for n in c['payload_sha256']}
assert payload==c['payload_sha256']==cpu['payload_after_sha256'] and len(payload)==L['payload_files']
assert {n:sha(stage/n) for n in L['lifecycle_sha256']}==L['lifecycle_sha256']
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
 assert cpu['status']=='REAL_ACTION_COST_GROUP_COMPLETE_CPU_AUDIT_NOT_POLICY_QUALITY' and cpu['child_exit_code']==0
 assert sha(post/'result.json')==cpu['result_sha256']
 assert cpu['budget_before_sha256']==cpu['budget_after_sha256']==sha(root/'reports/budget.json')
 result=json.loads((post/'result.json').read_text())
 assert result['runner_receipt_sha256']==sha(out/'diagnostic/receipt.json') and result['config_sha256']==L['config_sha256']
bindings={}
if success:
 runner=json.loads((out/'diagnostic/receipt.json').read_text())
 for request in runner['batch']['requests']:
  for row in request['paths']:
   artifacts=[('tensor',row['label'],row['vector_artifact'],result['actual_tensor_audit']['files']),('video',row['label'],row['video_artifact'],result['videos'])]
   artifacts += [('tensor',request['sample_name']+':step'+str(o['step']),o['artifact'],result['actual_tensor_audit']['files']) for o in row['origins']]
   for kind,label,art,items in artifacts:
    path=pathlib.Path(art['path']).resolve();assert path.is_relative_to((out/'diagnostic').resolve())
    item=next(x for x in items if x['path']==str(path))
    assert path.stat().st_size==art['bytes']==item['bytes'] and sha(path)==art['sha256']==item['sha256']
    bindings[kind+':'+label]={'recorded_path':art['path'],'resolved_path':str(path),'bytes':art['bytes'],'sha256':art['sha256']}
 tableart=result['group_mechanism_artifact'];tablepath=pathlib.Path(tableart['path']).resolve()
 assert tablepath.is_relative_to(post.resolve()) and tablepath.stat().st_size==tableart['bytes'] and sha(tablepath)==tableart['sha256']
 bindings['table']={'recorded_path':tableart['path'],'resolved_path':str(tablepath),'bytes':tableart['bytes'],'sha256':tableart['sha256']}
files={'supervisor':out/'supervisor.json','CPU_receipt':post/'receipt.json','CPU_driver':post/'driver.py','CPU_driver_log':post/'driver.log','GPU_supervisor_log':post.parent/'GPU-supervisor.log','GPU_log':out/'run.log','GPU_monitor':out/'gpu-monitor.jsonl','budget':root/'reports/budget.json','config':stage/'action-cost-config.json','launch':post/'launch.json'}
for key,path in [('runner',out/'diagnostic/receipt.json'),('CPU_result',post/'result.json'),('CPU_log',post/'CPU-audit.log'),('calibration_table',post/'action-cost-moments-and-cost.json')]:
 if path.exists():files[key]=path
native={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
capture={'status':'REAL_ACTION_COST_GROUP_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS' if success else 'REAL_ACTION_COST_GROUP_ORIGINAL_TERMINAL_FAILURE_COMPLETE_SCOPE_RETAINED','observed_unix':time.time(),'run_id':L['run_id'],'source_revision':L['source_revision'],'original_PIDs_absent':[p for p in pids if p],'GPU_exit_code':gpu.get('exit_code'),'CPU_exit_code':cpu.get('exit_code'),'planned_scope':L['planned_scope'],'config_sha256':L['config_sha256'],'payload_after_sha256':payload,'post_driver_sha256':sha(post/'driver.py'),'lock_released':True,'GPU_observation':observation,'compute_apps':apps,'budget_settled':budget,'actual_GPU_wall_seconds':gpu['wall_seconds'],'GPU_submissions_by_capture':0,'artifact_path_bindings':bindings}
print(json.dumps({'capture':capture,'native':native}))
'''
    process = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'gkd_minchen', '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'], input=remote, text=True, capture_output=True, timeout=55)
    if process.returncode:
        raise RuntimeError(process.stderr[-5000:])
    value = json.loads(process.stdout)
    if not value['native']:
        print(json.dumps(value['capture']))
        return 2
    original_target=Path(PREFIX+'capture_and_independent_audit.json')
    target = Path(PREFIX + ('capture_reaudit_r3.json' if args.audit_retained else 'capture_and_independent_audit.json'))
    assert not target.exists()
    retained=json.loads(original_target.read_text()) if args.audit_retained else None
    if retained is not None:
        assert retained['GPU_exit_code']==retained['CPU_exit_code']==0
        assert retained['independent_check_failure']['type']=='AssertionError'
        assert retained['artifact_path_bindings']==value['capture']['artifact_path_bindings']
    objects, verified = {}, {}
    for key, item in value['native'].items():
        compressed = base64.b64decode(item['gzip_base64'], validate=True)
        raw = gzip.decompress(compressed)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        assert hashlib.sha256(compressed).hexdigest() == item['compressed_sha256']
        path = Path(PREFIX + key + '_native.gz')
        if retained is None:assert not path.exists()
        else:assert path.read_bytes()==compressed and retained['files'][key]['sha256']==item['sha256']
        verified[key] = (path, compressed, raw)
        if item['path'].endswith('.json'):
            objects[key] = json.loads(raw)
    proof = value['capture']; proof['files'] = {}
    # Save failure/evidence bytes before independent checks; an audit error retains originals.
    for key, (path, compressed, raw) in verified.items():
        if retained is None:path.write_bytes(compressed)
        proof['files'][key] = {k: v for k, v in value['native'][key].items() if k != 'gzip_base64'}
        proof['files'][key]['local_path'] = str(path)
    if retained is not None:
        proof['original_failed_capture_ref']=str(original_target)
        proof['original_failed_capture_sha256']=hashlib.sha256(original_target.read_bytes()).hexdigest()
        proof['original_native_bytes_unchanged']=True
        prior_reaudit=Path(PREFIX+'capture_reaudit.json')
        assert json.loads(prior_reaudit.read_text())['independent_check_failure']['type']=='AssertionError'
        proof['previous_failed_reaudit_ref']=str(prior_reaudit)
        proof['previous_failed_reaudit_sha256']=hashlib.sha256(prior_reaudit.read_bytes()).hexdigest()
        proof['repair_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        proof['unchanged_deployed_FP64_moment_tolerance']={'rel_tol':1e-10,'abs_tol':1e-12}
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
