"""S/Q CPU-only controller, reusing verified B1 environment and no GPU gate.

Immutable own stage, recovering on repetition. Copies code only, never assets.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_two_card_transport_r1 as transport

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-sq-cpu-r1-20261028'
MANIFEST='5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa'
OWN=('src/wcomr/sq_codec_r1.py','src/wcomr/sq_risk_r1.py','tests/test_sq_preparation_r1.py',
     'tests/test_scout_readout_v22.py','scripts/cara_sq_saved_cpu_r1.py')

LAUNCH=r'''
import pathlib,json,sys,os,subprocess,time,shutil,base64,hashlib,fcntl
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
stage=root/'.sync'/p['stage_name'];assets=root/'outputs/cara-ig-b1-r2-20261027/assets'
base=pathlib.Path(p['base']['stage']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
# Scope fence is independent of Git. It does not reserve a GPU or budget.
with (root/'.sync/cara-sq-CPU-only-r1.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if stage.exists():
  launch=stage/'launch.json'
  print(json.dumps(dict(status='RECOVER_EXISTING_STAGE_NO_REDISPATCH',stage=str(stage),launch=json.loads(launch.read_text()) if launch.exists() else None)))
  sys.exit(0)
 assert not subprocess.check_output(['docker','ps','-q'],text=True).strip(),'Review current CPU allocations'
 mem=int(next(l.split()[1] for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
 assert mem>=12*2**30 and {4,5}<=os.sched_getaffinity(0)
 v=os.statvfs(root);assert v.f_bavail*v.f_frsize>=2*2**30
 assert sha(assets/'manifest.json')==p['manifest_sha256']
 assert sha(base/'registration.json')==p['base']['registration_sha256']
 reg=json.loads((base/'registration.json').read_text())
 runtime_hashes=reg.get('runtime_source_sha256',reg.get('original_runtime_sha256'))
 assert runtime_hashes and all(sha(root/'runtime'/n)==h for n,h in runtime_hashes.items())
 stage.mkdir(mode=0o700);hashes={}
 for n,h in reg['payload_sha256'].items():
  assert sha(base/n)==h
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,target);hashes[n]=h
 for n,b64 in p['files'].items():
  raw=base64.b64decode(b64);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);hashes[n]=p['hashes'][n]
 (stage/'cache').mkdir(exist_ok=True);(stage/'cache/runtime').symlink_to(root/'runtime',target_is_directory=True)
 registration=dict(schema='CARA_SQ_CPU_ONLY_R1',source_revision=p['revision'],payload_sha256=hashes,
  runtime_source_sha256=runtime_hashes,asset_manifest_sha256=p['manifest_sha256'],GPU_submissions=0,
  resource_limits=dict(CPUs=2,cpuset='4,5',RAM_bytes=8*2**30,wall_seconds=1800,allocated_vCPUh_max=1.,
  output_bytes_max=64*2**20,assets_readonly=True,network='none',GPU='hidden'),base=p['base'])
 (stage/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
 sys.path[:0]=[str(stage/'src'),str(stage/'scripts'),str(root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022')]
 from four_card_bank24_execution_tools_r1 import process_environment
 from four_card_policy_assets_port_r1 import container_command
 from wcomr.gpu_budget_pool_v2 import process_identity
 cmd=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
 cmd[cmd.index('--cpus')+1]='2';cmd[cmd.index('--memory')+1]='8g'
 cmd[2:2]=['--cpuset-cpus','4,5','--memory-swap','8g','--ulimit','fsize=67108864:67108864','-v',str(assets.parent)+':'+str(assets.parent)+':ro']
 i=cmd.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'));ep=cmd.index('--entrypoint')+1
 python=cmd[ep];cmd[ep]='/usr/bin/timeout';assert i==ep+2
 cmd=cmd[:i]+['--signal=TERM','--kill-after=10s','1800','/usr/bin/ionice','-c','3',python,
  str(stage/'scripts/cara_sq_saved_cpu_r1.py'),'--assets',str(assets),'--manifest-sha256',p['manifest_sha256'],'--output',str(stage/'analysis.json')]
 assert '--gpus' not in cmd and 'CUDA_VISIBLE_DEVICES=' in cmd and 'NVIDIA_VISIBLE_DEVICES=void' in cmd
 (stage/'command.json').write_text(json.dumps(cmd))
 with (stage/'CPU.log').open('x') as log:
  child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 value=dict(status='SQ_GPU_HIDDEN_CPU_PREPARATION_LAUNCHED',stage=str(stage),container=stage.name+'-cpu',
  source_revision=p['revision'],registration_sha256=sha(stage/'registration.json'),identity=process_identity(child.pid),
  started_unix=time.time(),resource_limits=registration['resource_limits'],new_GPU_submissions=0,ledger_writes=0)
 (stage/'launch.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
'''

CAPTURE=r'''
import pathlib,json,sys,hashlib,subprocess,time
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(s/'registration.json')==L['registration_sha256'];reg=json.loads((s/'registration.json').read_text())
c=json.loads(subprocess.check_output(['docker','inspect',L['container']],text=True))[0];h=c['HostConfig'];p=s/'analysis.json'
print(json.dumps(dict(status='SQ_CPU_PREPARATION_CAPTURE',observed_unix=time.time(),launch=L,
 source_hashes_equal=all(sha(s/n)==v for n,v in reg['payload_sha256'].items()),
 runtime_hashes_equal=all(sha(pathlib.Path('/data20t/gaokuangda/worldcache_workspace/runtime')/n)==v for n,v in reg['runtime_source_sha256'].items()),
 container_state=c['State'],host_config={k:h[k] for k in ('DeviceRequests','NanoCpus','Memory','MemorySwap','CpusetCpus','NetworkMode','ReadonlyRootfs')},
 mounts=c['Mounts'],image=c['Image'],result=json.loads(p.read_text()) if p.exists() else None,
 result_sha256=sha(p) if p.exists() else None,log_tail=(s/'CPU.log').read_text(errors='replace')[-4000:],
 new_GPU_submissions=0,ledger_writes=0)))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('launch','capture','recover'))
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    if a.command=='launch':
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==revision
        files={n:(ROOT/n).read_bytes() for n in OWN}
        assert all(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)==v for n,v in files.items())
        base=json.loads((ROOT/'reports/cara_IG_grouped_two_card_CPU_finished_r1_20261027.json').read_text())['launch']
        value=transport.ssh(LAUNCH,dict(stage_name=STAGE,manifest_sha256=MANIFEST,base=base,revision=revision,
            files={n:base64.b64encode(v).decode() for n,v in files.items()},hashes={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}),docker_group=True)
    elif a.command=='capture':
        value=transport.ssh(CAPTURE,json.loads(a.launch_ref.read_text()),docker_group=True)
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+STAGE+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_SQ_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value=transport.ssh(code,docker_group=True)
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
