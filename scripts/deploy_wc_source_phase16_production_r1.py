#!/usr/bin/env python3
"""Freeze complete368 cal16 CPU-tested bytes, validate production, then dispatch."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
ROOT='/home/gaokuangda/data/gkd/worldcache_omr'
STAGE=ROOT+'/.sync/wc-source-phase16-production-r1-20261012'
CPU=ROOT+'/.sync/wc-source-phase16-cpu-r2-20261012'
CONFIG='configs/wc_source_phase16_full368_production_r1_20261012.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def remote(code):
    compile(code,'<cal16-remote-wrapper>','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');a=p.parse_args()
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    if not a.launch:
        c=json.loads((R/CONFIG).read_text());params=json.loads((R/c['parameters_ref']).read_text())
        names=[CONFIG,'src/wcomr/source_phase16_production_r1.py','scripts/run_wc_source_phase16_r1.py',
            'scripts/supervise_wc_source_phase16_r1.py','scripts/postprocess_wc_source_phase16_cpu_r1.py',
            'scripts/check_wc_source_phase16_raw_cpu_r1.py',c['authority_ref']]+[c[k+'_ref'] for k in ('selection','parameters','cost','baseline')]+list(params['sources'])
        names=list(dict.fromkeys(names));packet={'source_revision':rev,'new_payload':{n:sha(R/n) for n in names}}
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w:gz') as t:
            for n in names:t.add(R/n,arcname=n)
        raw=json.loads((R/'reports/wc_source_phase16_cpu_r2_independent_raw_20261012.json').read_text())
        code='CPU='+repr(CPU)+'\nSTAGE='+repr(STAGE)+'\nRAW='+repr(raw)+'\n'+r'''import pathlib,json,hashlib,shutil
cpu=pathlib.Path(CPU);stage=pathlib.Path(STAGE);assert not stage.exists()
r=json.loads((cpu/'CPU-result.json').read_text());reg=json.loads((cpu/'registration.json').read_text())
assert r['status']=='SOURCE_PHASE16_TWO_FLOW_FULL16_PARENTS32_STATES_CPU_PASS_NOT_GPU' and r['actual_CPU_paths']==16 and not r['CUDA_initialized']
assert RAW['status']=='SOURCE_PHASE16_ALL32_RAW384_CFG_RECONSTRUCTION_CPU_PASS_NOT_REAL_LABELS' and RAW['raw_tensors']==384
assert RAW['sampling_result_sha256']==hashlib.sha256((cpu/'CPU-result.json').read_bytes()).hexdigest()
assert r['payload_sha256']==reg['payload_sha256'];stage.mkdir()
for n,h in reg['payload_sha256'].items():
 source=cpu/n;assert hashlib.sha256(source.read_bytes()).hexdigest()==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
shutil.copyfile(cpu/'CPU-result.json',stage/'sampling-CPU-result.json')
shutil.copyfile(cpu/'registration.json',stage/'sampling-CPU-registration.json')
(stage/'independent-CPU-raw-audit.json').write_text(json.dumps(RAW,indent=2)+'\n')
print(json.dumps({'status':'COMPLETE_CPU16_RAW384_COPIED','CPU_paths':16,'payload_files':len(reg['payload_sha256'])}))
'''
        print(remote(code).strip());subprocess.run(HOST+['tar -xzf - -C '+STAGE],input=buf.getvalue(),check=True)
        code='P='+repr(packet)+'\nSTAGE='+repr(STAGE)+'\nROOT='+repr(ROOT)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);reg=json.loads((stage/'sampling-CPU-registration.json').read_text());reg['source_revision']=P['source_revision']
for n,h in P['new_payload'].items():
 assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
 if n in reg['payload_sha256']:assert reg['payload_sha256'][n]==h
 reg['payload_sha256'][n]=h
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_source_phase16_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
print(json.dumps({'status':'SOURCE_PHASE16_ACTUAL_PRODUCTION_CPU_STARTED_NOT_GPU','pid':child.pid,'command':command,'stage':str(stage),'source_revision':P['source_revision'],'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}))
'''
        result=json.loads(remote(code));(R/'reports/wc_source_phase16_r1_production_cpu_launch_20261012.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return
    code='STAGE='+repr(STAGE)+'\nROOT='+repr(ROOT)+'\nREV='+repr(rev)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);r=json.loads((stage/'production-CPU-result.json').read_text());reg=json.loads((stage/'registration.json').read_text())
assert r['status']=='SOURCE_PHASE16_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and r['exit_code']==0 and reg['source_revision']==REV
assert r['registration_sha256']==hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()
for n,h in reg['payload_sha256'].items():assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
assert not (stage/'GPU-launch.json').exists() and not (root/'outputs/wc-source-phase16-full368-r1').exists()
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/supervise_wc_source_phase16_r1.py'),'--project',str(root),'--stage',str(stage),'--source-revision',REV]
with (stage/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
postcode="""import subprocess,sys,time,pathlib,json,os
pid=int(sys.argv[1]);stage=pathlib.Path(sys.argv[2]);root=pathlib.Path(sys.argv[3])
while pathlib.Path('/proc/'+str(pid)).exists():time.sleep(5)
output=root/'outputs/wc-source-phase16-full368-r1'
if not (output/'supervisor.json').exists():raise SystemExit('GPU admission failed; no new submission')
s=json.loads((output/'supervisor.json').read_text());assert s['status']=='SOURCE_PHASE16_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
with (stage/'post-CPU.log').open('x') as log:
 rc=subprocess.call([sys.executable,str(stage/'scripts/postprocess_wc_source_phase16_cpu_r1.py'),'--project',str(root),'--stage',str(stage)],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
(stage/'post-CPU-exit.json').write_text(json.dumps({'exit_code':rc,'GPU_submissions':0,'ledger_written':False,'ended_unix':time.time()})+'\\n')
"""
with (stage/'post-watcher.log').open('x') as log:
 post=subprocess.Popen(['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u','-c',postcode,str(child.pid),str(stage),str(root)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
r={'status':'SOURCE_PHASE16_COMPLETE368_DISPATCHED_ADMISSION_PENDING','supervisor_pid':child.pid,'post_watcher_pid':post.pid,'command':command,'stage':str(stage),'source_revision':REV,'started_unix':time.time()}
(stage/'GPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
    result=json.loads(remote(code));(R/'reports/wc_source_phase16_r1_GPU_launch_20261012.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
