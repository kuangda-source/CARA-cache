#!/usr/bin/env python3
"""Fresh read-only disk/device/pool snapshot immediately before the whole18 dispatch."""
import argparse,gzip,json,shlex,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    launch=json.loads((ROOT/'reports/wc_drop1_full56_actual18_CPU_launch_20261017.json').read_text())['launch']
    code='LAUNCH='+repr(launch)+'\n'+r'''
import json,pathlib,subprocess,sys,time,os,gzip
stage=pathlib.Path(LAUNCH['stage']);root=stage.parents[1];sys.path.insert(0,str(stage/'src'))
from wcomr.gpu_budget_pool_v2 import BudgetPool,DeviceLease,sha
c=json.loads((stage/'configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json').read_text())
b=json.loads((stage/'CPU-bundle-result.json').read_text());assert b['status']=='DROP1_COMPLETE_CPU_ACCEPTED_NOT_GPU' and b['exit_code']==0
assert sha(stage/'registration.json')==LAUNCH['registration_sha256'] and b['source_revision']==LAUNCH['source_revision']
pool=BudgetPool(root).read();assert pool['cap_gpu_hours']==226 and pool['available_gpu_hours']>=c['billed_limit_GPUh']
uuid='GPU-de9a5370-cd87-0f1c-a48e-288888777dd3'
values=subprocess.check_output(['nvidia-smi','-i',uuid,'--query-gpu=uuid,name,memory.used,compute_cap','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True,timeout=10)
own=[q for q in apps.splitlines() if q.split(',')[0].strip()==uuid]
gpu=dict(uuid=values[0].strip(),name=values[1].strip(),memory_used_MiB=int(values[2]),compute_cap=values[3].strip(),own_compute_apps=own)
stat=os.statvfs(root);free=stat.f_bavail*stat.f_frsize
assert gpu['uuid']==uuid and gpu['compute_cap']=='8.6' and gpu['memory_used_MiB']<1024 and not own
assert free>=6*1024**3
with DeviceLease(root,uuid):pass
v=dict(status='DROP1_FRESH_READONLY_UUID_DISK_AND_WHOLE_BUDGET_ELIGIBLE_NOT_GPU_LAUNCH',observed_unix=time.time(),source_revision=LAUNCH['source_revision'],registration_sha256=sha(stage/'registration.json'),GPU=gpu,disk_available_bytes=free,minimum_disk_bytes=6*1024**3,pool=pool,own_UUID_lock_available_at_check=True,GPU_submissions=0,ledger_written=False)
sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,timeout=120)
    if r.returncode:raise RuntimeError(r.stderr.decode())
    a.output.write_bytes(r.stdout);v=json.loads(gzip.decompress(r.stdout))
    print(json.dumps(dict(status=v['status'],GPU=v['GPU'],free_GiB=v['disk_available_bytes']/1024**3,available_GPUh=v['pool']['available_gpu_hours'],observed_unix=v['observed_unix'])))
if __name__=='__main__':main()
