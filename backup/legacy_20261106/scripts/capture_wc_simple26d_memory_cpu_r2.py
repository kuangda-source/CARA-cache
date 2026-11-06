#!/usr/bin/env python3
"""One scheduled collection of the immutable CPU stage; never launches a GPU."""
import argparse,gzip,json,shlex,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 launch=json.loads((ROOT/'reports/wc_simple26d_memory_full144_CPU_launch_20261015.json').read_text())['launch']
 assert time.time()>=launch['launched_unix']+launch['estimated_collect_after_seconds'],'Before registered CPU ETA; no SSH'
 code='LAUNCH='+repr(launch)+'\n'+r'''
import pathlib,json,sys,gzip,time
s=pathlib.Path(LAUNCH['stage']);r=s.parents[1];sys.path.insert(0,str(s/'src'))
from wcomr.gpu_budget_pool_v2 import process_identity,BudgetPool,sha
reg=json.loads((s/'registration.json').read_text());assert sha(s/'registration.json')==LAUNCH['registration_sha256']
v=dict(observed_unix=time.time(),launch=LAUNCH,registration=reg,payload_verified={n:sha(s/n)==h for n,h in reg['payload_sha256'].items()},process=process_identity(LAUNCH['pid']),pool=BudgetPool(r).read())
for k,n in [('bundle','CPU-bundle-result.json'),('numeric','simple26d-memory-sampling-CPU-result.json'),('production','production-CPU-result.json')]:
 if (s/n).exists():v[k]=json.loads((s/n).read_text());v[k+'_sha256']=sha(s/n)
if 'bundle' not in v or v['bundle'].get('exit_code')!=0:
 v['CPU_log_tail']=(s/'CPU-bundle.log').read_text(errors='replace')[-18000:]
print(json.dumps(v))
'''
 result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,text=True,timeout=120)
 assert result.returncode==0,result.stderr
 value=json.loads(result.stdout);a.output.write_bytes(gzip.compress(json.dumps(value,allow_nan=False).encode()))
 if 'bundle' not in value:
  print(json.dumps(dict(status='CPU_STILL_RUNNING_OR_NO_TERMINAL',process=value['process'])));return
 from sys import path
 path.insert(0,str(ROOT/'src'))
 from wcomr.simple26d_memory_r2 import CPU_STATUS,PRODUCTION_CPU_STATUS,CONFIG,sha
 b,n,p=value['bundle'],value.get('numeric',{}),value.get('production',{})
 assert b['exit_code']==0 and b['status']=='SIMPLE26D_COMPLETE_CPU_ACCEPTED_NOT_GPU',value.get('CPU_log_tail')
 assert b['source_revision']==launch['source_revision']==p['source_revision']
 assert all(value['payload_verified'].values()) and n['payload_sha256']==value['registration']['payload_sha256']
 assert n['status']==CPU_STATUS and n['actual_CPU_paths']==144 and n['legacy_complete_paths']==48 and n['repair_complete_paths']==96
 assert not n['CUDA_initialized'] and n['GPU_submissions']==0
 assert len(n['checks'])==2 and all(x['complete_CPU_paths']==72 and x['all36_clean_outputs_actions_video_equal'] for x in n['checks'])
 assert p['status']==PRODUCTION_CPU_STATUS and p['registration_sha256']==launch['registration_sha256'] and p['config_sha256']==sha(ROOT/CONFIG)
 assert p['sampling_CPU_sha256']==value['numeric_sha256'] and not p['CUDA_initialized'] and p['GPU_submissions']==0
 assert len(b['commands'])==5 and all(x['exit_code']==0 for x in b['commands'])
 assert value['process']['state'] in (None,'Z','X')
 print(json.dumps(dict(status='SIMPLE26D_MEMORY_FULL_CPU_INDEPENDENT_ACCEPTED_NOT_GPU',source_revision=launch['source_revision'],CPU_paths=144,CPU_seconds=b['wall_seconds'],GPU_submissions=0)))

if __name__=='__main__':main()
