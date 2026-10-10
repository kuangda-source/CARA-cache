#!/usr/bin/env python3
"""Copy frozen accepted CPU sources and launch only the E1 storage-owner delta."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile


DRIVER=r'''import hashlib,json,os,pathlib,subprocess,sys,time
s=pathlib.Path(sys.argv[1]);project=s.parents[1];reg=json.loads((s/'registration.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=s/'receipt.json';assert not receipt.exists()
r={'status':'E1_COMPLETE_STORAGE_CPU_RUNNING','pid':os.getpid(),'source_revision':sys.argv[2],
 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'budget_before_sha256':sha(project/'reports/budget.json')}
def save():
 tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(receipt)
save();start=time.perf_counter()
try:
 assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']
 assert {n:sha(project/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
 command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(s/'scripts/check_wc_e1_storage_full_sampler_cpu_r1.py'),
  '--stage',str(s),'--runtime',str(project/'runtime'),'--output',str(s/'result.json')]
 with (s/'CPU.log').open('x') as log:
  child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
   env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
  r.update(child_pid=child.pid,command=command);save();r['child_exit_code']=child.wait()
 assert r['child_exit_code']==0
 value=json.loads((s/'result.json').read_text())
 assert value['status']=='CPU_STORAGE_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'
 assert value['actual_CPU_backed_additional_roundtrips']==896
 assert (value['actual_complete_solver_updates'],value['actual_normal_net_calls'],value['actual_all_tensors_reloaded'])==(9216,18432,4736)
 assert not value['CUDA_initialized'] and value['GPU_submissions']==0
 r.update(status='E1_COMPLETE_STORAGE_CPU_EXIT0_NOT_REAL_GPU_REPAIR',exit_code=0,result_sha256=sha(s/'result.json'))
except BaseException as error:r.update(status='E1_COMPLETE_STORAGE_CPU_FAILED_SCOPE_RETAINED',exit_code=1,error_type=type(error).__name__,error=str(error))
finally:
 r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),budget_after_sha256=sha(project/'reports/budget.json'),
  payload_after_sha256={n:sha(s/n) for n in reg['payload_sha256']})
 if r['budget_after_sha256']!=r['budget_before_sha256'] or r['payload_after_sha256']!=reg['payload_sha256']:
  r.update(status='E1_COMPLETE_STORAGE_CPU_IDENTITY_CHANGED',exit_code=1)
 save()
raise SystemExit(r['exit_code'])
'''


def main():
    root=Path(__file__).resolve().parents[1]
    launch=root/'reports/wc_e1_storage_full_sampler_cpu_r1_launch_20261011.json'
    assert not launch.exists()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    previous=json.loads((root/'manifests/wc_current_birth_sampling_cpu_r3_preregistration_20261010.json').read_text())
    payload=dict(previous['payload_sha256'])
    changed=['src/wcomr/cpu_owned_state_snapshot.py','src/wcomr/source_aware_CPU_storage_sampling_r1.py',
        'tests/check_source_aware_CPU_storage_sampling_r1.py','scripts/check_wc_e1_storage_full_sampler_cpu_r1.py',
        'research/287_WC_E1_PRIMITIVE_PASS_AND_COMPLETE_SAMPLER_STORAGE_BINDING_20261011.md']
    for name in changed:payload[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
    for name in changed:
        expected=payload[name]
        data=(root/name).read_bytes();assert hashlib.sha256(data).hexdigest()==expected
        assert data==subprocess.check_output(['git','show',revision+':'+name],cwd=root)
    # Retain the original accepted fixture documentation bytes even when the
    # current plan has since advanced. Executable old sources must still match.
    historical_document='plans/WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md'
    for name,expected in previous['payload_sha256'].items():
        if name!=historical_document:
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected
    reg={**previous,'payload_sha256':payload,'E1_storage_CPU_scope':{'all_existing_scope_preserved':True,
        'actual_CPU_backed_additional_roundtrips':896,'GPU_submissions':0,'real_GPU_repair_claim':False},
        'source_revision':revision,'prior_current_birth_sources_readonly':True,
        'original_fixture_document_preserved_as_historical_input':historical_document}
    copies={n:h for n,h in payload.items() if n not in changed}
    blobs={n:(root/n).read_bytes() for n in changed}
    blobs.update({'registration.json':(json.dumps(reg,indent=2)+'\n').encode(),'driver.py':DRIVER.encode()})
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as tar:
        for name,data in blobs.items():
            entry=tarfile.TarInfo(name);entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
    stem='wc-e1-storage-full-sampler-cpu-r1-20261011'
    archive=root/'.sync'/(stem+'.tgz');assert not archive.exists();archive.write_bytes(buffer.getvalue())
    remote='/home/gaokuangda/data/gkd/worldcache_omr/.sync/'+stem+'.tgz'
    subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(archive),'gkd_minchen:'+remote],check=True)
    packet={'stem':stem,'archive':remote,'archive_sha256':hashlib.sha256(buffer.getvalue()).hexdigest(),
        'copies':copies,'revision':revision,'driver_sha256':hashlib.sha256(DRIVER.encode()).hexdigest()}
    code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,tarfile,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');s=root/'.sync'/P['stem'];assert not s.exists()
old=root/'.sync/wc-current-birth-sampling-cpu-r3-20261010'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'receipt.json').read_text());reg=json.loads((old/'registration.json').read_text())
assert r['exit_code']==r['child_exit_code']==0 and r['status']=='CURRENT_BIRTH_SAMPLING_ACTUAL_CPU_PASS_NOT_REAL_CAL'
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in (r['pid'],r['child_pid']))
assert {n:sha(old/n) for n in reg['payload_sha256']}==reg['payload_sha256']==r['payload_after_sha256']
assert sha(pathlib.Path(P['archive']))==P['archive_sha256']
s.mkdir()
for name,expected in P['copies'].items():
 assert sha(old/name)==expected
 target=s/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/name,target)
with tarfile.open(P['archive']) as tar:
 for member in tar.getmembers():
  assert member.isfile() and not pathlib.PurePosixPath(member.name).is_absolute() and '..' not in pathlib.PurePosixPath(member.name).parts
 tar.extractall(s)
reg=json.loads((s/'registration.json').read_text())
assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']
assert sha(s/'driver.py')==P['driver_sha256']
command=['python3',str(s/'driver.py'),str(s),P['revision']]
with (s/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
v={'stage':str(s),'supervisor_pid':child.pid,'source_revision':P['revision'],'archive_sha256':P['archive_sha256'],
 'registration_sha256':sha(s/'registration.json'),'command':command,'payload_files':len(reg['payload_sha256']),
 'old_source_files_copied_readonly':len(P['copies']),'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(s/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''
    result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stderr[-1800:])
    value=json.loads(result.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
