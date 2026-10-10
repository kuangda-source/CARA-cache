#!/usr/bin/env python3
"""Transport one registered read-only metadata CPU check, no model execution."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

DRIVER = r'''import hashlib,json,os,pathlib,subprocess,sys,time
stage=pathlib.Path(sys.argv[1]);project=stage.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((stage/'registration.json').read_text())
receipt={'status':'COMPLETE_REAL_INPUT_METADATA_CPU_RUNNING','pid':os.getpid(),'source_revision':sys.argv[2],
 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'CUDA_initialized':False,
 'budget_before_sha256':sha(project/'reports/budget.json'),'payload_sha256':reg['source_sha256']}
def save():
 p=stage/'receipt.json';t=p.with_suffix('.tmp');t.write_text(json.dumps(receipt,indent=2)+chr(10));t.replace(p)
assert not (stage/'receipt.json').exists();save();started=time.perf_counter()
try:
 assert {n:sha(stage/n) for n in reg['source_sha256']}==reg['source_sha256']
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
 cmd=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(stage/'scripts/check_wc_current_birth_real_inputs_cpu_r2.py'),'--project',str(project)]
 with (stage/'test.log').open('x') as log:
  child=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT);receipt['child_pid']=child.pid;save();receipt['child_exit_code']=child.wait()
 assert receipt['child_exit_code']==0
 dest=stage/'reports/wc_current_birth_real_inputs_cpu_r2_results_20261010.json';value=json.loads(dest.read_text())
 assert value['actual_Native_file_sizes_and_hashes_verified']==4 and value['complete_method_parameter_sets']==16
 assert not value['CUDA_initialized'] and not value['model_or_controller_installed'] and value['GPU_submissions']==0
 receipt.update(status='COMPLETE_REAL_INPUT_METADATA_ACTUAL_CPU_PASS_NOT_VIDEO',exit_code=0,result_sha256=sha(dest),result_ref=str(dest))
except BaseException as e:receipt.update(status='COMPLETE_REAL_INPUT_METADATA_CPU_FAILED_NO_INSTALLATION',exit_code=1,error_type=type(e).__name__,error=str(e))
finally:
 receipt.update(CPU_wall_seconds=time.perf_counter()-started,ended_unix=time.time(),budget_after_sha256=sha(project/'reports/budget.json'),payload_after_sha256={n:sha(stage/n) for n in reg['source_sha256']})
 if receipt['payload_after_sha256']!=reg['source_sha256']:receipt.update(status='SOURCE_CHANGED',exit_code=1)
 save()
raise SystemExit(receipt['exit_code'])
'''


def main():
    ref=Path('manifests/wc_current_birth_real_inputs_cpu_r2_preregistration_20261010.json')
    reg=json.loads(ref.read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert ref.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(ref)])
    files={n:Path(n).read_bytes() for n in reg['source_sha256']}
    for n,b in files.items():
        assert hashlib.sha256(b).hexdigest()==reg['source_sha256'][n]
        assert b==subprocess.check_output(['git','show',revision+':'+n])
    compile(DRIVER,'metadata_CPU_supervisor','exec')
    files.update({'registration.json':ref.read_bytes(),'driver.py':DRIVER.encode()})
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as tar:
        for n,b in files.items():
            entry=tarfile.TarInfo(n);entry.size=len(b);tar.addfile(entry,io.BytesIO(b))
    raw=buffer.getvalue();stem='wc-current-birth-real-inputs-cpu-r2-20261010'
    archive=Path('.sync')/(stem+'.tgz');assert not archive.exists();archive.write_bytes(raw)
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    launch=Path('reports/wc_current_birth_real_inputs_cpu_r2_launch_20261010.json');assert not launch.exists()
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(archive),'gkd_minchen:'+remote],check=True,timeout=600)
    packet={'remote':remote,'archive_sha256':hashlib.sha256(raw).hexdigest(),'source_revision':revision,'stage_name':stem,'driver_sha256':hashlib.sha256(DRIVER.encode()).hexdigest()}
    code='P='+repr(packet)+chr(10)+r'''
import hashlib,io,json,os,pathlib,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=root/'.sync'/P['stage_name'];assert not stage.exists()
raw=pathlib.Path(P['remote']).read_bytes();assert hashlib.sha256(raw).hexdigest()==P['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
 for item in tar.getmembers():
  p=pathlib.PurePosixPath(item.name);assert item.isfile() and not p.is_absolute() and '..' not in p.parts
 stage.mkdir();tar.extractall(stage)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'driver.py')==P['driver_sha256']
reg=json.loads((stage/'registration.json').read_text());assert {n:sha(stage/n) for n in reg['source_sha256']}==reg['source_sha256']
with (stage/'driver.log').open('x') as log:
 child=subprocess.Popen(['python3',str(stage/'driver.py'),str(stage),P['source_revision']],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
value={'stage':str(stage),'supervisor_pid':child.pid,'source_revision':P['source_revision'],'archive_sha256':P['archive_sha256'],'driver_sha256':P['driver_sha256'],'registration_sha256':sha(stage/'registration.json'),'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(stage/'launch.json').write_text(json.dumps(value,indent=2)+chr(10));print(json.dumps(value))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,timeout=55)
    if result.returncode:raise RuntimeError(result.stderr[-1500:])
    value=json.loads(result.stdout);launch.write_text(json.dumps(value,indent=2)+chr(10));print(json.dumps(value))


if __name__=='__main__':main()
