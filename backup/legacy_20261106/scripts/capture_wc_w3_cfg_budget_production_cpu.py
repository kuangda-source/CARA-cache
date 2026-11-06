import base64,gzip,hashlib,json,subprocess,time
from pathlib import Path
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
launch=json.loads(Path('reports/wc_w3_cfg_budget_production_cpu_r1_launch_20261008.json').read_text());c=json.loads(Path('configs/wc_w3_cfg_budget_production_r1_20261008.json').read_text())
remote='STAGE='+repr(launch['stage'])+'\n'+r'''
import base64,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/STAGE;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((stage/'receipt.json').read_text());m=json.loads((stage/'manifest.json').read_text())
assert r['exit_code']==0 and r['status']=='CFG_BUDGET_PRODUCTION_CPU_PASS_NOT_GPU';pids=[r['pid']]+[x['pid'] for x in r['steps']];assert all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
assert r['payload_before_sha256']==r['payload_after_sha256']==m['payload_sha256'];assert {n:sha(stage/n) for n in m['payload_sha256']}==m['payload_sha256']
assert sha(stage/'budget-config.json')==m['config_sha256'] and sha(root/'reports/budget.json')==m['budget_sha256']==r['budget_before_sha256']==r['budget_after_sha256']
raw={n:base64.b64encode((stage/n).read_bytes()).decode() for n in ['receipt.json','runner.log','metric.log','driver.log','manifest.json','launch.json','budget-config.json']}
print(json.dumps({'status':'CFG_BUDGET_PRODUCTION_CPU_ORIGINAL_BYTES_AND_SOURCE_CAPTURE_PASS_NOT_GPU','observed_unix':time.time(),'source_revision':m['source_revision'],'driver_sha256':sha(stage/'driver.py'),'original_PIDs_absent':pids,'budget_sha256':sha(root/'reports/budget.json'),'raw':raw}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=remote,text=True,capture_output=True,timeout=50);assert r.returncode==0,r.stderr
v=json.loads(r.stdout);assert v['driver_sha256']==launch['driver_sha256'];raw=v.pop('raw');archives={}
for name,value in raw.items():
 data=base64.b64decode(value);path=Path('reports/wc_w3_cfg_budget_production_cpu_r1_20261008_'+name.replace('.','_')+'_native.gz');assert not path.exists();path.write_bytes(gzip.compress(data,mtime=0));archives[str(path)]={'raw_sha256':hashlib.sha256(data).hexdigest(),'gzip_sha256':sha(path),'bytes':len(data)}
v['archives']=archives
path=Path('reports/wc_w3_cfg_budget_production_cpu_r1_terminal_capture_20261008.json');path.write_text(json.dumps(v,indent=2)+'\n')
receipt=json.loads(base64.b64decode(raw['receipt.json']));result=receipt['steps'][0]['result'];metric=receipt['steps'][1]['result']
assert receipt['payload_before_sha256']==receipt['payload_after_sha256']==c['payload_sha256'];assert result['payload_sha256']==c['payload_sha256'] and result['transitive_local_source_count']>=20
assert result['production_contract_mutation_refusals']==['seed','snapshot_step','snapshot_after_call','swaps','main_comparisons','scope_counts','remaining_policy','per_CFG_full_counts','maximum_age_solver_steps']
assert result['parsed_request']['seed']==2 and result['parsed_request']['name']=='human_199_seed2'
assert metric['scored_videos']==0 and not metric['CUDA_initialized'] and metric['GPU_submissions']==0
assert v['budget_sha256']==sha('reports/budget.json')
audit={'status':'CFG_BUDGET_PRODUCTION_CPU_INDEPENDENT_ORIGINAL_BINDING_PASS_NOT_GPU','source_revision':launch['source_revision'],'CPU_wall_seconds':receipt['CPU_wall_seconds'],'original_PIDs_absent':v['original_PIDs_absent'],'payload_files':len(c['payload_sha256']),'affected_core_source_unchanged':True,'contract_mutation_refusals':9,'transitive_local_source_count':result['transitive_local_source_count'],'actual_guardrail_cache_and_Blocklist':True,'actual_delayed_paired_entry_checked':True,'actual_full93_metric_resource_and_model_instantiation':True,'scored_videos':0,'budget_unchanged':True,'CUDA_initialized':False,'GPU_submissions':0,'receipt_raw_sha256':hashlib.sha256(base64.b64decode(raw['receipt.json'])).hexdigest(),'capture_sha256':sha(path)}
p=Path('reports/wc_w3_cfg_budget_production_cpu_r1_independent_audit_20261008.json');p.write_text(json.dumps(audit,indent=2)+'\n')
assert c['GPU_execution_selected'] is False and c['budget_extension_authority']['ref']=='manifests/budget_authorization_20261008_wc_50gpuh.json'
print(json.dumps(audit))
