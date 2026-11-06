"""Copy accepted source bytes read-only and execute the affected CPU scope."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


DRIVER=r'''import hashlib,json,os,pathlib,subprocess,sys,time
s=pathlib.Path(sys.argv[1]);project=s.parents[1];reg=json.loads((s/'registration.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'status':'E4C_MATCHED_SOURCE_AGE_FULL_CPU_RUNNING','pid':os.getpid(),'source_revision':sys.argv[2],
 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'budget_before_sha256':sha(project/'reports/budget.json')}
target=s/'receipt.json';assert not target.exists()
def save():
 tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(target)
save();started=time.perf_counter()
try:
 assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']
 assert {n:sha(project/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
 command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(s/'scripts/check_wc_e4c_matched_source_age_cpu_r2.py'),
  '--stage',str(s),'--runtime',str(project/'runtime'),'--output',str(s/'result.json')]
 with (s/'CPU.log').open('x') as log:
  child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
   env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
  r.update(child_pid=child.pid,command=command);save();r['child_exit_code']=child.wait()
 assert r['child_exit_code']==0
 v=json.loads((s/'result.json').read_text())
 assert v['status']=='E4C_MATCHED_SOURCE_AGE_FULL_CPU_PASS_NOT_REAL_MODEL_OR_ADMISSION'
 assert (v['full_parent_paths'],v['suffixes'],v['same_state_age_points'],v['actual_tensors_reloaded'])==(8,32,48,776)
 assert v['actual_direct_tensor_comparisons']==324 and not v['CUDA_initialized']
 r.update(status='E4C_MATCHED_SOURCE_AGE_FULL_CPU_EXIT0_NOT_GPU',exit_code=0,result_sha256=sha(s/'result.json'))
except BaseException as error:r.update(status='E4C_MATCHED_SOURCE_AGE_FULL_CPU_FAILED_SCOPE_RETAINED',exit_code=1,error_type=type(error).__name__,error=str(error))
finally:
 r.update(CPU_wall_seconds=time.perf_counter()-started,ended_unix=time.time(),budget_after_sha256=sha(project/'reports/budget.json'),
  payload_after_sha256={n:sha(s/n) for n in reg['payload_sha256']})
 if r['budget_after_sha256']!=r['budget_before_sha256'] or r['payload_after_sha256']!=reg['payload_sha256']:
  r.update(status='E4C_MATCHED_SOURCE_AGE_FULL_CPU_IDENTITY_CHANGED',exit_code=1)
 save()
raise SystemExit(r['exit_code'])
'''


def main():
    root=Path(__file__).resolve().parents[1];name='manifests/wc_e4c_matched_source_age_full_cpu_r2_20261011.json'
    reg=json.loads((root/name).read_text());launch=root/'reports/wc_e4c_matched_source_age_cpu_r2_launch_20261011.json'
    assert not launch.exists()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    for n in [name]+reg['new_local_files']:
        assert (root/n).read_bytes()==subprocess.check_output(['git','show',revision+':'+n],cwd=root),n
    blobs={n:(root/n).read_bytes() for n in reg['new_local_files'] if n not in reg['copies_readonly_sha256']}
    assert all(hashlib.sha256(v).hexdigest()==reg['payload_sha256'][n] for n,v in blobs.items())
    blobs.update({'registration.json':(root/name).read_bytes(),'driver.py':DRIVER.encode()})
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
        for n,data in blobs.items():
            entry=tarfile.TarInfo(n);entry.size=len(data);archive.addfile(entry,io.BytesIO(data))
    stem='wc-e4c-matched-source-age-cpu-r2-20261011';path=root/'.sync'/(stem+'.tgz');assert not path.exists();path.write_bytes(buffer.getvalue())
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(path),'gkd_minchen:'+remote],check=True)
    packet={'stem':stem,'archive':remote,'archive_sha256':hashlib.sha256(buffer.getvalue()).hexdigest(),
        'copies':reg['copies_readonly_sha256'],'original':reg['original_accepted_CPU_stage'],
        'original_receipt_sha256':reg['original_accepted_CPU_receipt_sha256'],'revision':revision,
        'driver_sha256':hashlib.sha256(DRIVER.encode()).hexdigest()}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');s=root/'.sync'/P['stem'];old=root/P['original']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'receipt.json').read_text())
assert r['exit_code']==r['child_exit_code']==0 and sha(old/'receipt.json')==P['original_receipt_sha256']
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in (r['pid'],r['child_pid']))
assert {n:sha(old/n) for n in P['copies']}==P['copies']==r['payload_after_sha256']
assert sha(pathlib.Path(P['archive']))==P['archive_sha256'] and not s.exists();s.mkdir()
for n,h in P['copies'].items():
 target=s/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
with tarfile.open(P['archive']) as archive:
 for m in archive.getmembers():
  p=pathlib.PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and not (s/m.name).exists()
 archive.extractall(s)
reg=json.loads((s/'registration.json').read_text())
assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256'] and sha(s/'driver.py')==P['driver_sha256']
command=['python3',str(s/'driver.py'),str(s),P['revision']]
with (s/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
v={'stage':str(s),'supervisor_pid':child.pid,'source_revision':P['revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(s/'registration.json'),'payload_files':len(reg['payload_sha256']),
 'command':command,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(s/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    value=json.loads(call.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
