"""Recover/start/capture the exact32 direct CPU B1 transfer; no GPU commands."""
import argparse
import base64
import json
import os
from pathlib import Path
import shlex
import subprocess

from cara_two_card_transport_r1 import four_ssh,password

ROOT=Path(__file__).resolve().parents[1]
PROFILE='plans/cara_next_stage_20261028/sq/B1_PORT_CPU_PROFILE_R1.json'
STAGE='/home/user/cara_sq_b1_port_cpu_r1_20261029'
FILES=('src/wcomr/__init__.py','src/wcomr/gpu_budget_pool_v2.py',
       'src/wcomr/sq_b1_port_r1.py','scripts/cara_sq_b1_port_worker_r1.py',PROFILE)


def source_endpoint():
    cfg={}
    for line in subprocess.check_output(['ssh','-G','two_card_lan'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).splitlines():
        key,_,value=line.partition(' ')
        if key in ('hostname','user','port','hostkeyalias','userknownhostsfile'):cfg[key]=value
    lookup=cfg.get('hostkeyalias',cfg['hostname'])
    if lookup=='none':lookup=cfg['hostname']
    if cfg['port']!='22':lookup='['+lookup+']:'+cfg['port']
    pins={}
    for name in shlex.split(cfg['userknownhostsfile']):
        path=Path(os.path.expanduser(name))
        if not path.is_file():continue
        query=subprocess.run(['ssh-keygen','-F',lookup,'-f',str(path)],capture_output=True,text=True)
        for line in query.stdout.splitlines():
            fields=line.split()
            if line.startswith(('#','@')) or len(fields)!=3:continue
            pins[fields[1]]=fields[2]
    if not pins:raise ValueError('Existing verified Mac source host-key pin required; keyscan is not trust')
    return {key:cfg[key] for key in ('hostname','user','port')},pins


START=r'''
import base64,fcntl,hashlib,json,os,pathlib,subprocess,sys,time
p=json.load(sys.stdin);s=pathlib.Path(p['stage']);project=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
sys.path.insert(0,str(project/'.sync/cara-sq-q1-saved-four-card-r1-20261028/src'))
from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
with pathlib.Path('/home/user/.cara-sq-b1-port-cpu-r1.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if s.exists():
  print(json.dumps(dict(status='B1_EXISTING_CPU_PORT_RECOVER_ONLY',stage=str(s),launch=json.loads((s/'launch.json').read_text()) if (s/'launch.json').exists() else None)));sys.exit(0)
 assert not subprocess.check_output(['docker','ps','-q'],text=True).strip(),'Preserve current CPU allocations'
 assert {4,5}<=os.sched_getaffinity(0)
 s.mkdir(mode=0o700);hashes={}
 for name,encoded in p['files'].items():
  raw=base64.b64decode(encoded);target=s/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);hashes[name]=hashlib.sha256(raw).hexdigest()
 profile=json.loads((s/p['profile_path']).read_text())
 assert profile['control_directory']==str(s) and profile['files']==32 and profile['asset_bytes']==20795567276
 reg=dict(source_revision=p['revision'],profile_path=p['profile_path'],endpoint=p['endpoint'],host_key_pins=p['pins'],payload_sha256=hashes,GPU_submissions=0,ledger_writes=0)
 atomic_json(s/'registration.json',reg)
 cmd=['/usr/bin/timeout','--signal=TERM','--kill-after=10s','7200','/usr/bin/ionice','-c','3','/usr/bin/python3','-u',str(s/'scripts/cara_sq_b1_port_worker_r1.py'),'--stage',str(s)]
 with (s/'intent.json').open('x') as f:json.dump(dict(command=cmd,created_unix=time.time(),GPU_submissions=0),f);f.flush();os.fsync(f.fileno())
 with (s/'CPU.log').open('x') as log:
  child=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',PYTHONDONTWRITEBYTECODE='1'))
  child.stdin.write(json.dumps(dict(source_password=p.pop('source_password'))).encode());child.stdin.close()
 result=dict(status='B1_EXACT32_DIRECT_CPU_PORT_STARTED',stage=str(s),source_revision=reg['source_revision'],registration_sha256=hashlib.sha256((s/'registration.json').read_bytes()).hexdigest(),identity=process_identity(child.pid),started_unix=time.time(),source_host='two_card',destination_host='four_card',planned_files=32,planned_bytes=20795567276,wall_seconds_max=7200,GPU_submissions=0,ledger_writes=0)
 atomic_json(s/'launch.json',result);print(json.dumps(result))
'''

CAPTURE=r'''
import hashlib,json,pathlib,sys,time
p=json.load(sys.stdin);s=pathlib.Path(p['stage']);project=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
sys.path.insert(0,str(project/'.sync/cara-sq-q1-saved-four-card-r1-20261028/src'))
from wcomr.gpu_budget_pool_v2 import same_live_process
def read(name):
 f=s/name;return json.loads(f.read_text()) if f.exists() else None
launch=read('launch.json')
if launch is None:print(json.dumps(dict(status='NO_ORIGINAL_B1_PORT_LAUNCH',stage_exists=s.exists(),intent=read('intent.json'))));sys.exit(0)
if p.get('launch') is not None:assert launch==p['launch'],'Recover the original B1 CPU port handle'
assert hashlib.sha256((s/'registration.json').read_bytes()).hexdigest()==launch['registration_sha256']
reg=read('registration.json');live=same_live_process(launch['identity'])
print(json.dumps(dict(status='B1_ORIGINAL_CPU_PORT_CAPTURE',observed_unix=time.time(),launch=launch,original_handle_live=live,payload_intact=all(hashlib.sha256((s/n).read_bytes()).hexdigest()==v for n,v in reg['payload_sha256'].items()),worker=read('worker.json'),progress=read('progress.json'),exit=read('exit.json'),result=read('result.json') if not live else None,log_tail=(s/'CPU.log').read_text(errors='replace')[-1800:] if (s/'CPU.log').exists() else None,GPU_submissions=0,ledger_writes=0)))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('recover','start','capture'))
    p.add_argument('--source-revision');p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original CPU transfer receipt')
    if args.command=='start':
        revision=subprocess.check_output(['git','rev-parse',(args.source_revision or 'HEAD')+'^{commit}'],cwd=ROOT,text=True).strip()
        published=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
        if subprocess.run(['git','merge-base','--is-ancestor',revision,published],cwd=ROOT).returncode:
            raise ValueError('Publish the exact CPU transfer source before starting')
        endpoint,pins=source_endpoint();files={name:subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT) for name in FILES}
        data=dict(stage=STAGE,profile_path=PROFILE,revision=revision,endpoint=endpoint,pins=pins,
            files={name:base64.b64encode(raw).decode() for name,raw in files.items()},source_password=password())
        try:value=four_ssh(START,data)
        finally:data.pop('source_password',None)
    else:
        launch=json.loads(args.launch_ref.read_text()) if args.launch_ref else None
        value=four_ssh(CAPTURE,dict(stage=STAGE,launch=launch))
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','original_handle_live','planned_files','planned_bytes')}))


if __name__=='__main__':main()
