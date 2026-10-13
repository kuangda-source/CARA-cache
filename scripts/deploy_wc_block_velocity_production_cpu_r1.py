"""Prepare exact full312 production on CPU only, without observing main GPU."""
import argparse
import base64
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SERVER='/home/gaokuangda/data/gkd/worldcache_omr'
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
BASE=SERVER+'/.sync/wc-block-saved-reference-cpu-r1-20261013'
SAMPLE=SERVER+'/.sync/wc-block-velocity-suffix3-cpu-r2-20261013'
CONFIG='configs/wc_block_velocity_suffix3_full312_production_r1_20261013.json'
NEW=[CONFIG,'src/wcomr/block_velocity_production_r1.py','scripts/run_wc_block_velocity_r1.py',
 'scripts/supervise_wc_block_velocity_r1.py','scripts/watch_wc_block_velocity_cpu_r1.py',
 'scripts/postprocess_wc_block_velocity_cpu_r1.py','scripts/deploy_wc_block_velocity_production_cpu_r1.py']


def main():
    p=argparse.ArgumentParser();p.add_argument('--suffix',choices=('r1','r2','r3'),default='r1');a=p.parse_args()
    stage=SERVER+'/.sync/wc-block-velocity-production-'+a.suffix+'-20261013'
    cfg=json.loads((ROOT/CONFIG).read_text())
    names=list(dict.fromkeys(NEW+[cfg[k+'_ref'] for k in ('parameters','cost','baseline','authority')]))
    assert all((ROOT/n).is_file() for n in names)
    rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    packet=dict(source_revision=rev,new_payload_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    for n,h in packet['new_payload_sha256'].items():
        assert hashlib.sha256(subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)).hexdigest()==h
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w:gz') as t:
        for n in names:t.add(ROOT/n,arcname=n)
    code=('P='+repr(packet)+'\nROOT='+repr(SERVER)+'\nBASE='+repr(BASE)+'\nSAMPLE='+repr(SAMPLE)
          +'\nSTAGE='+repr(stage)+'\nARCHIVE='+repr(base64.b64encode(buf.getvalue()).decode())+'\n')+r'''
import pathlib,json,hashlib,subprocess,os,time,base64,io,tarfile,sys
root=pathlib.Path(ROOT);base=pathlib.Path(BASE);sample=pathlib.Path(SAMPLE);stage=pathlib.Path(STAGE)
if (stage/'production-CPU-launch.json').exists():
 r=json.loads((stage/'registration.json').read_text());assert r['new_payload_sha256']==P['new_payload_sha256']
 print((stage/'production-CPU-launch.json').read_text());sys.exit(0)
assert not (stage/'production-CPU.log').exists(),'Unknown original CPU handle, do not resubmit'
raw=json.loads((base/'CPU-result.json').read_text());sampling=json.loads((sample/'CPU-result.json').read_text())
reg=json.loads((base/'registration.json').read_text())
assert raw['status']=='FOUR_SAVED_B_REFERENCE_ALL_IDENTITIES_SHAPES_REPEATS_AND_REFUSALS_CPU_PASS'
assert raw['payload_sha256']==reg['payload_sha256'] and len(raw['rows'])==4
assert sampling['status']=='B_SAVED_VELOCITY_SUFFIX3_TWO_FLOW32_PARENTS64_SUFFIXES_CPU_PASS_NOT_GPU'
assert sampling['actual_CPU_parents']==32 and sampling['endpoint_suffixes']==64
assert not raw['CUDA_initialized'] and not sampling['CUDA_initialized']
stage.mkdir(exist_ok=True)
def store(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():assert path.read_bytes()==data
 else:path.write_bytes(data)
for n,h in reg['payload_sha256'].items():
 data=(base/n).read_bytes();assert hashlib.sha256(data).hexdigest()==h;store(stage/n,data)
store(stage/'sampling-CPU-result.json',(sample/'CPU-result.json').read_bytes())
store(stage/'saved-reference-CPU-result.json',(base/'CPU-result.json').read_bytes())
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(ARCHIVE)),mode='r:gz') as t:
 for m in t.getmembers():
  assert m.isfile() and m.name in P['new_payload_sha256'];data=t.extractfile(m).read()
  assert hashlib.sha256(data).hexdigest()==P['new_payload_sha256'][m.name];store(stage/m.name,data)
payload=dict(reg['payload_sha256'])
for n,h in P['new_payload_sha256'].items():
 if n in payload:assert payload[n]==h
 payload[n]=h
final=dict(reg,source_revision=P['source_revision'],payload_sha256=payload,new_payload_sha256=P['new_payload_sha256'])
store(stage/'registration.json',(json.dumps(final,indent=2)+'\n').encode())
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_block_velocity_r1.py'),
 '--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
receipt=dict(stage=str(stage),CPU_pid=child.pid,source_revision=P['source_revision'],command=command,started_unix=time.time(),
 payload_files=len(payload),GPU_submissions=0,ledger_written=False,inflight_main_not_observed_or_modified=True)
store(stage/'production-CPU-launch.json',(json.dumps(receipt,indent=2)+'\n').encode());print(json.dumps(receipt))
'''
    compile(code,'saved-B-production-CPU-deployment','exec')
    r=json.loads(subprocess.check_output(HOST+['python3 -'],input=code,text=True,timeout=120))
    (ROOT/'reports'/('wc_block_velocity_production_'+a.suffix+'_CPU_launch_20261013.json')).write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r))


if __name__=='__main__':main()
