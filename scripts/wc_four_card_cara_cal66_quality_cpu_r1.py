#!/usr/bin/env python3
"""Fresh immutable five-model CPU only; never installs into the P1 environment.

Resources and an offline dependency overlay must already be staged under the
owned quality cache. Preflight can return gaps without creating a stage.
"""
import argparse,base64,hashlib,json,sys,subprocess
from pathlib import Path
from wc_four_card_policy_assets_r1 import write,read,REPO,base_ssh,bridge,RUNTIME_REF
from wc_four_card_cara_pg_cpu_r1 import BASE

# Large immutable dependency inventories are CPU-only reads. A longer bounded
# transport deadline does not extend any GPU or postprocessing budget.
def ssh(code,data=None):
    return base_ssh(bridge(code,read(REPO/RUNTIME_REF)).replace('timeout=160','timeout=840'),data,timeout=900)

PREFLIGHT=r'''
import hashlib,json,os,pathlib,shutil,sys,time
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
cache=root/'cache/cara-pg-p2-quality-r1';gaps=[];resources={}
assert not cache.is_symlink() and cache.resolve().is_relative_to((root/'cache').resolve())
for role,r in p['packet']['resources'].items():
 path=cache/(role+'.pth');okay=path.is_file() and not path.is_symlink() and path.stat().st_uid==os.getuid() and path.stat().st_size==r['bytes']
 resources[role]=dict(path=str(path),bytes=r['bytes'],sha256=r['sha256'])
 if not okay:gaps.append('RESOURCE:'+role)
overlay=cache/'dependency-overlay';lock=cache/'dependency-overlay-manifest.json'
assert not overlay.is_symlink() and overlay.resolve().is_relative_to(cache.resolve())
if not overlay.is_dir() or not lock.is_file():gaps.append('OFFLINE_DEPENDENCY_OVERLAY')
else:
 inventory=json.loads(lock.read_text())
 assert inventory['base_environment_modified'] is False and inventory['files']
 for n,h in inventory['files'].items():
  rel=pathlib.PurePosixPath(n);f=overlay/n
  assert not rel.is_absolute() and '..' not in rel.parts and not f.is_symlink() and f.resolve().is_relative_to(overlay.resolve())
  assert hashlib.sha256(f.read_bytes()).hexdigest()==h
free=shutil.disk_usage(root).free
mem=int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
if free<40*2**30:gaps.append('DISK_BELOW_40_GIB')
if mem<32*2**30:gaps.append('MEMORY_BELOW_32_GIB')
snapshot=dict(status='QUALITY_CPU_PREFLIGHT_READY' if not gaps else 'QUALITY_CPU_PREFLIGHT_GAPS',observed_unix=time.time(),gaps=gaps,
 disk_free=free,MemAvailable=mem,resources=resources,overlay=str(overlay),GPU_submissions=0,base_environment_modified=False)
'''

