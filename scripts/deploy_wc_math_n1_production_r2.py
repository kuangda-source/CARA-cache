#!/usr/bin/env python3
"""Stage the tested whole speed20 source, run actual CPU entry, then one optional launch."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
FILES=['src/wcomr/math_n1_production_r2.py','scripts/run_wc_math_n1_r2.py',
 'scripts/supervise_wc_math_n1_r2.py','scripts/postprocess_wc_math_n1_cpu_r1.py',
 'configs/wc_math_n1_natural12_production_r1_20261012.json',
 'manifests/wc_math_n1_full180_cost_r1_20261012.json',
 'manifests/wc_math_n1_original_guided36_bindings_r1_20261012.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def remote(code):return subprocess.check_output(HOST+['python3 -'],input=code,text=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');a=p.parse_args()
 root='/home/gaokuangda/data/gkd/worldcache_omr';stage=root+'/.sync/wc-math-n1-production-r2-20261012';cpu=root+'/.sync/wc-math-n1-cpu-r4-20261012'
 rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
 if not a.launch:
  packet={'source_revision':rev,'new_payload':{n:sha(R/n) for n in FILES}}
  buf=io.BytesIO()
  with tarfile.open(fileobj=buf,mode='w:gz') as tar:
   for n in FILES:tar.add(R/n,arcname=n)
  code='ROOT='+repr(root)+'\nCPU='+repr(cpu)+'\nSTAGE='+repr(stage)+'\n'+r'''import pathlib,json,hashlib,shutil
cpu=pathlib.Path(CPU);stage=pathlib.Path(STAGE);assert not stage.exists()
r=json.loads((cpu/'CPU-result.json').read_text());assert r['status']=='MATH_N1_TWO_FLOW_FULL8_CPU_PATHS12_STATES_PASS_NOT_GPU' and r['actual_CPU_paths']==8 and not r['CUDA_initialized']
reg=json.loads((cpu/'registration.json').read_text());assert r['payload_sha256']==reg['payload_sha256'];stage.mkdir()
for n,h in reg['payload_sha256'].items():
 source=cpu/n;assert hashlib.sha256(source.read_bytes()).hexdigest()==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
shutil.copyfile(cpu/'CPU-result.json',stage/'sampling-CPU-result.json')
shutil.copyfile(cpu/'registration.json',stage/'sampling-CPU-registration.json')
print(json.dumps({'status':'SAMPLED_CPU_SOURCE_COPIED','paths':8,'payload_files':len(reg['payload_sha256'])}))
'''
  print(remote(code).strip());subprocess.run(HOST+['tar -xzf - -C '+stage],input=buf.getvalue(),check=True)
  code='P='+repr(packet)+'\nSTAGE='+repr(stage)+'\nROOT='+repr(root)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);reg=json.loads((stage/'sampling-CPU-registration.json').read_text());reg['source_revision']=P['source_revision']
for n,h in P['new_payload'].items():
 assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
 if n in reg['payload_sha256']:assert reg['payload_sha256'][n]==h
 reg['payload_sha256'][n]=h
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_math_n1_r2.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
print(json.dumps({'status':'ACTUAL_PRODUCTION_CPU_STARTED_NOT_GPU','pid':child.pid,'command':command,'stage':str(stage),'source_revision':P['source_revision'],'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}))
'''
  result=json.loads(remote(code));(R/'reports/wc_math_n1_r2_production_cpu_launch_20261012.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return
 code='STAGE='+repr(stage)+'\nROOT='+repr(root)+'\nREV='+repr(rev)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);r=json.loads((stage/'production-CPU-result.json').read_text());reg=json.loads((stage/'registration.json').read_text())
assert r['status']=='MATH_N1_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and r['exit_code']==0 and reg['source_revision']==REV
assert r['registration_sha256']==hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()
for n,h in reg['payload_sha256'].items():assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
assert not (stage/'GPU-launch.json').exists() and not (root/'outputs/wc-math-n1-natural-unit-r1').exists()
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/supervise_wc_math_n1_r2.py'),'--project',str(root),'--stage',str(stage),'--source-revision',REV]
with (stage/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
postcode="""import subprocess,sys,time,pathlib,json
pid=int(sys.argv[1]);stage=pathlib.Path(sys.argv[2]);root=pathlib.Path(sys.argv[3])
while pathlib.Path('/proc/'+str(pid)).exists():time.sleep(5)
output=root/'outputs/wc-math-n1-natural-unit-r1'
if not (output/'supervisor.json').exists():raise SystemExit('Original GPU admission failed; no new GPU submission')
s=json.loads((output/'supervisor.json').read_text());assert s['status']=='MATH_N1_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
with (stage/'post-CPU.log').open('x') as log:
 rc=subprocess.call([sys.executable,str(stage/'scripts/postprocess_wc_math_n1_cpu_r1.py'),'--project',str(root),'--stage',str(stage)],stdout=log,stderr=subprocess.STDOUT,env=dict(__import__('os').environ,CUDA_VISIBLE_DEVICES=''))
(stage/'post-CPU-exit.json').write_text(json.dumps({'exit_code':rc,'GPU_submissions':0,'ledger_written':False,'ended_unix':time.time()})+'\\n')
"""
with (stage/'post-watcher.log').open('x') as log:
 post=subprocess.Popen(['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u','-c',postcode,str(child.pid),str(stage),str(root)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
r={'status':'ORIGINAL_COMPLETE_SPEED20_DISPATCHED_ADMISSION_PENDING','supervisor_pid':child.pid,'post_watcher_pid':post.pid,'command':command,'stage':str(stage),'source_revision':REV,'started_unix':time.time()}
(stage/'GPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
 result=json.loads(remote(code));(R/'reports/wc_math_n1_r2_GPU_launch_20261012.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
