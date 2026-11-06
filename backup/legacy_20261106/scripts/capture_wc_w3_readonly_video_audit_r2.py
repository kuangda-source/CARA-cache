#!/usr/bin/env python3
"""One ETA collection of the fresh read-only CPU repair; never restarts a job."""
import argparse,gzip,json,shlex,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 launch=json.loads((ROOT/'reports/wc_w3_readonly_video_audit_r2_CPU_launch_20261016.json').read_text())['launch']
 assert time.time()>=launch['next_check_not_before_unix'],'Not due; no SSH or wait'
 code='LAUNCH='+repr(launch)+'\n'+r'''
import gzip,hashlib,json,pathlib,sys,time
stage=pathlib.Path(LAUNCH['stage']);root=stage.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==LAUNCH['registration_sha256']
reg=json.loads((stage/'registration.json').read_text());assert reg['source_revision']==LAUNCH['source_revision']
# The original W3 stage predates v2; capture uses stdlib only.
def process_identity(pid):
 p=pathlib.Path('/proc')/str(pid)
 try:
  rest=(p/'stat').read_text().split(') ',1)[1].split()
  return dict(pid=pid,state=rest[0],start_ticks=int(rest[19]),command=(p/'cmdline').read_bytes().replace(bytes([0]),b' ').decode())
 except FileNotFoundError:return dict(pid=pid,state=None,start_ticks=None,command=None)
v=dict(observed_unix=time.time(),launch=LAUNCH,registration=reg,payload_verified={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()},original_registration_unchanged=sha(pathlib.Path(LAUNCH['original_stage'])/'registration.json')==reg['original_registration_sha256'],process=process_identity(LAUNCH['pid']),pool=json.loads((root/'reports/gpu-budget-v2.json').read_text()))
for key,name in [('exit','CPU-exit.json'),('result','CPU-final-results.json')]:
 p=stage/name
 if p.exists():v[key]=json.loads(p.read_text());v[key+'_sha256']=sha(p)
if v.get('exit',{}).get('exit_code')!=0:v['CPU_log_tail']=(stage/'CPU.log').read_text(errors='replace')[-12000:]
print(json.dumps(v,allow_nan=False))
'''
 call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],capture_output=True,text=True,timeout=120)
 value=dict(transport_exit_code=call.returncode,stderr=call.stderr)
 try:value['capture']=json.loads(call.stdout)
 except json.JSONDecodeError:value['stdout']=call.stdout
 a.output.write_bytes(gzip.compress(json.dumps(value,allow_nan=False).encode(),mtime=0))
 state=value.get('capture',{});print(json.dumps(dict(receipt=str(a.output),transport_exit_code=call.returncode,process=state.get('process'),CPU_exit=state.get('exit',{}).get('exit_code'),result_status=state.get('result',{}).get('status'),scientific_acceptance_claim=False)))
 raise SystemExit(call.returncode)
if __name__=='__main__':main()
