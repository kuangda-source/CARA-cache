import ast,json,subprocess
from pathlib import Path
entry=ast.parse(Path('.sync/observe_wc_fair_cal_r1.py').read_text())
ssh=ast.literal_eval(next(n.value for n in entry.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ssh' for t in n.targets)))
remote=r'''
import json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-w1-native-reference-gpu-r1-20261006';output=root/'outputs/wc-w1-native-reference-cal8-r1'
handle=json.loads((stage/'supervisor-handle.json').read_text())
def read(path):return json.loads(path.read_text()) if path.exists() else None
sup=read(output/'supervisor.json');rec=read(output/'diagnostic/receipt.json')
pids=[handle['supervisor_pid']]
if sup and sup.get('child_pid'):pids.append(sup['child_pid'])
if rec and rec.get('pid'):pids.append(rec['pid'])
def tail(path,length=3000):
 if not path.exists():return ''
 with path.open('rb') as file:
  file.seek(max(0,path.stat().st_size-length));return file.read().decode(errors='replace')
result={'status':'READONLY_OBSERVATION_ORIGINAL_APPROVED_W1_RUN','observed_unix':time.time(),
 'source_revision':handle['source_revision'],'original_pids':[{'pid':p,'exists_now':pathlib.Path('/proc/'+str(p)).exists()} for p in pids],
 'supervisor':{k:v for k,v in (sup or {}).items() if k in ['status','pid','child_pid','child_started_unix','exit_code','wall_seconds','stop_reason','error','settlement_error','hard_wall_cap_exceeded','ended_unix']},
 'runner':{k:v for k,v in (rec or {}).items() if k in ['status','pid','started_unix','ended_unix','load_seconds','CUDA_initialized','accepted_references','rejected_references','error_type','error','cleanup_error']},
 'cases':[{k:v for k,v in case.items() if k in ['sample_name','original_CAL_index','status','outcome','CFG_calls','solver_steps','prepare_calls','pipeline_wall_seconds','block_counts','artifact','error_type','error']} for case in (rec or {}).get('cases',[])],
 'budget':read(root/'reports/budget.json'),'monitor_tail':tail(output/'gpu-monitor.jsonl',1500),
 'generation_log_tail':tail(output/'native-reference.log'), 'supervisor_launch_log_tail':tail(stage/'supervisor-launch.log',700),
 'GPU_submissions':0,'remote_writes':0}
try:
 result['actual_gpu']=subprocess.check_output(['nvidia-smi','-i',handle['gpu_uuid'],'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=5).strip()
 result['actual_compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=5).strip().splitlines()
except Exception as error:result['GPU_observation_error']=str(error)
print(json.dumps(result))
'''
r=subprocess.run(ssh+['python3 -u -'],input=remote,text=True,capture_output=True,timeout=30)
assert r.returncode==0,r.stderr[-3000:]
v=json.loads(r.stdout)
Path('.sync/w1-native-reference-original-observation-latest-20261006.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(v))
