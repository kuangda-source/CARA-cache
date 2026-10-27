"""Bounded GPU-hidden CPU diagnostics on settled read-only original assets."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import cara_two_card_transport_r1 as transport

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-scout-mechanism-saved-r1-20261027'
MANIFEST='5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa'

PREFLIGHT=r'''
import pathlib,json,sys,hashlib,os,time,subprocess
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
out=root/'outputs/cara-ig-b1-r2-20261027';assets=out/'assets';stage=root/'.sync'/p['stage_name']
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
assert sha(assets/'manifest.json')==p['manifest_sha256']
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert mem>=12*2**30 and {4,5}<=os.sched_getaffinity(0)
v=os.statvfs(root);assert v.f_bavail*v.f_frsize>2*2**30
for n,h in p['original_hashes'].items():assert sha(out/n)==h
ids=subprocess.run(['docker','ps','-q'],capture_output=True,text=True,check=True).stdout.split()
containers=[]
for i in ids:
 c=json.loads(subprocess.run(['docker','inspect',i],capture_output=True,text=True,check=True).stdout)[0]
 containers.append(dict(name=c['Name'],cpuset=c['HostConfig']['CpusetCpus']))
assert not containers,'Review active CPU container allocations before admission'
assert not stage.exists(),'Recover the existing diagnostic; do not relaunch'
os.nice(10)
subprocess.run(['ionice','-c','3','-p',str(os.getpid())],check=True,capture_output=True)
m=json.loads((assets/'manifest.json').read_text());refs=m['unique_anchors']+[r['artifact'] for r in m['states']]
assert len(refs)==32 and len({r['name'] for r in refs})==32
verified=[];start=time.monotonic()
for r in refs:
 f=assets/r['name'];assert f.resolve().parent==assets.resolve() and not f.is_symlink()
 assert f.stat().st_size==r['bytes'] and sha(f)==r['sha256']
 verified.append(dict(name=r['name'],bytes=r['bytes'],sha256=r['sha256']))
print(json.dumps(dict(status='SCOUT_MECHANISM_ASSETS_AND_CPU_RESOURCE_PREFLIGHT',observed_unix=time.time(),
 manifest_sha256=p['manifest_sha256'],verified=verified,hash_wall_seconds=time.monotonic()-start,
 MemAvailable=mem,load=os.getloadavg(),containers=containers,disk_available=v.f_bavail*v.f_frsize,
 assets=str(assets),stage=str(stage),new_GPU_submissions=0,ledger_writes=0)))
'''

LAUNCH=r'''
import pathlib,json,sys,os,subprocess,time,shutil,base64,hashlib
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
base=pathlib.Path(p['CPU']['launch']['stage']);stage=root/'.sync'/p['stage_name']
source=pathlib.Path(p['capture']['stage']);out=root/'outputs/cara-ig-b1-r2-20261027'
read=lambda f:json.loads(f.read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
pre=p['preflight'];assert pre['stage']==str(stage) and time.time()-pre['observed_unix']<1800
assert pre['manifest_sha256']==sha(out/'assets/manifest.json')==p['manifest_sha256']
assert not stage.exists(),'Recover existing stage, never duplicate launch'
for r in pre['verified']:assert (out/'assets'/r['name']).stat().st_size==r['bytes']
mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
assert mem>=12*2**30 and {4,5}<=os.sched_getaffinity(0)
assert not subprocess.run(['docker','ps','-q'],capture_output=True,text=True,check=True).stdout.strip()
assert sha(base/'registration.json')==p['CPU']['launch']['registration_sha256']
reg=read(base/'registration.json');hashes={}
assert all(sha(root/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
stage.mkdir(mode=0o700)
for n,h in reg['payload_sha256'].items():
 assert sha(base/n)==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,target);hashes[n]=h
for n,b64 in p['files'].items():
 raw=base64.b64decode(b64);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
 (stage/n).write_bytes(raw);hashes[n]=p['hashes'][n]
(stage/'cache').mkdir(exist_ok=True);(stage/'cache/runtime').symlink_to(root/'runtime',target_is_directory=True)
registration=dict(source_revision=p['revision'],payload_sha256=hashes,preflight=pre,
 original_result_sha256=p['capture']['files']['B1-results.json']['sha256'],
 original_billing_sha256=p['capture']['files']['billing']['sha256'],timeout_seconds=1800)
(stage/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
sys.path[:0]=[str(stage/'src'),str(stage/'scripts'),str(root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022')]
from four_card_bank24_execution_tools_r1 import process_environment
from four_card_policy_assets_port_r1 import container_command
from wcomr.gpu_budget_pool_v2 import process_identity
cmd=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
cmd[cmd.index('--cpus')+1]='2';cmd[cmd.index('--memory')+1]='8g'
cmd[2:2]=['--cpuset-cpus','4,5','-v',str(out)+':'+str(out)+':ro']
i=cmd.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'))
ep=cmd.index('--entrypoint')+1;python=cmd[ep];cmd[ep]='/usr/bin/timeout'
assert i==ep+2
cmd=cmd[:i]+['--signal=TERM','--kill-after=10s','1800',python,
 str(stage/'scripts/analyze_cara_scout_mechanism_saved_r1.py'),'--assets',str(out/'assets'),
 '--manifest-sha256',p['manifest_sha256'],'--output',str(stage/'analysis.json')]
assert '--gpus' not in cmd and any(x=='CUDA_VISIBLE_DEVICES=' for x in cmd)
(stage/'command.json').write_text(json.dumps(cmd))
with (stage/'CPU.log').open('x') as log:
 child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
v=dict(status='SCOUT_SAVED_MECHANISM_CPU_LAUNCHED',stage=str(stage),container=stage.name+'-cpu',
 registration_sha256=sha(stage/'registration.json'),identity=process_identity(child.pid),started_unix=time.time(),
 source_revision=p['revision'],GPU_submissions=0,CPU_limit=2,memory_bytes=8*2**30,timeout_seconds=1800)
(stage/'launch.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
'''

CAPTURE=r'''
import pathlib,json,sys,hashlib,subprocess,time
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(s/'registration.json')==L['registration_sha256'];reg=json.loads((s/'registration.json').read_text())
c=json.loads(subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,check=True).stdout)[0]
p=s/'analysis.json';config=c['HostConfig']
print(json.dumps(dict(status='SCOUT_SAVED_MECHANISM_CPU_CAPTURE',observed_unix=time.time(),launch=L,
 original_result_sha256=reg['original_result_sha256'],original_billing_sha256=reg['original_billing_sha256'],
 source_hashes_equal=all(sha(s/n)==h for n,h in reg['payload_sha256'].items()),
 container_state=c['State'],device_requests=config['DeviceRequests'],cpuset=config['CpusetCpus'],
 memory_bytes=config['Memory'],nano_cpus=config['NanoCpus'],mounts=c['Mounts'],
 result=json.loads(p.read_text()) if p.exists() else None,result_sha256=sha(p) if p.exists() else None,
 log_tail=(s/'CPU.log').read_text(errors='replace')[-3000:],GPU_submissions=0)))
'''


def read(p):return json.loads(Path(p).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['preflight','launch','capture','recover'])
    p.add_argument('--preflight',type=Path);p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    original=read(ROOT/'reports/cara_IG_B1_R2_terminal_20261027.json')
    if a.command=='recover':
        code="import json,pathlib; p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+STAGE+"/launch.json'); print(p.read_text() if p.exists() else json.dumps({'status':'NO_LAUNCH','stage_exists':p.parent.exists()}))"
        result=transport.ssh(code,docker_group=True)
    elif a.command=='capture':result=transport.ssh(CAPTURE,read(a.launch_ref),docker_group=True)
    elif a.command=='preflight':
        result=transport.ssh(PREFLIGHT,dict(stage_name=STAGE,manifest_sha256=MANIFEST,
            original_hashes={n:original['files'][k]['sha256'] for n,k in
                [('billing.json','billing'),('B1-results.json','B1-results.json'),('post-results.json','post-results.json')]}),docker_group=True,timeout=600)
    else:
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==revision
        names=['scripts/analyze_cara_scout_mechanism_saved_r1.py'];files={n:(ROOT/n).read_bytes() for n in names}
        assert all(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)==b for n,b in files.items())
        result=transport.ssh(LAUNCH,dict(stage_name=STAGE,manifest_sha256=MANIFEST,preflight=read(a.preflight),
            capture=original,CPU=read(ROOT/'reports/cara_IG_grouped_two_card_CPU_finished_r1_20261027.json'),
            revision=revision,files={n:base64.b64encode(b).decode() for n,b in files.items()},
            hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}),docker_group=True)
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:result.get(k) for k in ('status','container_state','result_sha256')}))
if __name__=='__main__':main()
