#!/usr/bin/env python3
"""Copy accepted CPU96 bytes, production CPU, then one whole36 GPU job."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
ROOT='/home/gaokuangda/data/gkd/worldcache_omr'
STAGE=ROOT+'/.sync/wc-source-phase-h1-production-r1-20261013'
CPU=ROOT+'/.sync/wc-source-phase-absolute-h1-cpu-r3-20261013'
CONFIG='configs/wc_source_phase_h1_full24_production_r1_20261013.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def remote(code):
    compile(code,'<source-phase-h1-production-wrapper>','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');a=p.parse_args()
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    if not a.launch:
        c=json.loads((R/CONFIG).read_text());previous=json.loads((R/c['previous_parameters_ref']).read_text())
        names=[CONFIG,c['authority_ref'],c['previous_parameters_ref'],c['cost_ref'],c['baseline_ref'],
            'src/wcomr/source_phase_h1_production_r1.py','scripts/run_wc_source_phase_h1_r1.py',
            'scripts/supervise_wc_source_phase_h1_r1.py','scripts/postprocess_wc_source_phase_h1_cpu_r1.py']+list(previous['sources'])
        for item in c['table_parameters'].values():
            names.append(item['ref']);names+=list(json.loads((R/item['ref']).read_text())['sources'])
        names=list(dict.fromkeys(names));packet={'source_revision':rev,'new_payload':{n:sha(R/n) for n in names}}
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w:gz') as t:
            for n in names:t.add(R/n,arcname=n)
        code='CPU='+repr(CPU)+'\nSTAGE='+repr(STAGE)+'\n'+r'''import pathlib,json,hashlib,shutil
cpu=pathlib.Path(CPU);stage=pathlib.Path(STAGE);assert not stage.exists()
r=json.loads((cpu/'CPU-result.json').read_text());reg=json.loads((cpu/'registration.json').read_text())
assert r['status']=='SOURCE_PHASE_ABSOLUTE_H1_TWO_FLOW_ALL48_AUDIT48_LEAN_CPU_PASS_NOT_GPU' and r['actual_CPU_paths']==96 and not r['CUDA_initialized']
assert all(set(v['sources_exercised'])=={'D','P'} and set(v['readouts_exercised'])=={'C','A'} for v in r['checks'])
assert r['payload_sha256']==reg['payload_sha256'];stage.mkdir()
for n,h in reg['payload_sha256'].items():
 source=cpu/n;assert hashlib.sha256(source.read_bytes()).hexdigest()==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
shutil.copyfile(cpu/'CPU-result.json',stage/'sampling-CPU-result.json')
shutil.copyfile(cpu/'registration.json',stage/'sampling-CPU-registration.json')
print(json.dumps({'status':'FULL_CPU96_D_P_SOURCES_C_A_COPIED','payload_files':len(reg['payload_sha256'])}))
'''
        print(remote(code).strip());subprocess.run(HOST+['tar -xzf - -C '+STAGE],input=buf.getvalue(),check=True)
        code='P='+repr(packet)+'\nSTAGE='+repr(STAGE)+'\nROOT='+repr(ROOT)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);reg=json.loads((stage/'sampling-CPU-registration.json').read_text());reg['source_revision']=P['source_revision']
for n,h in P['new_payload'].items():
 assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
 if n in reg['payload_sha256']:assert reg['payload_sha256'][n]==h
 reg['payload_sha256'][n]=h
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_source_phase_h1_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
print(json.dumps({'status':'SOURCE_PHASE_H1_ACTUAL_PRODUCTION_CPU_STARTED_NOT_GPU','pid':child.pid,'command':cmd,'stage':str(stage),'source_revision':P['source_revision'],'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}))
'''
        r=json.loads(remote(code));(R/'reports/wc_source_phase_h1_r1_production_cpu_launch_20261013.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return
    code='STAGE='+repr(STAGE)+'\nROOT='+repr(ROOT)+'\nREV='+repr(rev)+'\nCONFIG='+repr(CONFIG)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);r=json.loads((stage/'production-CPU-result.json').read_text());reg=json.loads((stage/'registration.json').read_text());c=json.loads((stage/CONFIG).read_text())
assert r['status']=='SOURCE_PHASE_H1_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and r['exit_code']==0 and reg['source_revision']==REV
assert r['registration_sha256']==hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()
for n,h in reg['payload_sha256'].items():assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
assert not (stage/'GPU-launch.json').exists() and not (root/'outputs'/c['run_id']).exists()
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/supervise_wc_source_phase_h1_r1.py'),'--project',str(root),'--stage',str(stage),'--source-revision',REV]
with (stage/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
postcode="""import subprocess,sys,time,pathlib,json,os
pid=int(sys.argv[1]);stage=pathlib.Path(sys.argv[2]);root=pathlib.Path(sys.argv[3]);run=sys.argv[4]
while pathlib.Path('/proc/'+str(pid)).exists():time.sleep(5)
output=root/'outputs'/run
if not (output/'supervisor.json').exists():raise SystemExit('Original GPU admission failed; no new submission')
s=json.loads((output/'supervisor.json').read_text());assert s['status']=='SOURCE_PHASE_H1_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
with (stage/'post-CPU.log').open('x') as log:
 rc=subprocess.call([sys.executable,str(stage/'scripts/postprocess_wc_source_phase_h1_cpu_r1.py'),'--project',str(root),'--stage',str(stage)],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
(stage/'post-CPU-exit.json').write_text(json.dumps({'exit_code':rc,'GPU_submissions':0,'ledger_written':False,'ended_unix':time.time()}))
"""
compile(postcode,'<released-H1-CPU-watcher>','exec')
with (stage/'post-watcher.log').open('x') as log:
 post=subprocess.Popen(['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u','-c',postcode,str(child.pid),str(stage),str(root),c['run_id']],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
r={'status':'SOURCE_PHASE_H1_COMPLETE36_DISPATCHED_ADMISSION_PENDING','supervisor_pid':child.pid,'post_watcher_pid':post.pid,'command':command,'stage':str(stage),'source_revision':REV,'started_unix':time.time(),'post_output_uses_same_config_run_id':c['run_id']}
(stage/'GPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
    r=json.loads(remote(code));(R/'reports/wc_source_phase_h1_r1_GPU_launch_20261013.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))


if __name__=='__main__':main()
