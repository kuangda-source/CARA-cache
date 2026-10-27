"""Single existing-stage dispatch. Unknown outcomes require handle recovery."""
import json
from pathlib import Path
from cara_two_card_transport_r1 import four_ssh
from wc_four_card_price_refresh_gpu_r1 import saved_secret
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r'''
import sys,json,os,time,fcntl,subprocess
from pathlib import Path
p=json.load(sys.stdin);secret=p.pop('sudo_password');s=Path(p['stage']);root=Path('/data20t/gaokuangda/worldcache_workspace');sys.path[:0]=[str(s/'src'),str(s/'scripts')]
from wcomr.wc73_execution_r1 import validate,Pool,hold,sha,RUN
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity,DeviceLease
from wcomr.wc73_exclusive_r1 import observe
from wcomr.history104_storage_r2 import storage_for
c,reg,auth=validate(root,s);assert sha(s/'registration.json')==p['registration_sha256'];storage=storage_for(s);storage.check()
with (root/'.sync/wc73-original-launch.lock').open('a+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not (s/'GPU-intent.json').exists() and RUN not in Pool(root).read()['jobs'],'Recover existing original'
 pool=Pool(root).read();assert pool['available_gpu_hours']>=12 and not any(j['status']=='RESERVED_OR_RUNNING' and not hold(j) for j in pool['jobs'].values())
 snap=observe(auth['gpu_uuid']);assert snap['compute_apps']==[] and snap['mps_processes']==[] and snap['compute_mode'] in ('Default','Exclusive_Process')
 with DeviceLease(root,auth['gpu_uuid']):pass
 intent=dict(run_id=RUN,launch_id=auth['launch_id'],stage=str(s),source_revision=reg['source_revision'],registration_sha256=sha(s/'registration.json'),gpu_uuid=auth['gpu_uuid'],host='four_card',whole_GPUh=12,created_unix=time.time())
 with (s/'GPU-intent.json').open('x') as f:json.dump(intent,f);f.flush();os.fsync(f.fileno())
 with (s/'whole-controller.log').open('x') as log:
  child=subprocess.Popen([sys.executable,str(s/'scripts/wc73_whole_controller_r1.py'),'--project',str(root),'--stage',str(s)],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  child.stdin.write(json.dumps(dict(sudo_password=secret)).encode());child.stdin.close();secret=None
 launch=dict(intent,controller_identity=process_identity(child.pid),dispatched_unix=time.time(),status='ORIGINAL_CONTROLLER_DISPATCHED_GPU_ADMISSION_PENDING')
 atomic_json(s/'GPU-launch.json',launch);print(json.dumps(launch))
'''
def main():
 r=json.loads((ROOT/'reports/cara_wc73_execution_stage_20261027.json').read_text());data={k:r[k] for k in ('stage','registration_sha256')};data['sudo_password']=saved_secret()
 v=four_ssh(REMOTE,data,timeout=45);f=ROOT/'reports/cara_wc73_GPU_launch_20261027.json';assert not f.exists();f.write_text(json.dumps(v,indent=2)+'\n');print(v)
if __name__=='__main__':main()
