#!/usr/bin/env python3
"""Dispatch exactly one complete card only after original N06 acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
STAGE='.sync/wc-paper-n05-core66-production-cpu-r1-20261016'

def main():
    p=argparse.ArgumentParser()
    for name in ('N06-acceptance','CPU-launch','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    assert time.time()>=1792097651.2794473,'Before original N06 ETA: do not SSH or launch GPU'
    accepted=json.loads(a.N06_acceptance.read_text())
    assert accepted['status'] in ('SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED','SIMPLE26D_FULL36_TERMINAL_WITH_REJECTIONS_RETAINED')
    launch=json.loads(a.CPU_launch.read_text())['launch'];revision=launch['source_revision']
    launch_id=str(uuid.uuid4())
    code='REV='+repr(revision)+'\nACCEPTED='+repr(accepted)+'\nLAUNCH_ID='+repr(launch_id)+'\nSTAGE='+repr(STAGE)+'\n'+r'''
import json,os,pathlib,subprocess,sys,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve();stage=root/STAGE
sys.path.insert(0,str(stage/'src'))
from wcomr.paper_baseline_production_r1 import CONFIG,RUN,COUNTS,PRODUCTION_CPU_STATUS,sha,write,validate,verify_N06_prerequisite
from wcomr.gpu_budget_pool_v2 import process_identity
previous=verify_N06_prerequisite(root,ACCEPTED)
c,reg,*_=validate(root,stage);proof=json.loads((stage/'production-CPU-result.json').read_text());bundle=json.loads((stage/'CPU-bundle-result.json').read_text())
assert reg['source_revision']==REV==proof['source_revision']
assert proof['status']==PRODUCTION_CPU_STATUS and bundle['status']=='N05_CORE66_COMPLETE_PRODUCTION_CPU_PASS_NOT_GPU'
assert bundle['exit_code']==0 and len(bundle['commands'])==4 and all(r['exit_code']==0 for r in bundle['commands'])
assert proof['registration_sha256']==sha(stage/'registration.json') and proof['config_sha256']==sha(stage/CONFIG)
assert not (root/'outputs'/RUN).exists()
# Exclusive request fence makes a lost transport reply non-retriable.
with (stage/'GPU-launch-request.json').open('x') as f:json.dump(dict(launch_id=LAUNCH_ID,source_revision=REV),f)
authority=json.loads((stage/c['references']['autonomy']['ref']).read_text())
assert authority['automatic_comparison']=='strictly_less_than' and authority['automatic_single_job_gpu_hours']==12
assert c['forecast_complete_GPUh']<=c['billed_limit_GPUh']<12
gpu_uuid='GPU-de9a5370-cd87-0f1c-a48e-288888777dd3'
auth=dict(direct_user_authorization=True,user_reply_quote=authority['user_reply_quote'],autonomy_exclusive_upper_GPUh=12,
 source_revision=REV,launch_id=LAUNCH_ID,whole_card_run=RUN,gpu_uuid=gpu_uuid,
 config_sha256=sha(stage/CONFIG),production_CPU_sha256=sha(stage/'production-CPU-result.json'),N06_independent_acceptance=ACCEPTED)
authpath=stage/'GPU-authorization.json';write(authpath,auth)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
command=[sys.executable,str(stage/'scripts/supervise_wc_paper_N05_core66_r1.py'),'--project',str(root),'--stage',str(stage),
 '--source-revision',REV,'--gpu-uuid',gpu_uuid,'--authorization',str(authpath)]
with (stage/'supervisor.log').open('xb') as log:
 job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
identity=process_identity(job.pid)
assert identity['state'] not in (None,'Z','X') and 'supervise_wc_paper_N05_core66_r1.py' in identity['command']
receipt=dict(status='N05_CORE66_DISPATCHED_FRESH_ADMISSION_PENDING',source_revision=REV,launch_id=LAUNCH_ID,
 supervisor_pid=job.pid,supervisor_identity=identity,stage=str(stage),gpu_uuid=gpu_uuid,run_id=RUN,
 command=command,scope_counts=COUNTS,started_unix=time.time(),forecast_complete_GPUh=c['forecast_complete_GPUh'],
 billed_limit_GPUh=c['billed_limit_GPUh'],N06_prerequisite=previous,registration_sha256=sha(stage/'registration.json'),
 next_check_not_before_unix=time.time()+7*3600,post_watcher_pid=None)
write(stage/'GPU-launch.json',receipt)
post_command=[sys.executable,str(stage/'scripts/watch_wc_paper_N05_post_cpu_r1.py'),'--project',str(root),'--stage',str(stage),
 '--supervisor-pid',str(job.pid),'--supervisor-start-ticks',str(identity['start_ticks'])]
try:
 with (stage/'post-watcher.log').open('xb') as log:
  post=subprocess.Popen(post_command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 receipt.update(post_watcher_pid=post.pid,post_command=post_command)
except BaseException as error:receipt.update(post_dispatch_error_type=type(error).__name__,post_dispatch_error=str(error));raise
finally:write(stage/'GPU-launch.json',receipt);print(json.dumps(receipt))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,timeout=120)
    value=dict(transport_exit_code=result.returncode,stderr=result.stderr.decode())
    try:value['dispatch']=json.loads(result.stdout)
    except json.JSONDecodeError:value['stdout']=result.stdout.decode()
    a.output.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value));raise SystemExit(result.returncode)

if __name__=='__main__':main()