DEPLOY=PREFLIGHT+r'''
if gaps:print(json.dumps(snapshot));sys.exit(0)
stage=root/'.sync'/p['stage_name'];assert stage.parent==root/'.sync' and stage.name.startswith('cara-pg-p2-quality-CPU-')
if stage.exists():raise ValueError('Existing original stage: recover/capture, never redispatch')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
for role,r in resources.items():assert sha(pathlib.Path(r['path']))==r['sha256']
base=pathlib.Path(p['base']);assert sha(base/'registration.json')==p['base_registration_sha256']
reg=json.loads((base/'registration.json').read_text())
for n,h in reg['payload_sha256'].items():assert sha(base/n)==h
for n,b64 in p['files'].items():
 rel=pathlib.PurePosixPath(n);assert not rel.is_absolute() and '..' not in rel.parts
 assert hashlib.sha256(__import__('base64').b64decode(b64)).hexdigest()==p['packet']['payload_sha256'][n]
assert set(p['files'])==set(p['packet']['payload_sha256'])
stage.mkdir(mode=0o700)
for n,b64 in p['files'].items():
 f=stage/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(__import__('base64').b64decode(b64))
resources_raw=json.dumps(dict(resources=resources),indent=2)+'\n';(stage/'model-resources.json').write_text(resources_raw)
payload=dict(p['packet']['payload_sha256']);payload['model-resources.json']=sha(stage/'model-resources.json')
registration=dict(purpose='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING',roles=p['packet']['roles'],
 source_revision=p['packet']['source_revision'],stage=str(stage),payload_sha256=payload,
 official_VBench_commit=p['packet']['official_VBench_commit'],resource_capture_sha256=p['packet_sha256'],
 GPU_submissions=0,original_generation_stages_written=False,ledger_written=False)
(stage/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
sys.path.insert(0,str(base/'scripts'))
from four_card_policy_assets_port_r1 import container_command
bank=root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022';sys.path.insert(0,str(bank))
from four_card_bank24_execution_tools_r1 import process_environment
import subprocess
cmd=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
cmd[cmd.index('--cpus')+1]='1';cmd[cmd.index('--memory')+1]='8g'
for i,arg in enumerate(cmd):
 if arg.startswith('PYTHONPATH='):cmd[i]='PYTHONPATH='+str(stage/'scripts')+':'+str(stage/'src')+':'+str(overlay)
start=cmd.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'))
cmd[start:]=[str(stage/'scripts/evaluate_wc_N10_models_cpu_bundle_r1.py'),'--stage',str(stage)]
with (stage/'CPU-model-bundle.log').open('x') as log:
 child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
fields=(pathlib.Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split();now=time.time()
launch=dict(status='N10_FULL_FIVE_METRIC_MODEL_CPU_SINGLE_DISPATCHED',stage=str(stage),source_revision=registration['source_revision'],
 registration_sha256=sha(stage/'registration.json'),pid=child.pid,start_ticks=int(fields[19]),roles=registration['roles'],
 container=stage.name+'-cpu',started_unix=now,first_collection_not_before_unix=now,
 resource_admission=snapshot,dependency_overlay_manifest_sha256=sha(lock),GPU_submissions=0,ledger_written=False)
launch.update(controller_source_revision=p['controller_source_revision'],controller_source_sha256=p['controller_source_sha256'])
(stage/'CPU-model-launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''

CAPTURE=r'''
import base64,hashlib,json,pathlib,subprocess,sys,time
L=json.load(sys.stdin);stage=pathlib.Path(L['stage']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert stage.parent==pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync') and stage.name.startswith('cara-pg-p2-quality-CPU-')
assert sha(stage/'registration.json')==L['registration_sha256'];reg=json.loads((stage/'registration.json').read_text())
c=json.loads(subprocess.check_output(['docker','inspect',L['container']],text=True))[0]
assert c['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
live=c['State']['Running'];files={}
for n in ['model-resources.json','CPU-model-bundle-result.json']+['CPU-model-'+r+'.json' for r in L['roles']]:
 f=stage/n;row=dict(exists=f.is_file())
 if f.is_file():
  raw=f.read_bytes();row.update(sha256=hashlib.sha256(raw).hexdigest(),raw_base64=base64.b64encode(raw).decode(),data=json.loads(raw))
 files[n]=row
print(json.dumps(dict(status='N10_ORIGINAL_FIVE_MODEL_CPU_ONCE_CAPTURE',launch=L,observed_unix=time.time(),registration=reg,
 registration_sha256=L['registration_sha256'],payload_verified={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()},
 original_process_alive=live,role_result_files_present=[r for r in L['roles'] if files['CPU-model-'+r+'.json']['exists']],files=files,
 container=dict(state=c['State'],readonly_root=c['HostConfig']['ReadonlyRootfs'],devices=c['HostConfig'].get('Devices') or [],
 device_requests=c['HostConfig'].get('DeviceRequests') or [],network=c['HostConfig']['NetworkMode'],nano_cpus=c['HostConfig']['NanoCpus'],memory=c['HostConfig']['Memory']),
 GPU_submissions=0,ledger_written=False)))
'''

def accept(v):
    from accept_wc_N10_models_cpu_r1 import accept as model_accept
    c=v['container']
    if hashlib.sha256((json.dumps(v['registration'],indent=2)+'\n').encode()).hexdigest()!=v['launch']['registration_sha256']:
        raise ValueError('Original registered model source bytes changed')
    if c['state']['Running'] or c['state']['ExitCode']!=0 or not c['readonly_root'] or c['devices'] or c['device_requests'] or c['network']!='none' or c['nano_cpus']!=10**9 or c['memory']!=8*2**30:
        raise ValueError('Actual isolated model CPU container must exit0')
    for r in v['files'].values():
        if r['exists']:
            raw=base64.b64decode(r['raw_base64'],validate=True)
            if hashlib.sha256(raw).hexdigest()!=r['sha256'] or json.loads(raw)!=r['data']:raise ValueError('Original model CPU bytes changed')
    return model_accept(v)

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['preflight','deploy','capture','accept'])
    for n in ('packet','launch-ref','capture','output'):p.add_argument('--'+n,type=Path,required=n=='output')
    p.add_argument('--stage-name');a=p.parse_args();assert not a.output.exists()
    if a.command=='accept':
        raw=a.capture.read_bytes();v=accept(json.loads(raw));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest())
    elif a.command=='capture':v=ssh(CAPTURE,read(a.launch_ref))
    else:
        packet=read(a.packet);assert not packet['missing'] and len(packet['roles'])==5
        data=dict(packet=packet)
        if a.command=='deploy':
            revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
            name=str(Path(__file__).resolve().relative_to(REPO));raw=Path(__file__).read_bytes()
            assert subprocess.check_output(['git','show',revision+':'+name],cwd=REPO)==raw,'Commit exact CPU controller first'
            files={n:base64.b64encode((Path(packet['source_root'])/n).read_bytes()).decode() for n in packet['payload_sha256']}
            old=read(REPO/'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json')
            data.update(files=files,stage_name=a.stage_name,base=BASE,base_registration_sha256=old['registration_sha256'],packet_sha256=hashlib.sha256(a.packet.read_bytes()).hexdigest(),controller_source_revision=revision,controller_source_sha256=hashlib.sha256(raw).hexdigest())
        v=ssh(DEPLOY if a.command=='deploy' else PREFLIGHT+'\nprint(json.dumps(snapshot))',data)
    write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','gaps','CPU_accepted','GPU_submissions')}))
if __name__=='__main__':main()
