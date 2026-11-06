#!/usr/bin/env python3
"""Immutable price-stage CPU transport. GPU dispatch stays closed until full lifecycle acceptance."""
import argparse
import base64
import json
from pathlib import Path
import subprocess
import sys
import time
from wc_four_card_policy_assets_r1 import ssh, read, sha, write, REPO
from four_card_policy_assets_port_r1 import ROOT, IMAGE

STAGE = ROOT+'/.sync/wc-policy-price-refresh-fourcard-full1624-r1-20261023'
BASE = ROOT+'/.sync/wc-policy-assets-fourcard-full1624-r2-20261022'
CAPTURE = 'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json'
ACCEPTED = 'reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json'
QUOTE = 'manifests/wc_policy_price_refresh_full1624_whole_quote_r1_20261023.json'
NEW_FILES = [
    'src/wcomr/policy_price_refresh_contract_r1.py','src/wcomr/policy_price_refresh_sampling_r1.py',
    'src/wcomr/policy_price_refresh_audit_r1.py','src/wcomr/policy_price_refresh_production_r1.py',
    'src/wcomr/policy_price_mode_guard_r1.py','scripts/wc_policy_price_host_guardian_r1.py',
    'tests/test_policy_price_refresh_exclusive_r1.py','src/wcomr/policy_price_exclusive_r1.py','src/wcomr/policy_asset_price_review_r1.py',
    'scripts/run_wc_policy_price_refresh_r1.py','scripts/postprocess_wc_policy_price_refresh_r1.py',
    'scripts/check_wc_policy_price_refresh_cpu_r1.py','scripts/wc_policy_price_refresh_worker_r1.py',
    'scripts/wc_four_card_price_refresh_r1.py','tests/check_policy_price_refresh_sampling_cpu_r1.py',
    'tests/test_policy_price_refresh_contract_r1.py','tests/test_policy_price_refresh_audit_r1.py']


def prepare(output):
    sys.path.insert(0,str(REPO/'src'))
    from wcomr.policy_price_refresh_production_r1 import RUN,COUNTS,PROFILE,VERSION,matrix
    cap=read(REPO/CAPTURE);accepted=read(REPO/ACCEPTED);quote=read(REPO/QUOTE)
    assert accepted['full_protocol_accepted'] and accepted['capture_sha256']==sha(REPO/CAPTURE)
    assert cap['files']['bundle']['data']['generator_input_ready']
    config=dict(version=VERSION,run_id=RUN,scope_counts=COUNTS,matrix=matrix(),profile=PROFILE,
        requests=read(REPO/'configs/wc_policy_interval_assets_full1624_r1_20261020.json')['requests'],
        forecast_complete_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'],
        accepted_original_files={'runner.json':cap['runner_sha256'],
            'generator-input-bundle.json':cap['files']['bundle']['sha256'],
            'post-results.json':cap['files']['post']['sha256']},
        accepted_capture_sha256=sha(REPO/CAPTURE),independent_acceptance_sha256=sha(REPO/ACCEPTED),
        full_GPU_lifecycle_accepted=False)
    value=dict(status='PRICE_COMPLETE_NEW_SOURCE_PREPARED_CPU_ONLY',stage=STAGE,base=BASE,project=ROOT,
        base_registration_sha256=cap['registration_sha256'],config=config,quote=quote,
        overlay_sha256={n:sha(REPO/n) for n in NEW_FILES},GPU_submissions=0,
        full_GPU_lifecycle_accepted=False,production_CPU_accepted=False)
    write(output,value);return value


def deploy_cpu(a):
    packet=read(a.package)
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        assert prepare(Path(t)/'check.json')==packet,'Source/config changed after prepare'
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    files={}
    for n,h in packet['overlay_sha256'].items():
        raw=subprocess.check_output(['git','show',revision+':'+n],cwd=REPO)
        import hashlib
        assert hashlib.sha256(raw).hexdigest()==h,'Commit all new production sources first'
        files[n]=base64.b64encode(raw).decode()
    result=ssh(DEPLOY,dict(packet=packet,files=files,revision=revision))
    write(a.output,result);return result


