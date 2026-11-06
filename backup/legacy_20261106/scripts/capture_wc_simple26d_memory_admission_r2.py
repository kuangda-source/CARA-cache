#!/usr/bin/env python3
"""One resource/admission identity observation, without reading scientific progress."""
import argparse,json,shlex,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 launch=json.loads((ROOT/'reports/wc_simple26d_memory_full36_GPU_launch_20261015.json').read_text())['dispatch']
 code='LAUNCH='+repr(launch)+'\n'+r'''
import json,pathlib,sys,time,subprocess
s=pathlib.Path(LAUNCH['stage']);r=s.parents[1];sys.path.insert(0,str(s/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity,BudgetPool,sha
v=dict(observed_unix=time.time(),launch=LAUNCH,registration_sha256=sha(s/'registration.json'),processes={k:process_identity(LAUNCH[k]) for k in ('supervisor_pid','post_watcher_pid')},pool=BudgetPool(r).read(),scientific_runner_or_partial_outputs_read=False)
p=r/'outputs'/LAUNCH['run_id']/'supervisor.json'
if p.exists():
 v['supervisor']=json.loads(p.read_text());v['supervisor_sha256']=sha(p)
 if v['supervisor'].get('child_pid'):v['child_identity']=process_identity(v['supervisor']['child_pid'])
else:v['supervisor_log_tail']=(s/'supervisor.log').read_text(errors='replace')[-6000:]
v['own_GPU']=subprocess.check_output(['nvidia-smi','-i',LAUNCH['gpu_uuid'],'--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
print(json.dumps(v))
'''
 result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,text=True,timeout=120)
 assert result.returncode==0,result.stderr
 value=json.loads(result.stdout);a.output.write_text(json.dumps(value,indent=2)+'\n')
 sup=value.get('supervisor');assert sup is not None,value.get('supervisor_log_tail')
 assert sup['status']=='SIMPLE26D_GPU_RUNNING' and sup['source_revision']==launch['source_revision'] and sup['launch_id']==launch['launch_id']
 assert sup['pid']==launch['supervisor_pid'] and sup['gpu_uuid']==launch['gpu_uuid']
 assert value['registration_sha256']==launch['registration_sha256']
 assert value['child_identity']['pid']==sup['child_pid'] and value['child_identity']['state'] not in (None,'Z','X')
 assert value['child_identity']['start_ticks']==sup['child_identity']['start_ticks']
 job=value['pool']['jobs'][launch['run_id']];assert job['status']=='RESERVED_OR_RUNNING' and job['billed_limit_GPUh']==8
 assert job['launch_id']==launch['launch_id'] and job['gpu_uuid']==launch['gpu_uuid']
 print(json.dumps(dict(status='FULL36_MEMORY_R2_GPU_ADMITTED_AND_CHILD_IDENTITY_ACCEPTED',supervisor=sup['pid'],child=sup['child_pid'],post=launch['post_watcher_pid'],admission=sup['admission'],pool={k:value['pool'][k] for k in ('used_gpu_hours','reserved_gpu_hours','available_gpu_hours')},next_check_not_before_unix=launch['next_check_not_before_unix'])))
if __name__=='__main__':main()
