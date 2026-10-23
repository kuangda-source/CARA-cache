#!/usr/bin/env python3
"""New bounded PG CPU stage alongside the untouched exclusive price GPU job."""
import argparse,base64,hashlib,json,subprocess,sys
from pathlib import Path
from wc_four_card_policy_assets_r1 import ssh,write,read,sha,REPO
from four_card_policy_assets_port_r1 import ROOT
BASE=ROOT+'/.sync/wc-policy-assets-fourcard-full1624-r2-20261022'
FILES=['src/wcomr/policy_generator_r1/'+p.name for p in (REPO/'src/wcomr/policy_generator_r1').glob('*.py')]+[
 'tests/check_cara_pg_production_sampling_cpu_r1.py','scripts/check_cara_pg_p1_production_cpu_r1.py',
 'scripts/check_wc_policy_price_refresh_cpu_r1.py','src/wcomr/policy_price_refresh_production_r1.py',
 'src/wcomr/policy_price_refresh_contract_r1.py','plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json']
DEPLOY=r'''
import base64,hashlib,json,os,pathlib,shutil,subprocess,sys,time
p=json.load(sys.stdin);root=pathlib.Path(p['root']);base=pathlib.Path(p['base']);stage=root/'.sync'/p['stage_name']
assert stage.parent==root/'.sync' and stage.name.startswith('cara-pg-p1-CPU-')
if stage.exists():raise ValueError('Immutable CPU stage already exists; capture original or choose new revision')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((base/'registration.json').read_text())
assert sha(base/'registration.json')==p['base_registration_sha256']
mem=int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
disk=shutil.disk_usage(root).free
assert mem>=24*2**30 and disk>=40*2**30
for n,h in reg['payload_sha256'].items():assert not (base/n).is_symlink() and sha(base/n)==h
stage.mkdir(mode=0o700)
for n in reg['payload_sha256']:
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,target)
for n,encoded in p['files'].items():
 raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
names=set(reg['payload_sha256'])|set(p['files'])
new=dict(namespace='CARA_PG_P1_CPU_R1',stage=str(stage),source_revision=p['revision'],payload_sha256={n:sha(stage/n) for n in sorted(names)},runtime_source_sha256=reg['runtime_source_sha256'])
(stage/'registration.json').write_text(json.dumps(new,indent=2)+chr(10))
bank=root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022';sys.path.insert(0,str(bank))
from four_card_bank24_execution_tools_r1 import process_environment
sys.path.insert(0,str(stage/'scripts'))
from four_card_policy_assets_port_r1 import container_command
command=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
command[command.index('--memory')+1]='4g';command[command.index('--cpus')+1]='1'
start=command.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'))
command[start:]=[str(stage/'scripts/check_cara_pg_p1_production_cpu_r1.py'),'--project',str(root),'--stage',str(stage),'--output',str(stage/'PG-production-CPU.json')]
with (stage/'PG-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
from four_card_bank24_container_transport_r1 import identity
launch=dict(status='PG_BOUNDED_CPU_RUNNING',stage=str(stage),source_revision=p['revision'],registration_sha256=sha(stage/'registration.json'),
 identity=identity(child.pid),container=stage.name+'-cpu',started_unix=time.time(),GPU_submissions=0,ledger_written=False,
 resource_admission=dict(MemAvailable=mem,disk_free=disk,cpus=1,memory_GiB=4),active_GPU_stage_modified=False)
(stage/'PG-CPU-launch.json').write_text(json.dumps(launch,indent=2)+chr(10));print(json.dumps(launch))
'''
CAPTURE=r'''
import hashlib,json,pathlib,subprocess,sys,time
L=json.load(sys.stdin);stage=pathlib.Path(L['stage']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
r=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=20,check=True);c=json.loads(r.stdout)[0]
assert c['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
out=dict(status='PG_ORIGINAL_CPU_CAPTURE',launch=L,observed_unix=time.time(),registration=reg,
 container=dict(state=c['State'],image=c['Image'],readonly_root=c['HostConfig']['ReadonlyRootfs'],devices=c['HostConfig'].get('Devices') or [],device_requests=c['HostConfig'].get('DeviceRequests') or [],nano_cpus=c['HostConfig']['NanoCpus'],memory_bytes=c['HostConfig']['Memory']),
 payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},runtime_actual_sha256={n:sha(pathlib.Path('/data20t/gaokuangda/worldcache_workspace/runtime')/n) for n in reg['runtime_source_sha256']},GPU_submissions=0)
path=stage/'PG-production-CPU.json';out['proof']=dict(exists=path.exists())
if path.exists():out['proof'].update(data=json.loads(path.read_text()),sha256=sha(path))
with (stage/'PG-CPU.log').open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-10000));out['log_tail']=f.read().decode(errors='replace')
print(json.dumps(out))
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['deploy','capture']);p.add_argument('--stage-name');p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.command=='capture':v=ssh(CAPTURE,read(a.launch_ref))
 else:
  revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip();files={};hashes={}
  for n in FILES:
   raw=subprocess.check_output(['git','show',revision+':'+n],cwd=REPO);assert raw==(REPO/n).read_bytes(),'Commit PG sources first'
   files[n]=base64.b64encode(raw).decode();hashes[n]=hashlib.sha256(raw).hexdigest()
  old=read(REPO/'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json')
  v=ssh(DEPLOY,dict(root=ROOT,base=BASE,base_registration_sha256=old['registration_sha256'],stage_name=a.stage_name,revision=revision,files=files,hashes=hashes))
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','container','observed_unix','resource_admission')}))
if __name__=='__main__':main()
