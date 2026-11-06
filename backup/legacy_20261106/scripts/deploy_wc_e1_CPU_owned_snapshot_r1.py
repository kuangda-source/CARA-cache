#!/usr/bin/env python3
"""Unique pinned CPU primitive check; original failed full64 assets stay read-only."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import tempfile


def main():
    root=Path(__file__).resolve().parents[1]
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    files=['src/wcomr/__init__.py','src/wcomr/partial_mlp_deployment_state.py','src/wcomr/mid_coverage.py',
        'src/wcomr/mid_scope.py','src/wcomr/partial_mlp.py','src/wcomr/cpu_owned_state_snapshot.py',
        'scripts/check_wc_e1_CPU_owned_snapshot_r1.py','research/286_WC_E1_CPU_STORAGE_PRIMITIVE_PREREGISTRATION_20261011.md']
    hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
    original=json.loads(gzip.decompress((root/'reports/wc_current_birth_full64_r1_terminal_20261010_runner_native.gz').read_bytes()))
    for name in files[:5]:
        assert hashes[name]==original['config']['payload_sha256'][name]
    registration={'source_revision':revision,'CPU_scope':{'positive_controls':4,'refusals':11},
        'payload_sha256':hashes,'original_GPU_stage':'/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-current-birth-full64-selected-cpu-r1-20261010',
        'original_source_sha256':{name:hashes[name] for name in files[:5]},'GPU_submissions':0,
        'logical_copy_cap_unchanged':True,'old_GPU_admission_unchanged':True,'real_owner_integration':False}
    data=subprocess.check_output(['git','archive','--format=tar',revision,*files],cwd=root)
    stage='/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-e1-CPU-owned-snapshot-r1-20261011'
    archive=stage+'.tar'
    ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen']
    # Refuse before transfer, then the remote unique mkdir is checked again.
    guard='from pathlib import Path; p=Path('+repr(stage)+'); assert not p.exists(), "Existing E1 stage: no repeat"'
    subprocess.run(ssh+['python3 -c '+shlex.quote(guard)],check=True)
    with tempfile.NamedTemporaryFile(suffix='.tar') as f:
        f.write(data);f.flush()
        subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',f.name,'gkd_minchen:'+archive],check=True)
    code='''import base64,hashlib,json,os,pathlib,subprocess,tarfile,time
s=pathlib.Path(STAGE);p=s.parents[1]
reg=REGISTRATION;archive=pathlib.Path(ARCHIVE)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==ARCHIVE_SHA
for name,expected in reg['original_source_sha256'].items():
 assert hashlib.sha256((pathlib.Path(reg['original_GPU_stage'])/name).read_bytes()).hexdigest()==expected
s.mkdir()
with tarfile.open(archive) as tar:
 for member in tar.getmembers():
  assert (member.isdir() or member.isfile() and member.name in reg['payload_sha256']) and not member.name.startswith('/') and '..' not in pathlib.Path(member.name).parts
 tar.extractall(s)
for name,expected in reg['payload_sha256'].items():
 assert hashlib.sha256((s/name).read_bytes()).hexdigest()==expected
(s/'preregistration.json').write_text(json.dumps(reg,indent=2)+'\\n')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
before=sha(p/'reports/budget.json');start=time.perf_counter()
r={'source_revision':reg['source_revision'],'supervisor_pid':os.getpid(),'started_unix':time.time(),
 'GPU_submissions':0,'ledger_written':False,'budget_before_sha256':before,'status':'E1_CPU_STORAGE_PRIMITIVE_RUNNING'}
save=lambda:(s/'receipt.json').write_text(json.dumps(r,indent=2)+'\\n')
save()
with (s/'CPU.log').open('x') as log:
 child=subprocess.Popen(['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(s/'scripts/check_wc_e1_CPU_owned_snapshot_r1.py'),
  '--stage',str(s),'--output',str(s/'result.json')],stdout=log,stderr=subprocess.STDOUT,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
 r['child_pid']=child.pid;save();exit_code=child.wait()
r.update(exit_code=exit_code,child_exit_code=exit_code,CPU_wall_seconds=time.perf_counter()-start,
 ended_unix=time.time(),budget_after_sha256=sha(p/'reports/budget.json'),
 payload_after_sha256={name:sha(s/name) for name in reg['payload_sha256']},
 original_source_after_sha256={name:sha(pathlib.Path(reg['original_GPU_stage'])/name) for name in reg['original_source_sha256']},
 status='E1_CPU_STORAGE_PRIMITIVE_EXIT0_NOT_REAL_REPAIR' if exit_code==0 else 'E1_CPU_STORAGE_PRIMITIVE_FAILED_RETAINED')
if (s/'result.json').exists():r['result_sha256']=sha(s/'result.json')
save()
files={}
for name in ('receipt.json','preregistration.json','result.json','CPU.log'):
 path=s/name
 if path.exists():
  value=path.read_bytes();files[name]={'sha256':sha(path),'bytes':len(value),'base64':base64.b64encode(value).decode()}
print(json.dumps({'stage':str(s),'observed_unix':time.time(),'live_child':pathlib.Path('/proc/'+str(child.pid)).exists(),'files':files}))
'''.replace('STAGE',repr(stage)).replace('REGISTRATION',repr(registration)).replace('ARCHIVE_SHA',repr(hashlib.sha256(data).hexdigest())).replace('ARCHIVE',repr(archive))
    output=subprocess.run(ssh+['python3 -c '+shlex.quote(code)],check=True,capture_output=True,text=True)
    capture=json.loads(output.stdout)
    summary={k:v for k,v in capture.items() if k!='files'};summary['files']={}
    for name,item in capture['files'].items():
        value=base64.b64decode(item['base64']);assert len(value)==item['bytes'] and hashlib.sha256(value).hexdigest()==item['sha256']
        target=root/'reports'/('wc_e1_CPU_owned_snapshot_r1_terminal_20261011_'+name.replace('.','_')+'_native.gz')
        assert not target.exists();target.write_bytes(gzip.compress(value,mtime=0))
        summary['files'][name]={'sha256':item['sha256'],'bytes':item['bytes'],'local_ref':str(target.relative_to(root)),
            'gzip_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        if name=='receipt.json':receipt=json.loads(value)
    summary.update(source_revision=revision,archive_sha256=hashlib.sha256(data).hexdigest(),GPU_submissions=0)
    target=root/'reports/wc_e1_CPU_owned_snapshot_r1_terminal_20261011_capture.json'
    assert not target.exists();target.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'status':receipt['status'],'child_exit_code':receipt['exit_code'],'CPU_wall_seconds':receipt['CPU_wall_seconds']}))
    raise SystemExit(receipt['exit_code'])


if __name__=='__main__':main()
