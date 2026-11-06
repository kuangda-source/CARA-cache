#!/usr/bin/env python3
"""One dispatch after complete CPU acceptance; preserve the original W3 job."""
import argparse,hashlib,json,shlex,subprocess,uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
QUOTE='先排查并修复显存不足，保留已有结果和完整对照设计，验证通过后继续完成同26D实验，不影响W3。预算和少于12GPUh直接执行的规则不变，长任务按预计时间查收。'

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    source=json.loads((ROOT/'reports/wc_simple26d_memory_full144_CPU_launch_20261015.json').read_text())['source_revision']
    jobid=str(uuid.uuid4())
    code='REV='+repr(source)+'\nLAUNCH_ID='+repr(jobid)+'\nQUOTE='+repr(QUOTE)+'\n'+r'''
import pathlib,json,sys,os,time,subprocess,hashlib
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()
stage=root/'.sync/wc-simple26d-memory-production-r2-20261015'
sys.path.insert(0,str(stage/'src'))
from wcomr.simple26d_memory_r2 import validate,CONFIG,RUN,PRODUCTION_CPU_STATUS,sha,write,COUNTS,plans
from wcomr.gpu_budget_pool_v2 import process_identity
c,reg,old,inputs,tables,previous=validate(root,stage);proof=json.loads((stage/'production-CPU-result.json').read_text())
calibration=inputs[0];support=[]
for method,plan in plans().items():
 anchor=None
 for step,action in enumerate(plan,1):
  if action=='D':anchor=step
  else:
   assert (anchor,step) in calibration.rho_at and step in calibration.gains,(method,anchor,step)
   support.append(dict(method=method,anchor=anchor,step=step))
write(stage/'actual-calibration-mask-support.json',dict(status='ALL60_NON_D_REAL_CALIBRATION_CELLS_SUPPORTED',rows=support))
bundle=json.loads((stage/'CPU-bundle-result.json').read_text())
assert reg['source_revision']==REV and proof['status']==PRODUCTION_CPU_STATUS and bundle['status']=='SIMPLE26D_COMPLETE_CPU_ACCEPTED_NOT_GPU'
assert proof['registration_sha256']==sha(stage/'registration.json') and proof['config_sha256']==sha(stage/CONFIG)
assert not (stage/'GPU-launch.json').exists() and not (root/'outputs'/RUN).exists()
# Admission repeats this UUID observation under the new per-device lock.
gpu_uuid='GPU-de9a5370-cd87-0f1c-a48e-288888777dd3'
authority=dict(direct_user_authorization=True,user_reply_quote=QUOTE,cumulative_cap_GPUh=c['cumulative_cap_GPUh'],autonomy_exclusive_upper_GPUh=12)
old_budget_sha=sha(root/'reports/gpu-budget-v2.json')
auth={**authority,'source_revision':REV,'launch_id':LAUNCH_ID,'whole_card_run':RUN,'gpu_uuid':gpu_uuid,
    'config_sha256':sha(stage/CONFIG),'production_CPU_sha256':sha(stage/'production-CPU-result.json')}
authpath=stage/'new-GPU-authorization.json';write(authpath,auth)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
command=[sys.executable,str(stage/'scripts/supervise_wc_simple26d_memory_full36_r2.py'),'--project',str(root),'--stage',str(stage),
    '--source-revision',REV,'--gpu-uuid',gpu_uuid,'--authorization',str(authpath)]
with (stage/'supervisor.log').open('xb') as log:
 job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
post_command=[sys.executable,str(stage/'scripts/watch_wc_simple26d_memory_post_cpu_r2.py'),'--project',str(root),'--stage',str(stage),'--supervisor-pid',str(job.pid)]
with (stage/'post-watcher.log').open('xb') as log:
 post=subprocess.Popen(post_command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
now=time.time()
receipt=dict(status='SIMPLE26D_COMPLETE36_V2_DISPATCHED_ADMISSION_PENDING',source_revision=REV,launch_id=LAUNCH_ID,
    supervisor_pid=job.pid,post_watcher_pid=post.pid,command=command,post_command=post_command,
    gpu_uuid=gpu_uuid,stage=str(stage),run_id=RUN,started_unix=now,forecast_complete_GPUh=c['forecast_complete_GPUh'],
    billed_limit_GPUh=c['billed_limit_GPUh'],scope_counts=COUNTS,registration_sha256=sha(stage/'registration.json'),
    production_CPU_sha256=sha(stage/'production-CPU-result.json'),authorization_sha256=sha(authpath),
    old_ledger_before_bridge_sha256=old_budget_sha,old_ledger_after_bridge_sha256=sha(root/'reports/gpu-budget-v2.json'),
    next_check_not_before_unix=now+5*3600,original_W3_unchanged=True,timing_claim=c['timing_claim'])
write(stage/'GPU-launch.json',receipt);print(json.dumps(receipt))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,timeout=120)
    result=dict(transport_exit_code=r.returncode,stderr=r.stderr.decode())
    try:result['dispatch']=json.loads(r.stdout)
    except json.JSONDecodeError:result['stdout']=r.stdout.decode()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result));raise SystemExit(r.returncode)

if __name__=='__main__':main()
