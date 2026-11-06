"""Finalize tested full50 core on CPU; later admit exactly one serial GPU job."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
SERVER='/home/gaokuangda/data/gkd/worldcache_omr'
TEMPLATE=SERVER+'/.sync/wc-source-confirmation-production-template-r1-20261013'
STAGE=SERVER+'/.sync/wc-source-confirmation-production-r1-20261013'
CONFIG='configs/wc_source_conditional_confirmation_full50_production_r1_20261013.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def remote(code):
    compile(code,'confirmation-final-production-remote','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def names():
    c=json.loads((ROOT/CONFIG).read_text());f=json.loads((ROOT/c['candidate_freeze_ref']).read_text())
    values=[CONFIG,'src/wcomr/source_conditional_confirmation_production_r1.py',
        'src/wcomr/source_confirmation_post_r1.py','scripts/run_wc_source_conditional_confirmation_r1.py',
        'scripts/supervise_wc_source_conditional_confirmation_r1.py',
        'scripts/watch_wc_source_conditional_confirmation_cpu_r1.py',
        'scripts/postprocess_wc_source_conditional_confirmation_cpu_r1.py',
        'tests/check_source_confirmation_post_cpu_r1.py',c['candidate_freeze_ref'],c['warmup_baseline_ref'],c['cost_ref']]
    values+=list(f['source_files_sha256'])
    return list(dict.fromkeys(values))


def main():
    p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');a=p.parse_args()
    packet={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'new_payload':{name:sha(ROOT/name) for name in names()}}
    if not a.launch:
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
            for name in packet['new_payload']:archive.add(ROOT/name,arcname=name)
        code='TEMPLATE='+repr(TEMPLATE)+'\nSTAGE='+repr(STAGE)+'\n'+r'''import pathlib,json,hashlib,shutil
template=pathlib.Path(TEMPLATE);stage=pathlib.Path(STAGE);assert not stage.exists()
reg=json.loads((template/'registration.json').read_text());proof=json.loads((template/'production-CPU-result.json').read_text())
assert proof['status']=='SOURCE_CONFIRMATION_TEMPLATE_PRODUCTION_CPU_PASS_CANDIDATE_UNFROZEN_NO_GPU'
assert proof['registration_sha256']==hashlib.sha256((template/'registration.json').read_bytes()).hexdigest()
stage.mkdir()
for name,digest in reg['payload_sha256'].items():
 source=template/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
for name in ('sampling-CPU-result.json','sampling-CPU-registration.json'):
 shutil.copyfile(template/name,stage/name)
shutil.copyfile(template/'registration.json',stage/'template-registration.json')
shutil.copyfile(template/'production-CPU-result.json',stage/'template-production-CPU-result.json')
print(json.dumps({'status':'ACCEPTED_FULL240_FULL50_CORE_COPIED_NO_GPU','payload_files':len(reg['payload_sha256'])}))
'''
        print(remote(code).strip());subprocess.run(HOST+['tar -xzf - -C '+STAGE],input=buffer.getvalue(),check=True)
        code='P='+repr(packet)+'\nSTAGE='+repr(STAGE)+'\nROOT='+repr(SERVER)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);reg=json.loads((stage/'template-registration.json').read_text())
reg['source_revision']=P['source_revision'];reg['new_payload_sha256']=P['new_payload']
for name,digest in P['new_payload'].items():
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
 if name in reg['payload_sha256']:assert reg['payload_sha256'][name]==digest
 reg['payload_sha256'][name]=digest
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_source_conditional_confirmation_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
print(json.dumps({'status':'SOURCE_CONFIRMATION_FINAL_FULL50_PRODUCTION_CPU_STARTED_NOT_GPU','pid':child.pid,'command':command,
 'stage':str(stage),'source_revision':P['source_revision'],'started_unix':time.time(),'new_payload_sha256':P['new_payload'],'GPU_submissions':0,'ledger_written':False}))
'''
        receipt=json.loads(remote(code));(ROOT/'reports/wc_source_confirmation_final_r1_production_cpu_launch_20261013.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps({k:receipt[k] for k in ('status','pid','source_revision','GPU_submissions')}));return
    code='P='+repr(packet)+'\nSTAGE='+repr(STAGE)+'\nROOT='+repr(SERVER)+'\nCONFIG='+repr(CONFIG)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time,fcntl
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT)
reg=json.loads((stage/'registration.json').read_text());proof=json.loads((stage/'production-CPU-result.json').read_text())
assert proof['status']=='SOURCE_CONFIRMATION_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
assert proof['candidate_frozen'] and proof['post_tests']['all50_rows_40_formal_four_prompts_two_seeds_verified']
assert proof['registration_sha256']==hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()
assert reg['new_payload_sha256']==P['new_payload']
for name,digest in reg['payload_sha256'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
assert not (stage/'GPU-launch.json').exists()
c=json.loads((stage/CONFIG).read_text());assert c['candidate_frozen'] and not c['template_production_CPU_only']
assert not (root/'outputs'/c['run_id']).exists()
teacher=root/'.sync/wc-teacher-first-velocity-production-r1-20261013'
assert json.loads((teacher/'post-CPU-exit.json').read_text())['exit_code']==0
assert json.loads((teacher/'CPU-final-results.json').read_text())['status']=='TEACHER_FIRST_ALL4_PARENTS8_SUFFIXES4_TEACHERS12_OUTPUTS_AUDITED_ALL93_SCORED'
ledger=json.loads((root/'reports/budget.json').read_text());assert not any('inflight' in k for k in ledger)
lock=(root/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/supervise_wc_source_conditional_confirmation_r1.py'),'--project',str(root),'--stage',str(stage),'--source-revision',reg['source_revision']]
with (stage/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
post_command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/watch_wc_source_conditional_confirmation_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--supervisor-pid',str(child.pid)]
with (stage/'post-watcher.log').open('x') as log:
 post=subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
receipt={'status':'SOURCE_CONFIRMATION_FULL50_DISPATCHED_ADMISSION_PENDING','supervisor_pid':child.pid,'post_watcher_pid':post.pid,'command':command,
 'post_command':post_command,'stage':str(stage),'source_revision':reg['source_revision'],'started_unix':time.time()}
(stage/'GPU-launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
'''
    receipt=json.loads(remote(code));(ROOT/'reports/wc_source_confirmation_final_r1_GPU_launch_20261013.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
