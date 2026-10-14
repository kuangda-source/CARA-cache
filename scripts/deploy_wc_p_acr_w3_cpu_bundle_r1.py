"""Create one fresh project-owned CPU stage. No GPU or shared runtime writes."""
import argparse
import base64
import hashlib
import io
import json
import re
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
STAGE='.sync/wc-p-acr-w3-shared-prefix-cpu-r1-20261015'
REMOTE_PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
PROJECT='/home/gaokuangda/data/gkd/worldcache_omr'
SCRIPTS=('scripts/check_wc_p_acr_shared_prefix_cpu_r1.py','scripts/check_wc_w3_causal_trend_cpu_r1.py','scripts/run_wc_p_acr_w3_cpu_bundle_r1.py')
PREREG='manifests/wc_p_acr_w3_cpu_interface_prereg_20261015.json'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--launch-cpu',action='store_true');ap.add_argument('--stage-suffix',default='r1');a=ap.parse_args()
    if a.output.exists():raise ValueError('New launch receipt required')
    if not re.fullmatch(r'r[1-9][0-9]*',a.stage_suffix):raise ValueError('Fresh named CPU revision only')
    stage_name=STAGE.replace('cpu-r1-','cpu-'+a.stage_suffix+'-')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    names=sorted(str(p.relative_to(ROOT)) for directory in ('src/wcomr','tests') for p in (ROOT/directory).glob('*.py'))+list(SCRIPTS)+[PREREG]
    payload={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
    for name in names:
        blob=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
        if hashlib.sha256(blob).hexdigest()!=payload[name]:raise ValueError('CPU payload must be fully committed: '+name)
    reg={'source_revision':revision,'payload_sha256':payload,'CPU_scopes':['P80','W3_11'],'GPU_submissions':0,'shared_runtime_written':False,'stage':stage_name}
    if not a.launch_cpu:print(json.dumps({'status':'PACKET_READY_NOT_LAUNCHED','files':len(payload),'source_revision':revision,'GPU_submissions':0}));return
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as tar:
        for name in names:tar.add(ROOT/name,arcname=name,recursive=False)
        raw=json.dumps(reg,indent=2).encode();entry=tarfile.TarInfo('registration.json');entry.size=len(raw);tar.addfile(entry,io.BytesIO(raw))
    code="""import pathlib,tarfile,io,sys,json,subprocess,hashlib,time,os
root=pathlib.Path(PROJECT).resolve();stage=root/STAGE
assert not stage.exists(),'Fresh stage required; never duplicate original CPU launch'
stage.mkdir(parents=True)
archive=tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz')
for member in archive:
 assert member.isfile() and '..' not in pathlib.PurePosixPath(member.name).parts and not pathlib.PurePosixPath(member.name).is_absolute()
 path=stage/member.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.extractfile(member).read())
reg=json.loads((stage/'registration.json').read_text())
assert all(hashlib.sha256((stage/name).read_bytes()).hexdigest()==h for name,h in reg['payload_sha256'].items())
command=[sys.executable,str(stage/'scripts/run_wc_p_acr_w3_cpu_bundle_r1.py'),'--stage',str(stage),'--project',str(root),'--runtime',str(root/'runtime')]
log=(stage/'CPU-bundle.log').open('xb')
job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':''})
receipt={'pid':job.pid,'source_revision':reg['source_revision'],'stage':str(stage),'command':command,'launched_unix':time.time(),'registration_sha256':hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),'GPU_submissions':0,'estimated_collect_after_seconds':600}
(stage/'launch.json').write_text(json.dumps(receipt,indent=2)+'\\n');print(json.dumps(receipt))
"""
    code='PROJECT='+repr(PROJECT)+'\nSTAGE='+repr(stage_name)+'\n'+code
    command=REMOTE_PY+' -c '+shlex.quote(code)
    started=time.time();p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',command],input=buffer.getvalue(),capture_output=True,timeout=120)
    result={'transport_exit_code':p.returncode,'started_unix':started,'ended_unix':time.time(),'source_revision':revision,'stderr':p.stderr.decode(),'GPU_submissions':0}
    try:result['launch']=json.loads(p.stdout)
    except json.JSONDecodeError:result['unparsed_stdout']=p.stdout.decode()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
    if p.returncode:raise SystemExit(p.returncode)


if __name__=='__main__':main()
