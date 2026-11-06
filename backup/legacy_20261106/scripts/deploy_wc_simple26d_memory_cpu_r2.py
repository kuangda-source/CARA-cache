#!/usr/bin/env python3
"""Copy immutable W3 payload read-only, add separately committed new files."""
import argparse,hashlib,io,json,shlex,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
PROJECT='/home/gaokuangda/data/gkd/worldcache_omr'
STAGE='.sync/wc-simple26d-memory-production-r2-20261015'
BASE='.sync/wc-simple26d-production-r1-20261015'
FILES=('src/wcomr/simple26d_memory_r2.py', 'scripts/supervise_wc_simple26d_memory_full36_r2.py', 'scripts/check_wc_simple26d_memory_cpu_r2.py', 'scripts/postprocess_wc_simple26d_memory_full36_r2.py', 'scripts/watch_wc_simple26d_memory_post_cpu_r2.py', 'scripts/run_wc_simple26d_memory_cpu_bundle_r2.py', 'scripts/analyze_wc_simple26d_memory_full36_r2.py', 'scripts/run_wc_simple26d_memory_full36_r2.py', 'tests/check_simple26d_memory_sampling_cpu_r2.py', 'tests/test_simple26d_memory_boundary_r2.py', 'configs/wc_simple26d_memory_full36_r2_20261015.json', 'manifests/wc_simple26d_old28_memory_parity_r2_20261015.json', 'scripts/deploy_wc_simple26d_memory_cpu_r2.py', 'scripts/launch_wc_simple26d_memory_full36_r2.py')

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    payload={}
    for n in FILES:
        raw=(ROOT/n).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest==hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)).hexdigest(),n
        payload[n]=digest
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for n in FILES:archive.add(ROOT/n,arcname=n,recursive=False)
    code='PROJECT='+repr(PROJECT)+'\nBASE='+repr(BASE)+'\nSTAGE='+repr(STAGE)+'\nREV='+repr(revision)+'\nOVERLAY='+repr(payload)+'\n'+'''
import io,tarfile,pathlib,hashlib,json,subprocess,sys,os,time,shutil
root=pathlib.Path(PROJECT).resolve();base=root/BASE;stage=root/STAGE
assert not stage.exists(),'Never reuse or overwrite an old experiment stage'
stage.mkdir(parents=True)
reg=json.loads((base/'registration.json').read_text())
assert reg['source_revision']=='36f5583f321b70778129c8231a849ef7e370827d'
for n,h in reg['payload_sha256'].items():
 src=base/n;assert hashlib.sha256(src.read_bytes()).hexdigest()==h
 dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for name in ('simple26d-sampling-CPU-result.json',):
 assert (base/name).is_file();shutil.copyfile(base/name,stage/name)
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz') as archive:
 for member in archive:
  assert member.isfile() and member.name in OVERLAY and '..' not in pathlib.PurePosixPath(member.name).parts
  path=stage/member.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.extractfile(member).read())
  assert hashlib.sha256(path.read_bytes()).hexdigest()==OVERLAY[member.name]
reg.update(source_revision=REV,stage=STAGE,read_only_base_registration_sha256=hashlib.sha256((base/'registration.json').read_bytes()).hexdigest(),base_stage=str(base),CPU_scope='FULL144_MEMORY_PARITY_AND_ACTUAL_FULL36_PRODUCTION_NO_GPU')
reg['payload_sha256'].update(OVERLAY)
assert all(hashlib.sha256((stage/n).read_bytes()).hexdigest()==h for n,h in reg['payload_sha256'].items())
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\\n')
command=[sys.executable,str(stage/'scripts/run_wc_simple26d_memory_cpu_bundle_r2.py'),'--project',str(root),'--stage',str(stage)]
with (stage/'CPU-bundle.log').open('xb') as log:
 job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':''})
receipt=dict(status='SIMPLE26D_FULL_CPU_DISPATCHED',pid=job.pid,stage=str(stage),source_revision=REV,command=command,launched_unix=time.time(),registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),GPU_submissions=0,estimated_collect_after_seconds=900)
(stage/'launch.json').write_text(json.dumps(receipt,indent=2)+'\\n');print(json.dumps(receipt))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],input=stream.getvalue(),capture_output=True,timeout=120)
    result=dict(transport_exit_code=r.returncode,stderr=r.stderr.decode(),source_revision=revision)
    try:result['launch']=json.loads(r.stdout)
    except json.JSONDecodeError:result['stdout']=r.stdout.decode()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result));raise SystemExit(r.returncode)

if __name__=='__main__':main()
