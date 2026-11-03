#!/usr/bin/env python3
"""Prepare/capture one GPU-hidden B1 analysis through the existing two-card route."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

from cara_two_card_transport_r1 import password

ROOT=Path(__file__).resolve().parents[1]
FILES=('src/wcomr/cara_f19_saved_tensor_r2.py','src/wcomr/cara_f19_zero_gpu_r1.py',
    'scripts/analyze_cara_f19_saved_tensor_r2.py','src/wcomr/cara_fast_spec_r1.py',
    'src/wcomr/innovation_gain_assets_r1.py','src/wcomr/mid_coverage.py','src/wcomr/mid_scope.py',
    'src/wcomr/policy_generator_r1/__init__.py','src/wcomr/policy_generator_r1/interval_grammar.py')
REMOTE=r'''
import base64,gzip,hashlib,json,os,pathlib,subprocess,time
p=json.loads(gzip.decompress(base64.b64decode(__import__('sys').stdin.read().splitlines()[-1])))
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
stage=root/'.sync/cara-f19-real-B1-saved-CPU-r1-20261103'
name=stage.name
image='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
base=root/'.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102'
assets=root/'outputs/cara-ig-b1-r2-20261027/assets'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def write_new(path,value):
 with path.open('x') as stream:stream.write(json.dumps(value,indent=2)+'\n')
def inspect():
 q=subprocess.run(['docker','inspect',name],capture_output=True,text=True)
 if q.returncode:
  if 'No such object' in q.stderr:return None
  raise RuntimeError(q.stderr[-500:])
 return json.loads(q.stdout)[0]
def capture():
 if not (stage/'intent.json').exists():return dict(status='NO_F19_CPU_INTENT',GPU_submissions=0)
 intent=json.loads((stage/'intent.json').read_text());reg=json.loads((stage/'registration.json').read_text())
 assert sha((stage/'registration.json').read_bytes())==intent['registration_sha256']
 assert all(sha((stage/k).read_bytes())==v for k,v in reg['files'].items())
 c=inspect()
 if c is None:return dict(status='ORIGINAL_F19_CPU_UNKNOWN_NO_RETRY',intent=intent,GPU_submissions=0)
 h=c['HostConfig'];env=c['Config']['Env']
 assert c['Image']==image and not h.get('DeviceRequests')
 assert h['Memory']==h['MemorySwap']==8*2**30 and h['NanoCpus']==2000000000
 assert h['CpusetCpus']=='4,5' and h['NetworkMode']=='none' and h['ReadonlyRootfs']
 assert {'CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void'}<=set(env)
 result=dict(status='ORIGINAL_F19_SAVED_CPU_ACTIVE' if c['State']['Running'] else 'ORIGINAL_F19_SAVED_CPU_TERMINAL',
  container_id=c['Id'],state=c['State'],host_config=h,intent=intent,registration=reg,
  source_hashes_equal=True,GPU_submissions=0,ledger_accessed=False,
  progress=json.loads((stage/'progress.json').read_text()) if (stage/'progress.json').exists() else None)
 if not c['State']['Running']:
  logs=subprocess.run(['docker','logs','--tail','25',name],capture_output=True,text=True)
  result['log_tail']=(logs.stdout+logs.stderr)[-5000:]
  if (stage/'result.json').exists():
   raw=(stage/'result.json').read_bytes();result.update(result_sha256=sha(raw),result=json.loads(raw))
 return result
if p['mode']=='capture' or (stage/'intent.json').exists():
 print(json.dumps(capture()));raise SystemExit
assert inspect() is None,'Existing container without this intent; inspect, never replay'
assert not stage.exists(),'Partial stage retained; inspect before any continuation'
raw=(assets/'manifest.json').read_bytes();assert sha(raw)==p['manifest_sha256']
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert mem>=12*2**30 and {4,5}<=os.sched_getaffinity(0)
launch_raw=(base/'GPU-launch.json').read_bytes()
assert sha(launch_raw)=='86f01c9cebe0d45770c42855f3094baa428c6ef837c5371cb9d4b1afad652fcd'
launch=json.loads(launch_raw);runtime_python=launch['commands']['runner'][0]
assert runtime_python==str(root/'envs/wc-cosmos-py310-cu128-r3/bin/python')
old_command=launch['commands']['container_cli']
runtime_env=[old_command[i+1] for i,v in enumerate(old_command[:-1]) if v=='-e' and old_command[i+1].split('=',1)[0] in ('LD_LIBRARY_PATH','PATH')]
subprocess.run(['docker','image','inspect',image],check=True,stdout=subprocess.DEVNULL)
stage.mkdir(mode=0o700);(stage/'scratch').mkdir()
files={}
for relative_name,b64 in p['files'].items():
 relative=pathlib.Path(relative_name);assert not relative.is_absolute() and '..' not in relative.parts
 raw=base64.b64decode(b64);assert sha(raw)==p['hashes'][relative_name]
 target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);files[relative_name]=sha(raw)
reg=dict(files=files,manifest_sha256=p['manifest_sha256'],B1_assets_readonly=True,
 original_runtime_launch_sha256=sha(launch_raw),scope='B1_SAVED_LOCAL_CFG_ONLY_NO_HEAD_OR_ENDPOINT_INFERENCE')
write_new(stage/'registration.json',reg)
intent=dict(registration_sha256=sha((stage/'registration.json').read_bytes()),created_unix=time.time(),
 stage=str(stage),container=stage.name,mem_available_bytes=mem,CPU_wall_limit_seconds=1200,
 GPU_submissions=0,ledger_accessed=False,original_asset_mutation_allowed=False)
write_new(stage/'intent.json',intent)
command=['docker','run','--detach','--name',stage.name,'--label','cara.F19.saved='+intent['registration_sha256'],
 '--cpus','2','--cpuset-cpus','4,5','--memory','8g','--memory-swap','8g','--pids-limit','256',
 '--network','none','--read-only','--user',str(os.getuid())+':'+str(os.getgid()),
 '-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void','-e','PYTHONDONTWRITEBYTECODE=1',
 '-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2','-e','TMPDIR=/work/scratch',
 '-v',str(stage)+':/work:rw','-v',str(assets)+':/input:ro','-v',str(base/'src')+':/source:ro',
 '-w','/work']
for folder in ('envs','system-libs-r1'):command.extend(['-v',str(root/folder)+':'+str(root/folder)+':ro'])
for value in runtime_env:command.extend(['-e',value])
command.extend([image,'timeout','--signal=TERM','--kill-after=15s','1200',runtime_python,
 '/work/scripts/analyze_cara_f19_saved_tensor_r2.py','--assets','/input','--output','/work/result.json',
 '--progress','/work/progress.json','--manifest-sha256',p['manifest_sha256'],
 '--base-src','/source','--overlay-src','/work/src'])
write_new(stage/'command.json',command)
run=subprocess.run(command,capture_output=True,text=True)
write_new(stage/'launch.json',dict(exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr))
if run.returncode:print(json.dumps(dict(status='CPU_LAUNCH_FAILED_NO_RETRY',intent=intent,error=run.stderr[-1000:],GPU_submissions=0)))
else:print(json.dumps(capture()))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','capture'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ssh-prefix',type=Path,
        default=ROOT/'.sync/cara-C1-capture-ssh-v6.json')
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    mapping={name:(ROOT/name).read_bytes() for name in FILES} if args.mode=='prepare' else {}
    payload=dict(mode=args.mode,manifest_sha256='5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa',
        files={k:base64.b64encode(v).decode() for k,v in mapping.items()},
        hashes={k:hashlib.sha256(v).hexdigest() for k,v in mapping.items()})
    base=json.loads(args.ssh_prefix.read_text())
    base[1:1]=['-C','-o','ControlMaster=auto','-o','ControlPersist=300',
        '-o','ControlPath=/tmp/cara-f19-saved-CPU-task.sock']
    secret=password()
    command="sudo -S -p '' -u gaokuangda -g docker python3 -c "+shlex.quote(REMOTE)
    started=time.time()
    try:
        packet=base64.b64encode(gzip.compress(json.dumps(payload).encode())).decode()
        run=subprocess.run(base+[command],input=secret+'\n'+packet+'\n',
            capture_output=True,text=True,timeout=55)
        value=dict(mode=args.mode,started_unix=started,observed_unix=time.time(),exit_code=run.returncode,
            stderr=run.stderr.replace(secret,'[REDACTED]')[-1500:],GPU_submissions=0,
            operator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if run.returncode==0:value['capture']=json.loads(run.stdout)
    except subprocess.TimeoutExpired:
        value=dict(mode=args.mode,status='TRANSPORT_TIMEOUT_CAPTURE_ORIGINAL_ONLY',
            started_unix=started,observed_unix=time.time(),GPU_submissions=0)
    with args.output.open('x') as stream:
        stream.write(json.dumps(value,indent=2,allow_nan=False)+'\n')
    capture=value.get('capture',{})
    print(json.dumps(dict(report=str(args.output),exit_code=value.get('exit_code'),
        status=capture.get('status',value.get('status')),state=capture.get('state'),
        progress=capture.get('progress'),stderr=value.get('stderr'),log_tail=capture.get('log_tail'))))


if __name__=='__main__':
    main()
