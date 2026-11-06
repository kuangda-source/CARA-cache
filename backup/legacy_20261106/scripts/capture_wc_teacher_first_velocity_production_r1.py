"""Read exact full270 production handles/receipts without remote mutations."""
import argparse,hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
CODE=r'''import pathlib,json,hashlib,subprocess,fcntl,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=root/'.sync/wc-teacher-first-velocity-production-r1-20261013'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text())
c=json.loads((stage/'configs/wc_teacher_first_velocity_full270_production_r1_20261013.json').read_text())
output=root/'outputs'/c['run_id'];ids={}
r={'observed_unix':time.time(),'stage':str(stage),'output':str(output),
 'source_revision':reg['source_revision'],'payload_files':len(reg['payload_sha256']),
 'payload_all_verified':all(sha(stage/n)==h for n,h in reg['payload_sha256'].items()),
 'registration_sha256':sha(stage/'registration.json')}
for key,path in [('production_CPU',stage/'production-CPU-result.json'),('GPU_launch',stage/'GPU-launch.json'),
 ('supervisor',output/'supervisor.json'),('runner',output/'runner.json'),
 ('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json')]:
 if path.exists():r[key]=json.loads(path.read_text());r[key+'_sha256']=sha(path)
if r.get('GPU_launch'):ids.update({k:r['GPU_launch'][k] for k in ('supervisor_pid','post_watcher_pid')})
if r.get('supervisor',{}).get('child_pid'):ids['child_pid']=r['supervisor']['child_pid']
r['original_processes']={k:pathlib.Path('/proc',str(v)).exists() for k,v in ids.items()}
ledger=root/'reports/budget.json';r['ledger']=json.loads(ledger.read_text());r['ledger_sha256']=sha(ledger)
try:r['GPU']=subprocess.check_output(['nvidia-smi','-i','GPU-cebf7119-cf03-23b9-e192-cd196332b704','--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
except (OSError,subprocess.TimeoutExpired,subprocess.CalledProcessError) as e:r['GPU']={'status':'TELEMETRY_UNAVAILABLE','error':str(e)}
lock=(root/'.sync/f1.lock').open('a+')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r['kernel_lock_free']=True;fcntl.flock(lock,fcntl.LOCK_UN)
except BlockingIOError:r['kernel_lock_free']=False
lock.close()
for key,path in [('GPU.log_tail',output/'GPU.log'),('production-CPU.log_tail',stage/'production-CPU.log'),('post-CPU.log_tail',stage/'post-CPU.log')]:
 if path.exists():r[key]='\n'.join(path.read_text(errors='replace').splitlines()[-5:])
print(json.dumps(r,allow_nan=False))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='reports/wc_teacher_first_velocity_live_or_terminal_capture_20261013.json')
    a=p.parse_args();compile(CODE,'teacher-readonly-capture','exec')
    value=json.loads(subprocess.check_output(HOST+['python3 -'],input=CODE,text=True))
    assert value['payload_all_verified']
    full=ROOT/'.sync/wc_teacher_first_velocity_full_readonly_capture_20261013.json'
    full.parent.mkdir(exist_ok=True);full.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    receipt=dict(value,full_readonly_capture_ref=str(full),full_readonly_capture_sha256=hashlib.sha256(full.read_bytes()).hexdigest())
    if receipt.get('runner'):
        for parent in receipt['runner'].get('runs',[]):
            for branch in parent.get('event',{}).get('branches',[]):
                history=branch.pop('source_policy_tail',None)
                if history:branch['future_physical_actions_compact']=[h['action'] for h in history]
    if receipt.get('final'):receipt['final'].pop('GPU_supervisor',None)
    (ROOT/a.output).write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'source_revision':receipt['source_revision'],'payload_files':receipt['payload_files'],
        'payload_all_verified':receipt['payload_all_verified'],'production_CPU_status':receipt.get('production_CPU',{}).get('status'),
        'GPU_selected':bool(receipt.get('GPU_launch')),'parents_completed':sum(p.get('status')=='COMPLETE' for p in receipt.get('runner',{}).get('runs',[])),
        'parents_planned':4,'final_status':receipt.get('final',{}).get('status'),
        'original_processes':receipt['original_processes'],'kernel_lock_free':receipt['kernel_lock_free']}))


if __name__=='__main__':main()
