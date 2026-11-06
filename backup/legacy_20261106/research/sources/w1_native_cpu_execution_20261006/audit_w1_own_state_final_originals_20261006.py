"""Read-only receipt/hash/expense audit and same-video endpoint join."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

read=lambda path:json.loads(Path(path).read_text())
m=read('manifests/wc_w1_own_state_execution_20261006.json')
dispatch=read('reports/wc_w1_own_state_dispatch_20261006.json')
cpu=read('reports/wc_w1_own_state_terminal_and_summary_cpu_r1_20261006.json')
original_cpu={k:v for k,v in cpu.items() if k not in ['CPU_receipt_original_sha256','executed_CPU_wrapper_sha256']}
originals={name:read('reports/'+name) for name in ['wc_w1_own_state_supervisor_20261006.json',
 'wc_w1_own_state_runner_20261006.json','wc_w1_own_state_signed_summary_cpu_r1_20261006.json','budget.json']}
endpoints=read('reports/wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json')
tree=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)
 and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
remote=('M='+repr(m)+'\nSOURCE='+repr(dispatch['source_revision'])+'\nCPU='+repr(original_cpu)
 +'\nCPU_SHA='+repr(cpu['CPU_receipt_original_sha256'])+'\nORIGINALS='+repr(originals)
 +'\nENDPOINTS='+repr(endpoints)+'\n'+r'''
import fcntl,hashlib,json,math,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/M['stage'];output=root/'outputs/wc-w1-own-state-shadow-r1'
checked=[]
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as file:
  for chunk in iter(lambda:file.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def check(path,digest):
 assert sha(path)==digest,str(path);checked.append({'path':str(path),'sha256':digest})
def original(path,name):
 value=json.loads(path.read_text());assert value==ORIGINALS[name],str(path)
 checked.append({'path':str(path),'sha256':sha(path)});return value
for directory,files in [(stage,M['payload_sha256']),(root/M['base_stage'],M['base_payload_sha256'])]:
 for name,digest in files.items():check(directory/name,digest)
check(root/M['base_stage']/'receipt.json',M['base_original_receipt_sha256'])
check(stage/'terminal-and-summary-cpu-receipt.json',CPU_SHA)
assert json.loads((stage/'terminal-and-summary-cpu-receipt.json').read_text())==CPU
sup=original(output/'supervisor.json','wc_w1_own_state_supervisor_20261006.json')
rec=original(output/'diagnostic/receipt.json','wc_w1_own_state_runner_20261006.json')
budget=original(root/'reports/budget.json','budget.json')
summary=json.loads((stage/'terminal-and-summary-cpu.log').read_text().strip().splitlines()[-1])
assert summary==ORIGINALS['wc_w1_own_state_signed_summary_cpu_r1_20261006.json']==CPU['result']
check(output/'supervisor.json',CPU['supervisor_receipt_sha256']);check(output/'diagnostic/receipt.json',CPU['runner_receipt_sha256'])
check(stage/'terminal-and-summary-cpu.log',CPU['result_log_sha256']);check(stage/'terminal-and-summary-cpu.err',CPU['error_log_sha256'])
assert sup['source_revision']==rec['source_revision']==SOURCE and sup['exit_code']==CPU['exit_code']==0
assert sup['reserved_seconds']==1800 and 0<sup['wall_seconds']<=1800 and not sup['hard_wall_cap_exceeded']
assert sup['config']==rec['scope']==json.loads((stage/'own-state-config.json').read_text())
assert sup['budget_after']==budget and budget['cap_gpu_hours']==24 and budget['gpu_jobs_launched']==49
assert budget['used_gpu_hours']==sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600
assert not any(k.endswith('_inflight') for k in budget)
assert summary['status']=='COMPLETE_THREE_SCENE_DIAGNOSTIC' and summary['valid_scene_count']==3
assert summary['terminal']['status']=='OWN_STATE_FULL_TERMINAL_AUDIT_PASS' and summary['terminal']['observations']==12
assert summary['CUDA_initialized'] is False and summary['historical_endpoint_reused_only_after_exact_video_bridge']
assert not summary['independent_confirmation'] and not summary['formal_W3_training_labels'] and not summary['quality_or_clean_speed_decision']
pids=[sup['pid'],sup['child_pid'],rec['pid'],CPU['CPU_supervisor_PID'],CPU['CPU_child_PID']]
assert len(set(pids))==5 and all(not pathlib.Path('/proc/'+str(p)).exists() for p in pids)
with (root/'.sync/f1.lock').open('r') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
joined=[]
for case,row in zip(rec['cases'],summary['rows']):
 assert case['bridge_pass'] and row['name']==case['name'] and case['status']=='HISTORICAL_OFF_BRIDGE_AND_OBSERVATIONS_PASS'
 obs=case['observed'];records=obs['shadow_records'];assert [r['call'] for r in records]==[45,46,67,68]
 check(obs['video_path'],obs['video_sha256']);assert len(obs['decoded_rgb'])==93
 for kind,error in row['errors'].items():
  a=[r['candidates']['official'][kind]['mse'] for r in records];b=[r['candidates']['scalar'][kind]['mse'] for r in records]
  assert all(math.isfinite(v) for v in a+b)
  assert error['official_mean_MSE']==sum(a)/4 and error['scalar_mean_MSE']==sum(b)/4
  assert error['official_minus_scalar']==sum(a)/4-sum(b)/4
  assert error['individual_signed_deltas']==[x-y for x,y in zip(a,b)]
 endpoint=next(v for v in ENDPOINTS['summary']['per_scene'] if v['scene']==case['name'])
 pair=next(v for v in ENDPOINTS['pairs'] if v['scene']==case['name'] and v['method']=='W1_scalar')
 assert pair['candidate']['sha256']==obs['video_sha256'] and pair['score']['mean_LPIPS']==endpoint['W1_LPIPS']
 check(pair['candidate']['path'],pair['candidate']['sha256']);check(pair['reference']['path'],pair['reference']['sha256'])
 joined.append({'scene':case['name'],'same_video_sha256':obs['video_sha256'],'own_state_errors':row['errors'],
  'existing_endpoint':endpoint,'existing_endpoint_reused_not_new_LPIPS_score':True})
monitor=[json.loads(line) for line in (output/'gpu-monitor.jsonl').read_text().splitlines()]
assert monitor and all(v['uuid']==M['gpu_uuid'] and set(v['pids']).issubset(pids[:3]) for v in monitor)
assert not sup['release']['pids'] and sup['release']['uuid']==M['gpu_uuid'] and sup['release']['memory_used_mib']<=1024
logs=[]
for path in [output/'own-state.log',output/'gpu-monitor.jsonl',stage/'supervisor-launch.log',
 stage/'terminal-and-summary-cpu-start.json',stage/'terminal-and-summary-cpu-handle.json']:
 logs.append({'path':str(path),'sha256':sha(path)})
result={'status':'OWN_STATE_NATIVE_SOURCE_COST_HANDLES_SIGNED_JOIN_AUDIT_PASS_NOT_CONF','observed_unix':time.time(),
 'GPU_source_revision':SOURCE,'checked_native_SHA256_count':len(checked),'checked_native_SHA256':checked,
 'original_logs_and_handles_SHA256':logs,'original_handles_exited':pids,'global_lock_free':True,
 'budget':budget,'budget_sha256':sha(root/'reports/budget.json'),'GPU_wall_seconds':sup['wall_seconds'],
 'GPU_charge_hours':sup['wall_seconds']/3600,'CPU_original_receipt_sha256':CPU_SHA,'joined_rows':joined,
 'three_exposed_CAL_scenes_not_CONF':True,'twelve_observations_not_independent_videos':True,
 'W3_B_not_automatically_authorized_or_launched':not (root/'outputs/wc-w3-placement-swap-r1').exists(),
 'new_GPU_submissions':0,'no_Torch_import_or_GPU_query_in_auditor':True}
print(json.dumps(result))
''')
ast.parse(remote)
p=subprocess.run(ssh+['python3 -u -'],input=remote,text=True,capture_output=True,timeout=60)
assert p.returncode==0,p.stderr[-5000:]
value=json.loads(p.stdout)
value['executed_audit_wrapper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
target=Path('reports/wc_w1_own_state_final_original_native_audit_20261006.json')
assert not target.exists(),'Preserve original independent audit'
target.write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:value[k] for k in ['status','checked_native_SHA256_count','original_handles_exited','GPU_wall_seconds','GPU_charge_hours','budget_sha256']}))
