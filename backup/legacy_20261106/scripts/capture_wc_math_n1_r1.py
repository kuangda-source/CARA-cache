#!/usr/bin/env python3
"""Read-only source/ledger/process snapshot; never launch or mutate remote jobs."""
import argparse,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
CODE=r'''import json,pathlib,subprocess,time,hashlib
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync/wc-math-n1-production-r2-20261012';output=root/'outputs/wc-math-n1-natural-unit-r1'
value={'observed_unix':time.time(),'stage':str(stage),'output':str(output)}
for n,p in [('supervisor',output/'supervisor.json'),('runner',output/'runner.json'),('final',stage/'CPU-final-results.json'),('post_exit',stage/'post-CPU-exit.json')]:
 if p.exists():value[n]=json.loads(p.read_text());value[n+'_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
b=root/'reports/budget.json';value['ledger']=json.loads(b.read_text());value['ledger_sha256']=hashlib.sha256(b.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text());value['payload_verified']={n:hashlib.sha256((stage/n).read_bytes()).hexdigest()==h for n,h in reg['payload_sha256'].items()}
value['GPU']=subprocess.check_output(['nvidia-smi','-i','GPU-cebf7119-cf03-23b9-e192-cd196332b704','--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],text=True).strip()
pids=[value.get('supervisor',{}).get('pid'),value.get('supervisor',{}).get('child_pid')]
value['original_processes']={str(pid):pathlib.Path('/proc/'+str(pid)).exists() for pid in pids if pid}
for name in ['GPU-supervisor.log','post-CPU.log','post-watcher.log']:
 p=stage/name
 if p.exists():value[name+'_tail']=p.read_text()[-4000:]
p=output/'GPU.log'
if p.exists():value['GPU.log_tail']=p.read_text()[-5000:]
print(json.dumps(value))
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--save',action='store_true');a=p.parse_args()
 r=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],input=CODE,text=True))
 assert all(r['payload_verified'].values())
 if a.save:(R/'reports/wc_math_n1_live_or_terminal_capture_20261012.json').write_text(json.dumps(r,indent=2)+'\n')
 rr=r.get('runner',{});rows=rr.get('runs',[])
 summary={k:r.get(k) for k in ['observed_unix','GPU','original_processes']}
 summary.update(supervisor_status=r.get('supervisor',{}).get('status'),runner_status=rr.get('status'),finished_parents=sum(x['status']=='COMPLETE' for x in rows),finished_points=sum(len(x.get('diagnostic_points',[])) for x in rows),current_scene=rows[-1].get('scene') if rows else None,final_status=r.get('final',{}).get('status'),post_exit=r.get('post_exit'),source_preserved=True,actual_used=r['ledger']['used_gpu_hours'] if not any('inflight' in k for k in r['ledger']) else r.get('supervisor',{}).get('budget_before',{}).get('used_gpu_hours'))
 progress=re.findall(r'(\d+)/36',r.get('GPU.log_tail',''))
 summary['current_sample_solver_progress']=int(progress[-1]) if progress else None
 print(json.dumps(summary))
 if rr.get('error'):print('runner_error:',rr['error'])
 if not r.get('supervisor'):print(r.get('GPU-supervisor.log_tail',''))
 if r.get('final',{}).get('error'):print('CPU_error:',r['final']['error'])
if __name__=='__main__':main()
