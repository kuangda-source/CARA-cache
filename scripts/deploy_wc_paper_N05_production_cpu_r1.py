#!/usr/bin/env python3
"""Fresh independent no-GPU stage; copy the stopped R1 source read-only."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
PROJECT='/home/gaokuangda/data/gkd/worldcache_omr'
STAGE='.sync/wc-paper-n05-core66-production-cpu-r1-20261016'
BASE='.sync/wc-simple26d-production-r1-20261015'
FILES=(
 'src/wcomr/paper_baseline_grid_r1.py','src/wcomr/paper_baseline_production_r1.py','src/wcomr/paper_baseline_post_r1.py',
 'scripts/run_wc_paper_N05_core66_r1.py','scripts/postprocess_wc_paper_N05_core66_r1.py',
 'scripts/supervise_wc_paper_N05_core66_r1.py','scripts/watch_wc_paper_N05_post_cpu_r1.py',
 'scripts/run_wc_paper_N05_production_cpu_bundle_r1.py','scripts/deploy_wc_paper_N05_production_cpu_r1.py',
 'scripts/launch_wc_paper_N05_core66_r1.py',
 'scripts/check_wc_paper_N05_core216_local_cpu_r1.py','tests/check_paper_baseline_grid_sampling_cpu_r1.py',
 'tests/test_paper_baseline_grid_r1.py','tests/test_paper_baseline_production_and_post_r1.py','tests/test_paper_baseline_launch_cpu_r1.py',
 'configs/wc_paper_N05_core66_production_r1_20261016.json',
 'manifests/wc_paper_N05_bounded_baseline_grid_preregistration_draft_20261016.json',
 'manifests/wc_paper_N05_core66_preregistration_r1_20261016.json','manifests/wc_paper_N05_core66_full_cost_r1_20261016.json',
 'manifests/wc_paper_N05_original420_default20_bindings_r1_20261016.json',
 'reports/wc_paper_N05_actual_native_scheduler_grid_CPU_20261016.json',
 'reports/wc_paper_N05_core216_local_CPU_result_20261016.json','reports/wc_paper_N05_core216_local_CPU_independent_acceptance_20261016.json')
# Bind every reused numerical/helper source, including the later memory fix
# that is intentionally absent from the stopped R1 base stage.
NUMERIC=json.loads((ROOT/'reports/wc_paper_N05_core216_local_CPU_result_20261016.json').read_text())
FILES=tuple(dict.fromkeys((*FILES,*NUMERIC['source_sha256'])))

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();payload={}
    for name in FILES:
        raw=(ROOT/name).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        assert digest==hashlib.sha256(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)).hexdigest(),name
        payload[name]=digest
    assert all(payload[name]==digest for name,digest in NUMERIC['source_sha256'].items())
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for name in FILES:archive.add(ROOT/name,arcname=name,recursive=False)
    code='PROJECT='+repr(PROJECT)+'\nBASE='+repr(BASE)+'\nSTAGE='+repr(STAGE)+'\nREV='+repr(revision)+'\nOVERLAY='+repr(payload)+'\n'+r'''
import hashlib,io,json,os,pathlib,shutil,subprocess,sys,tarfile,time
root=pathlib.Path(PROJECT).resolve();base=root/BASE;stage=root/STAGE
assert not stage.exists(),'Never overwrite an old or running stage'
reg=json.loads((base/'registration.json').read_text())
assert reg['source_revision']=='36f5583f321b70778129c8231a849ef7e370827d'
stage.mkdir(parents=True)
for name,digest in reg['payload_sha256'].items():
 assert not pathlib.PurePosixPath(name).is_absolute() and '..' not in pathlib.PurePosixPath(name).parts
 source=base/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz') as archive:
 for member in archive:
  assert member.isfile() and member.name in OVERLAY and '..' not in pathlib.PurePosixPath(member.name).parts
  dest=stage/member.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.extractfile(member).read())
  assert hashlib.sha256(dest.read_bytes()).hexdigest()==OVERLAY[member.name]
reg.update(source_revision=REV,stage=STAGE,base_stage=str(base),CPU_scope='N05_FULL66_REAL_PRODUCTION_ENTRY_NO_GPU',
 read_only_base_registration_sha256=hashlib.sha256((base/'registration.json').read_bytes()).hexdigest())
reg['payload_sha256'].update(OVERLAY)
assert all(hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest for name,digest in reg['payload_sha256'].items())
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=[sys.executable,str(stage/'scripts/run_wc_paper_N05_production_cpu_bundle_r1.py'),'--project',str(root),'--stage',str(stage)]
with (stage/'CPU-bundle.log').open('xb') as log:
 job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env={**os.environ,'CUDA_VISIBLE_DEVICES':'','PYTHONDONTWRITEBYTECODE':'1','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'})
now=time.time()
receipt=dict(status='N05_CORE66_REAL_PRODUCTION_CPU_SINGLE_DISPATCH',pid=job.pid,source_revision=REV,stage=str(stage),
 command=command,launched_unix=now,registration_sha256=hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),
 original_N06_stage_or_processes_read=False,shared_runtime_written=False,GPU_submissions=0,
 first_collection_not_before_unix=now+180,expected_CPU_commands=4)
(stage/'launch.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
'''
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(code)],
        input=stream.getvalue(),capture_output=True,timeout=120)
    value=dict(transport_exit_code=r.returncode,stderr=r.stderr.decode(),source_revision=revision)
    try:value['launch']=json.loads(r.stdout)
    except json.JSONDecodeError:value['stdout']=r.stdout.decode()
    a.output.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value));raise SystemExit(r.returncode)

if __name__=='__main__':main()
