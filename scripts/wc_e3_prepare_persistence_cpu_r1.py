"""Transport and capture one immutable CPU-only metadata check."""
import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

REG = 'manifests/wc_e3_prepare_persistence_affected_cpu_r1_20261011.json'
STEM = 'wc-e3-prepare-persistence-cpu-r1-20261011'
ROOT = '/home/gaokuangda/data/gkd/worldcache_omr'
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
DRIVER = r'''import hashlib,json,os,pathlib,subprocess,sys,time
s=pathlib.Path(sys.argv[1]);project=s.parents[1];reg=json.loads((s/'registration.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'status':'E3_PREPARE_PERSISTENCE_CPU_RUNNING','pid':os.getpid(),'source_revision':sys.argv[2],
 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False,'budget_before_sha256':sha(project/'reports/budget.json')}
target=s/'receipt.json';assert not target.exists()
def save():
 tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(target)
save();started=time.perf_counter()
try:
 assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']
 command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',str(s/'scripts/check_wc_e3_prepare_persistence_cpu_r1.py'),
  '--source',str(s),'--registration',str(s/'registration.json'),'--output',str(s/'result.json')]
 with (s/'CPU.log').open('x') as log:
  child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
   env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
  r.update(child_pid=child.pid,command=command);save();r['child_exit_code']=child.wait()
 assert r['child_exit_code']==0
 result=json.loads((s/'result.json').read_text())
 assert result['status']=='E3_PREPARE_PERSISTENCE_AFFECTED_CPU_PASS_NOT_PRODUCTION_BATCH_OR_GPU'
 assert result['checks_passed']==8 and not result['CUDA_initialized'] and result['GPU_submissions']==0
 r.update(status='E3_PREPARE_PERSISTENCE_CPU_EXIT0',exit_code=0,result_sha256=sha(s/'result.json'))
except BaseException as error:r.update(status='E3_PREPARE_PERSISTENCE_CPU_FAILED',exit_code=1,error_type=type(error).__name__,error=str(error))
finally:
 r.update(CPU_wall_seconds=time.perf_counter()-started,ended_unix=time.time(),budget_after_sha256=sha(project/'reports/budget.json'),
  payload_after_sha256={n:sha(s/n) for n in reg['payload_sha256']})
 if r['budget_after_sha256']!=r['budget_before_sha256'] or r['payload_after_sha256']!=reg['payload_sha256']:
  r.update(status='E3_PREPARE_PERSISTENCE_CPU_IDENTITY_CHANGED',exit_code=1)
 save()
raise SystemExit(r['exit_code'])
'''


def ssh(code):
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                             'gkd_minchen', 'python3 -'], input=code, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=('deploy', 'capture'))
    args = parser.parse_args(); root = Path(__file__).resolve().parents[1]
    launch = root / 'reports/wc_e3_prepare_persistence_cpu_r1_launch_20261011.json'
    reg = json.loads((root / REG).read_text())
    if args.mode == 'deploy':
        assert not launch.exists()
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        for n in [REG, 'scripts/wc_e3_prepare_persistence_cpu_r1.py', *reg['payload_sha256']]:
            assert (root/n).read_bytes() == subprocess.check_output(['git', 'show', revision+':'+n], cwd=root), n
        blobs = {n:(root/n).read_bytes() for n in reg['payload_sha256']}
        assert {n:hashlib.sha256(v).hexdigest() for n,v in blobs.items()} == reg['payload_sha256']
        blobs.update({'registration.json':(root/REG).read_bytes(), 'driver.py':DRIVER.encode()})
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            for n,data in blobs.items():
                entry=tarfile.TarInfo(n);entry.size=len(data);archive.addfile(entry,io.BytesIO(data))
        path=root/'.sync'/(STEM+'.tgz');assert not path.exists();path.write_bytes(buffer.getvalue())
        remote=ROOT+'/.sync/'+STEM+'.tgz'
        subprocess.run(['scp','-q','-o','BatchMode=yes','-o','ConnectTimeout=15',str(path),'gkd_minchen:'+remote],check=True)
        packet=dict(stage=ROOT+'/.sync/'+STEM,archive=remote,archive_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),
                    source_revision=revision,driver_sha256=hashlib.sha256(DRIVER.encode()).hexdigest(),python=PYTHON)
        code='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,subprocess,tarfile,time
s=pathlib.Path(P['stage']);a=pathlib.Path(P['archive']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not s.exists() and sha(a)==P['archive_sha256'];s.mkdir()
with tarfile.open(a) as archive:
 for m in archive.getmembers():
  p=pathlib.PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts
 archive.extractall(s)
r=json.loads((s/'registration.json').read_text());assert {n:sha(s/n) for n in r['payload_sha256']}==r['payload_sha256']
assert sha(s/'driver.py')==P['driver_sha256']
command=['python3',str(s/'driver.py'),str(s),P['source_revision']]
with (s/'driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
value={**P,'supervisor_pid':child.pid,'registration_sha256':sha(s/'registration.json'),
 'command':command,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
(s/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''
        value=ssh(code);launch.write_text(json.dumps(value,indent=2)+'\n')
        print(json.dumps(value));return 0
    original=json.loads(launch.read_text())
    code='P='+repr(original)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,time
s=pathlib.Path(P['stage']);r=json.loads((s/'receipt.json').read_text())
pids=[r['pid'],r.get('child_pid')];live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'status':'E3_ORIGINAL_CPU_HANDLES_LIVE','PIDs':live}));raise SystemExit(0)
assert r['pid']==P['supervisor_pid'] and r['source_revision']==P['source_revision']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((s/'registration.json').read_text());assert sha(s/'registration.json')==P['registration_sha256']
assert {n:sha(s/n) for n in reg['payload_sha256']}==reg['payload_sha256']==r['payload_after_sha256']
assert r['budget_before_sha256']==r['budget_after_sha256'] and r['GPU_submissions']==0 and not r['ledger_written']
names=['receipt.json','registration.json','CPU.log','driver.log','launch.json']
if (s/'result.json').exists():names.append('result.json')
if r['exit_code']==0:
 assert sha(s/'result.json')==r['result_sha256']
 v=json.loads((s/'result.json').read_text());assert v['source_sha256']==reg['payload_sha256']
 assert v['checks_passed']==8 and not v['CUDA_initialized']
native={}
for n in names:
 raw=(s/n).read_bytes();z=gzip.compress(raw,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(z).hexdigest(),'base64':base64.b64encode(z).decode()}
print(json.dumps({'status':'E3_ORIGINAL_PREPARE_CPU_TERMINAL_CAPTURE','receipt':r,'native':native,'observed_unix':time.time()}))
'''
    value=ssh(code)
    if 'native' not in value:print(json.dumps(value));return 2
    target=root/'reports/wc_e3_prepare_persistence_cpu_r1_terminal_20261011_capture.json';assert not target.exists()
    value['files']={}
    for n,v in value.pop('native').items():
        z=base64.b64decode(v.pop('base64'),validate=True);raw=gzip.decompress(z)
        assert hashlib.sha256(z).hexdigest()==v['compressed_sha256'] and hashlib.sha256(raw).hexdigest()==v['sha256'] and len(raw)==v['bytes']
        p=root/'reports'/('wc_e3_prepare_persistence_cpu_r1_terminal_20261011_'+n+'.native.gz');assert not p.exists();p.write_bytes(z)
        value['files'][n]={**v,'local_path':str(p.relative_to(root))}
        if n=='registration.json':assert json.loads(raw)==reg
        if n=='launch.json':assert json.loads(raw)==original
    value['source_and_original_terminal_receipts_independently_verified']=True
    target.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
