#!/usr/bin/env python3
"""Capture exact original terminal artifacts through existing SSH; refuses incomplete runs.
No new GPU submission or restart. Run from project root after bound scoring ends.
"""
import base64,gzip,hashlib,json,subprocess
from pathlib import Path
L=json.loads(Path('reports/wc_w3_cfg_budget_gpu_r1_launch_20261009.json').read_text());P=json.loads(Path('reports/wc_w3_cfg_budget_post_cpu_r1_launch_20261009.json').read_text())
remote='L='+repr(L)+'\nP='+repr(P)+'\n'+r'''
import base64,fcntl,gzip,hashlib,json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/L['stage'];post=root/P['stage'];run=root/'outputs'/L['run_id'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=json.loads((stage/'budget-config.json').read_text());sup=json.loads((run/'supervisor.json').read_text());receipt=json.loads((post/'receipt.json').read_text());score=json.loads((post/'score.json').read_text());pids=[sup['pid'],sup['child_pid'],receipt['pid'],receipt['score_pid']]
assert sup['exit_code']==receipt['exit_code']==0 and sup['source_revision']==receipt['source_revision']==L['source_revision'];assert all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
assert sha(post/'score.json')==receipt['score_sha256'];assert sha(stage/'budget-config.json')==L['config_sha256'];payload={n:sha(stage/n) for n in c['payload_sha256']};assert payload==receipt['payload_after_sha256']==c['payload_sha256'];assert sha(post/'driver.py')==P['driver_sha256'] and sha(post/'binding.json')==P['binding_sha256'];assert sha(stage/c['budget_extension_authority']['ref'])==c['budget_extension_authority']['sha256']
assert sha(stage/c['single_job_exception_authority']['ref'])==c['single_job_exception_authority']['sha256']
assert score['same_per_CFG_computation_quota']==[18,17] and score['all_cells_whole_full_calls']==35
budget=json.loads((root/'reports/budget.json').read_text());assert budget==sup['budget_after']==receipt['budget_at_end'] and not any('inflight' in k for k in budget)
lock=(root/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
gpu=subprocess.check_output(['nvidia-smi','-i',c['gpu_uuid'],'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True).strip();apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip()
files={'runner':run/'diagnostic/receipt.json','supervisor':run/'supervisor.json','CPU_receipt':post/'receipt.json','CPU_score':post/'score.json','CPU_score_log':post/'score.log','CPU_driver_log':post/'driver.log','GPU_log':run/'run.log','GPU_monitor':run/'gpu-monitor.jsonl','budget':root/'reports/budget.json'}
items={}
for key,path in files.items():
 raw=path.read_bytes();compressed=gzip.compress(raw,mtime=0);items[key]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'gzip_base64':base64.b64encode(compressed).decode()}
r={'status':'CFG_BUDGET_ORIGINAL_GPU_AND_FULL93_CPU_TERMINAL_NATIVE_CAPTURE_PASS','observed_unix':time.time(),'source_revision':L['source_revision'],'run_id':L['run_id'],'original_PIDs_absent':pids,'GPU_exit_code':sup['exit_code'],'CPU_exit_code':receipt['exit_code'],'score_status':score['status'],'payload_after_sha256':payload,'authorization_sha256':c['budget_extension_authority']['sha256'],'single_job_authority_sha256':c['single_job_exception_authority']['sha256'],'post_driver_sha256':sha(post/'driver.py'),'post_binding_sha256':sha(post/'binding.json'),'lock_released':True,'GPU_observation':gpu,'compute_apps':apps,'budget_settled':budget,'actual_GPU_wall_seconds':sup['wall_seconds'],'CPU_total_wait_and_wall_seconds':receipt['total_wait_and_CPU_wall_seconds'],'CUDA_initialized_in_score':score['CUDA_initialized'],'GPU_submissions_by_capture':0};print(json.dumps({'capture':r,'native':items}))
'''
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=remote,text=True,capture_output=True,timeout=50);assert r.returncode==0,r.stderr;v=json.loads(r.stdout)
prefix='reports/wc_w3_cfg_budget_complete_r1_20261009_';capture=v['capture'];capture['files']={}
for key,item in v['native'].items():
 data=base64.b64decode(item['gzip_base64']);assert hashlib.sha256(data).hexdigest()==item['compressed_sha256'];raw=gzip.decompress(data);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'];dest=Path(prefix+key+'_native.gz');assert not dest.exists();dest.write_bytes(data);capture['files'][key]={k:val for k,val in item.items() if k!='gzip_base64'};capture['files'][key]['local_path']=str(dest)
 if key=='budget':Path('reports/budget.json').write_bytes(raw)
p=Path('reports/wc_w3_cfg_budget_complete_r1_terminal_capture_20261009.json');assert not p.exists();p.write_text(json.dumps(capture,indent=2)+'\n')
score=json.loads(gzip.decompress(Path(prefix+'CPU_score_native.gz').read_bytes()));print(json.dumps({'status':capture['status'],'original_PIDs_absent':capture['original_PIDs_absent'],'actual_GPU_wall_seconds':capture['actual_GPU_wall_seconds'],'GPU_observation':capture['GPU_observation'],'cap_GPUh':capture['budget_settled']['cap_gpu_hours'],'used_GPUh':capture['budget_settled']['used_gpu_hours'],'scope':score['planned_scope'],'verdict':score['verdict'],'cell_mean_LPIPS':{k:val['mean_LPIPS'] for k,val in score['losses'].items()},'factorial_summary':score['factorial_summary']}))
