#!/usr/bin/env python3
"""Read only the original P0 handles and compact progress; never dispatch."""
import json
from pathlib import Path
import subprocess


def main():
    launch = json.loads(Path('reports/wc_action_cost_real_r1_GPU_launch_20261010.json').read_text())
    code = 'L='+repr(launch)+'\n'+r'''
import json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');out=root/'outputs'/L['run_id'];post=pathlib.Path(L['post_CPU_stage'])
gpu=json.loads((out/'supervisor.json').read_text());cpu=json.loads((post/'receipt.json').read_text())
assert gpu['pid']==L['supervisor_pid'] and cpu['pid']==L['post_CPU_pid']
assert gpu['source_revision']==cpu['source_revision']==L['source_revision']
pids=[gpu['pid'],gpu.get('child_pid'),cpu['pid'],cpu.get('child_pid')]
result={'observed_unix':time.time(),'run_id':L['run_id'],'source_revision':L['source_revision'],
 'GPU_status':gpu['status'],'CPU_status':cpu['status'],
 'original_live_PIDs':[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()],
 'GPU':subprocess.check_output(['nvidia-smi','-i',gpu['gpu_uuid'],'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
 'elapsed_unsettled_seconds':time.time()-gpu['started_unix'] if gpu['status']!='EXITED_REQUIRES_RESULT_AUDIT' else None,
 'GPU_submissions_by_observation':0,'remote_writes':False,'log_tail':(out/'run.log').read_text()[-1200:]}
receipt=out/'diagnostic/receipt.json'
if receipt.exists():
 runner=json.loads(receipt.read_text());result['runner_status']=runner.get('status')
 result['parent_progress']=[{'scene':r['sample_name'],'paths':[{'label':p['label'],'status':p['status'],
 'solver_completed':len(p.get('solver_returns',[])),'origins':len(p.get('origins',[]))}
 for p in r['paths']]} for r in runner.get('batch',{}).get('requests',[])]
print(json.dumps(result))
'''
    call = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code,text=True,capture_output=True,timeout=45)
    if call.returncode:
        raise RuntimeError(call.stderr[-3000:])
    value = json.loads(call.stdout)
    Path('.sync/wc_action_cost_real_current_live.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value,indent=2))


if __name__ == '__main__':
    main()