DEPLOY=r'''
import base64,hashlib,json,os,pathlib,shutil,subprocess,sys,time
p=json.load(sys.stdin);v=p['packet'];root=pathlib.Path(v['project']);stage=pathlib.Path(v['stage']);base=pathlib.Path(v['base'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert stage.parent==base.parent==root/'.sync'
if stage.exists():
 print(json.dumps(dict(status='EXISTING_PRICE_STAGE_RECOVER_ONLY',stage=str(stage),
  launch=json.loads((stage/'price-CPU-launch.json').read_text()) if (stage/'price-CPU-launch.json').exists() else None)));raise SystemExit(0)
assert sha(base/'registration.json')==v['base_registration_sha256']
reg=json.loads((base/'registration.json').read_text());pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
assert not [k for k,j in pool['jobs'].items() if j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False]
assert shutil.disk_usage(root).free>=30*2**30
mem=int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
assert mem>=18*2**30
for n,h in reg['payload_sha256'].items():assert not (base/n).is_symlink() and sha(base/n)==h
stage.mkdir(mode=0o700)
for n in reg['payload_sha256']:
 dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/n,dst)
for n,encoded in p['files'].items():
 raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==v['overlay_sha256'][n]
 dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
for n,obj in [('price-refresh-config.json',v['config']),('price-whole-quote.json',v['quote'])]:
 (stage/n).write_text(json.dumps(obj,indent=2)+chr(10))
names=set(reg['payload_sha256'])|set(p['files'])|{'price-refresh-config.json','price-whole-quote.json'}
new=dict(namespace=v['config']['version'],source_revision=p['revision'],stage=str(stage),read_only_base=str(base),
 read_only_base_registration_sha256=v['base_registration_sha256'],payload_sha256={n:sha(stage/n) for n in sorted(names)},
 runtime_source_sha256=reg['runtime_source_sha256'])
(stage/'registration.json').write_text(json.dumps(new,indent=2)+chr(10))
bank=root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022';sys.path.insert(0,str(bank))
from four_card_bank24_execution_tools_r1 import process_environment,verify_nltk_resources
verify_nltk_resources(root)
sys.path.insert(0,str(stage/'scripts'))
from four_card_policy_assets_port_r1 import container_command
command=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),process_environment(root,stage/'CPU-caches'),os.getuid(),os.getgid())
old=str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py');assert command.count(old)==1
command[command.index(old)]=str(stage/'scripts/wc_policy_price_refresh_worker_r1.py')
with (stage/'price-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
from four_card_bank24_container_transport_r1 import identity
now=time.time();launch=dict(status='PRICE_NEW_FULL_CPU_RUNNING',stage=str(stage),project=str(root),source_revision=p['revision'],
 registration_sha256=sha(stage/'registration.json'),identity=identity(child.pid),container=stage.name+'-cpu',
 started_unix=now,halfway_not_before_unix=now+600,final_not_before_unix=now+1800,
 GPU_submissions=0,ledger_written=False,full_GPU_lifecycle_accepted=False)
(stage/'price-CPU-launch.json').write_text(json.dumps(launch,indent=2)+chr(10));print(json.dumps(launch))
'''


def capture(a):
    L=read(a.launch_ref)
    result=ssh(r'''
import json,pathlib,subprocess,sys,time
p=json.load(sys.stdin);L=p['launch'];stage=pathlib.Path(L['stage'])
sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
from wcomr.policy_price_refresh_production_r1 import read,sha,CPU_PROOF,CPU_BUNDLE,CONFIG
from wcomr.gpu_budget_pool_v2 import process_identity
assert sha(stage/'registration.json')==L['registration_sha256']
q=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=20);assert q.returncode==0
c=json.loads(q.stdout)[0];assert c['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
v=dict(status='PRICE_ORIGINAL_CPU_CAPTURE',launch=L,observed_unix=time.time(),process=process_identity(L['identity']['pid']),
 container=dict(state=c['State'],image=c['Image'],readonly_root=c['HostConfig']['ReadonlyRootfs'],pid_mode=c['HostConfig']['PidMode'],
 device_requests=c['HostConfig'].get('DeviceRequests') or [],devices=c['HostConfig'].get('Devices') or []),files={},GPU_submissions=0)
reg=read(stage/'registration.json');v['registration']=reg
v['payload_actual_sha256']={n:sha(stage/n) for n in reg['payload_sha256']}
v['runtime_actual_sha256']={n:sha(pathlib.Path(L['project'])/'runtime'/n) for n in reg['runtime_source_sha256']}
for key,n in [('production',CPU_PROOF),('numerical','price-numerical-CPU.json'),('bundle',CPU_BUNDLE),('config',CONFIG)]:
 path=stage/n;v['files'][key]=dict(exists=path.exists())
 if path.exists():v['files'][key].update(data=read(path),sha256=sha(path))
log=stage/'price-CPU.log'
with log.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-16384));tail=f.read().decode(errors='replace')
v['log_tail']=tail
print(json.dumps(v))
''',dict(launch=L))
    write(a.output,result);return {k:result[k] for k in ('status','observed_unix','container')}


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    q=s.add_parser('prepare');q.add_argument('--output',type=Path,required=True)
    q=s.add_parser('deploy-cpu');q.add_argument('--package',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    q=s.add_parser('capture');q.add_argument('--launch-ref',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    result=prepare(a.output) if a.command=='prepare' else deploy_cpu(a) if a.command=='deploy-cpu' else capture(a)
    print(json.dumps({k:v for k,v in result.items() if k not in ('overlay_sha256','config','quote')},ensure_ascii=False))

if __name__=='__main__':main()
