#!/usr/bin/env python3
"""Observe the original suffix8 handles without restarting or changing state."""
import argparse,hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
CODE=r'''import json,pathlib,subprocess,time,hashlib,fcntl
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-pi0-suffix8-production-r1-20261013';output=root/'outputs/wc-pi0-readout-suffix8-full266-r1'
r={'observed_unix':time.time(),'stage':str(stage),'output':str(output)}
for n,p in [('supervisor',output/'supervisor.json'),('runner',output/'runner.json'),('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json')]:
 if p.exists():r[n]=json.loads(p.read_text());r[n+'_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text());r['source_revision']=reg['source_revision'];r['payload_verified']={n:hashlib.sha256((stage/n).read_bytes()).hexdigest()==h for n,h in reg['payload_sha256'].items()}
p=root/'reports/budget.json';r['ledger']=json.loads(p.read_text());r['ledger_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
launch=json.loads((stage/'GPU-launch.json').read_text());pids=[launch['supervisor_pid'],launch['post_watcher_pid'],r.get('supervisor',{}).get('child_pid')]
r['original_processes']={str(pid):pathlib.Path('/proc/'+str(pid)).exists() for pid in pids if pid}
r['GPU']=subprocess.check_output(['nvidia-smi','-i','GPU-cebf7119-cf03-23b9-e192-cd196332b704','--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True).strip()
r['compute_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True).strip().splitlines()
lock=(root/'.sync/f1.lock').open('a+')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r['kernel_lock_free']=True;fcntl.flock(lock,fcntl.LOCK_UN)
except BlockingIOError:r['kernel_lock_free']=False
lock.close()
r['point_files_saved_not_audited']=[{'path':str(p),'bytes':p.stat().st_size} for p in sorted(output.glob('*/branches/*/vectors.pt'))]
for name,path in [('GPU.log',output/'GPU.log'),('post-CPU.log',stage/'post-CPU.log'),('GPU-supervisor.log',stage/'GPU-supervisor.log')]:
 if path.exists():r[name+'_tail']=path.read_text()[-3500:]
print(json.dumps(r))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--save',action='store_true');a=p.parse_args()
    value=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],input=CODE,text=True))
    assert all(value['payload_verified'].values())
    rows=value.get('runner',{}).get('runs',[])
    if a.save:
        full=R/'.sync'/('wc_pi0_suffix8_full_readonly_capture_'+str(int(value['observed_unix']))+'.json')
        full.write_text(json.dumps(value,indent=2)+'\n')
        # All raw records remain on the server and in this complete ignored
        # capture. The small Git receipt retains every row/count/failure and
        # the full CPU-final labels, not duplicate per-step hook inventories.
        compact=dict(value);compact['full_readonly_capture_path']=str(full)
        compact['full_readonly_capture_sha256']=hashlib.sha256(full.read_bytes()).hexdigest()
        if 'runner' in compact:
            compact['runner']={k:v for k,v in value['runner'].items() if k!='runs'}
            compact['runner']['runs']=[]
            for old in rows:
                row={k:v for k,v in old.items() if k not in ('A_history','source_history','event')}
                if 'event' in old:
                    event=old['event'];row['event']={k:v for k,v in event.items() if k!='branches'}
                    row['event']['branches']=[{k:v for k,v in b.items() if k!='source_policy_tail'} for b in event.get('branches',[])]
                compact['runner']['runs'].append(row)
        (R/'reports/wc_pi0_suffix8_live_or_terminal_capture_20261013.json').write_text(json.dumps(compact,indent=2)+'\n')
    summary={k:value.get(k) for k in ('source_revision','observed_unix','GPU','original_processes','kernel_lock_free')}
    summary.update(runner_status=value.get('runner',{}).get('status'),
        completed_paths=sum(x['status']=='COMPLETE' for x in rows),
        completed_suffixes=sum(sum(b.get('status','').startswith('COMPLETE_ENDPOINT') for b in x.get('event',{}).get('branches',[])) for x in rows),
        point_files_saved_not_audited=len(value['point_files_saved_not_audited']),
        final_status=value.get('final',{}).get('status'),post_exit=value.get('post_exit'),
        current_scene=rows[-1].get('scene') if rows else None)
    print(json.dumps(summary))
    for name in ('runner','final'):
        if value.get(name,{}).get('error'):print(name+'_error:',value[name]['error'])


if __name__=='__main__':main()
