"""Copy tested R3 core, validate whole270 production on CPU, then serial admission."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
SERVER='/home/gaokuangda/data/gkd/worldcache_omr'
STAGE=SERVER+'/.sync/wc-teacher-first-velocity-production-r1-20261013'
CPU=SERVER+'/.sync/wc-teacher-first-velocity-cpu-r3-20261013'
CONFIG='configs/wc_teacher_first_velocity_full270_production_r1_20261013.json'
RAW='reports/wc_teacher_first_velocity_cpu_r3_independent_raw_20261013.json'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()


def remote(code):
    compile(code,'teacher-production-remote','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def names():
    c=json.loads((ROOT/CONFIG).read_text());params=json.loads((ROOT/c['parameters_ref']).read_text())
    values=[CONFIG,'src/wcomr/teacher_first_velocity_production_r1.py',
        'src/wcomr/teacher_first_velocity_alignment_r1.py',
        'scripts/run_wc_teacher_first_velocity_r1.py','scripts/supervise_wc_teacher_first_velocity_r1.py',
        'scripts/watch_wc_teacher_first_velocity_cpu_r1.py','scripts/postprocess_wc_teacher_first_velocity_cpu_r1.py',
        'scripts/check_wc_teacher_first_velocity_raw_cpu_r1.py','tests/check_teacher_first_watcher_cpu_r1.py',
        c['authority_ref']]+[c[key+'_ref'] for key in ('selection','parameters','cost','baseline','original396_capture')]+list(params['sources'])
    return list(dict.fromkeys(values))


def main():
    p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true');a=p.parse_args()
    packet={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'new_payload':{name:sha(ROOT/name) for name in names()}}
    if not a.launch:
        audit=json.loads((ROOT/RAW).read_text());assert audit['raw_files']==24 and not audit['GPU_submissions']
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
            for name in packet['new_payload']:archive.add(ROOT/name,arcname=name)
        code='CPU='+repr(CPU)+'\nSTAGE='+repr(STAGE)+'\nRAW='+repr(audit)+'\n'+r'''import pathlib,json,hashlib,shutil
cpu=pathlib.Path(CPU);stage=pathlib.Path(STAGE);assert not stage.exists()
result=json.loads((cpu/'CPU-result.json').read_text());reg=json.loads((cpu/'registration.json').read_text())
assert result['status']=='TEACHER_FIRST_TWO_FLOW_FULL24_PARENTS32_ENDPOINT_SUFFIXES_CPU_PASS_NOT_GPU'
assert result['actual_CPU_parents']==24 and result['endpoint_suffixes']==32 and result['teacher_pairs']==8 and not result['CUDA_initialized']
assert RAW['status']=='TEACHER_FIRST_ALL24_RAW_TWO_FLOW_FRESH_TEACHER_AND_C_CACHE_CPU_PASS_NOT_GPU'
assert RAW['sampling_result_sha256']==hashlib.sha256((cpu/'CPU-result.json').read_bytes()).hexdigest()
assert result['payload_sha256']==reg['payload_sha256'];stage.mkdir()
for name,digest in reg['payload_sha256'].items():
 source=cpu/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
shutil.copyfile(cpu/'CPU-result.json',stage/'sampling-CPU-result.json')
shutil.copyfile(cpu/'registration.json',stage/'sampling-CPU-registration.json')
(stage/'independent-CPU-raw-audit.json').write_text(json.dumps(RAW,indent=2)+'\n')
print(json.dumps({'status':'COMPLETE_R3_CORE24_PARENTS32_SUFFIXES8_TEACHERS_COPIED','payload_files':len(reg['payload_sha256'])}))
'''
        print(remote(code).strip())
        subprocess.run(HOST+['tar -xzf - -C '+STAGE],input=buffer.getvalue(),check=True)
        code='P='+repr(packet)+'\nSTAGE='+repr(STAGE)+'\nROOT='+repr(SERVER)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);reg=json.loads((stage/'sampling-CPU-registration.json').read_text())
reg['source_revision']=P['source_revision'];reg['new_payload_sha256']=P['new_payload']
for name,digest in P['new_payload'].items():
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
 if name in reg['payload_sha256']:assert reg['payload_sha256'][name]==digest
 reg['payload_sha256'][name]=digest
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_teacher_first_velocity_r1.py'),'--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
print(json.dumps({'status':'TEACHER_FIRST_ACTUAL_PRODUCTION_CPU_STARTED_NOT_GPU','pid':child.pid,'command':command,'stage':str(stage),'source_revision':P['source_revision'],'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'new_payload_sha256':P['new_payload']}))
'''
        value=json.loads(remote(code));(ROOT/'reports/wc_teacher_first_velocity_r1_production_cpu_launch_20261013.json').write_text(json.dumps(value,indent=2)+'\n')
        print(json.dumps({k:value[k] for k in ('status','pid','stage','source_revision','GPU_submissions')}));return
    # Record-only commits after CPU preparation must not silently redefine
    # source. Launch the exact frozen revision if all intended local bytes match.
    code='P='+repr(packet)+'\nSTAGE='+repr(STAGE)+'\nROOT='+repr(SERVER)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time,fcntl
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT)
reg=json.loads((stage/'registration.json').read_text());proof=json.loads((stage/'production-CPU-result.json').read_text())
assert proof['status']=='TEACHER_FIRST_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
assert reg['new_payload_sha256']==P['new_payload']
assert proof['registration_sha256']==hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()
for name,digest in reg['payload_sha256'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
assert not (stage/'GPU-launch.json').exists()
cfg=json.loads((stage/'configs/wc_teacher_first_velocity_full270_production_r1_20261013.json').read_text())
assert not (root/'outputs'/cfg['run_id']).exists()
ledger=json.loads((root/'reports/budget.json').read_text())
assert not any('inflight' in key for key in ledger)
lock=(root/'.sync/f1.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/supervise_wc_teacher_first_velocity_r1.py'),'--project',str(root),'--stage',str(stage),'--source-revision',reg['source_revision']]
with (stage/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
post_command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/watch_wc_teacher_first_velocity_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--supervisor-pid',str(child.pid)]
with (stage/'post-watcher.log').open('x') as log:
 post=subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
receipt={'status':'TEACHER_FIRST_COMPLETE270_DISPATCHED_ADMISSION_PENDING','supervisor_pid':child.pid,'post_watcher_pid':post.pid,'command':command,'post_command':post_command,'stage':str(stage),'source_revision':reg['source_revision'],'started_unix':time.time()}
(stage/'GPU-launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
'''
    value=json.loads(remote(code));(ROOT/'reports/wc_teacher_first_velocity_r1_GPU_launch_20261013.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))


if __name__=='__main__':main()
