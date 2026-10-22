#!/usr/bin/env python3
"""Prepare and operate the independent full1624 Ada card after BANK24 accepts.

prepare is local-only. deploy-cpu consumes an accepted BANK24 terminal and a
complete quote; it refuses while any confirmed project GPU job is in flight.
"""
import argparse
import base64
import gzip
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

from four_card_policy_assets_port_r1 import (ROOT, RUN, STAGE, CONFIG, SCIENCE_SOURCE,
    generated_sources, quote_from_bank24, sha, read, require, digest)
from wc_four_card_resource_cpu_r4 import ssh as base_ssh, write
from wc_four_card_bank24_native_transport_r4 import bridge, RUNTIME_REF

REPO = Path(__file__).resolve().parents[1]
BASE = ROOT+'/.sync/wc-bank24-fourcard-full-execution-r3-20261022'
APPROVAL = 'reports/wc_policy_interval_assets_full1624_specific_whole12_approval_20261020.json'
METADATA = 'manifests/wc_four_card_bank24_execution_metadata_r1_20261022.json'
OLD_QUOTE = 'manifests/wc_policy_interval_assets_full1624_whole_quote_r1_20261020.json'
EXTRA = ['scripts/wc_four_card_policy_assets_r1.py','scripts/four_card_policy_assets_port_r1.py',
         'scripts/four_card_bank24_execution_adapter_r1.py', APPROVAL]
ENTRY = ['scripts/wc_policy_interval_assets_lifecycle_r1.py',
         'scripts/run_wc_policy_interval_assets_r1.py',
         'scripts/check_wc_policy_interval_assets_cpu_r1.py',
         'scripts/postprocess_wc_policy_interval_assets_r1.py']


def ssh(code, data=None):
    return base_ssh(bridge(code, read(REPO/RUNTIME_REF)), data, timeout=180)


def prepare(output):
    sys.path.insert(0, str(REPO/'src'))
    from wcomr.immutable_stage_payload_r1 import configuration_closure, local_python_closure
    files = configuration_closure(REPO, [CONFIG])
    files.update(local_python_closure(REPO, ENTRY+[
        'tests/test_policy_interval_assets_r1.py','tests/check_policy_interval_assets_sampling_cpu_r1.py']))
    for name in EXTRA:
        files[name] = sha(REPO/name)
    generated, replacements = generated_sources(REPO)
    # The scientific implementation and config are bound to the previous tree.
    for name in set(replacements) | {CONFIG}:
        require((REPO/name).read_bytes() == subprocess.check_output(['git','show',SCIENCE_SOURCE+':'+name],cwd=REPO),
                'Scientific/host base differs from reviewed source: '+name)
    metadata = read(REPO/METADATA)
    value = dict(status='FULL1624_FOURCARD_LOCAL_PACKAGE_PREPARED_NOT_PRODUCTION_CPU',
        project=ROOT, stage=ROOT+'/.sync/'+STAGE, execution_run_id=RUN,
        original_scientific_run_id=read(REPO/CONFIG)['run_id'],
        original_config_sha256=sha(REPO/CONFIG), specific_approval_sha256=sha(REPO/APPROVAL),
        overlay_sha256=files, original_inputs_metadata_ref=METADATA,
        original_inputs_metadata_sha256=sha(REPO/METADATA),
        original_payload_count=len(metadata['original_payload_sha256']),
        source_scope=read(REPO/CONFIG)['scope_counts'],
        generated_sha256={n:digest(s.encode()) for n,s in generated.items()},
        reversible_substitutions=replacements,
        CPU_recipe=dict(commands=3,numerical_paths=28,cells_reloaded=4060,
            readout_trials=26040,actual_Cosmos_requests=4,guard_refusal_controls=12,
            cpus=2,memory_GiB=16,halfway_after_seconds=450,terminal_after_seconds=1080),
        source_is_published=False, production_CPU_accepted=False, GPU_dispatch_ready=False,
        GPU_submissions=0, remote_calls=0)
    value=json.loads(json.dumps(value))
    write(output,value)
    return value


def accepted_bank24(launch_ref, capture_ref, accepted_ref):
    # Reuse the entire original four-card acceptor, including finance and raw
    # artifacts, instead of trusting a Boolean copied from another receipt.
    from wc_four_card_bank24_execution_r2 import accept_gpu
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/'accept.json'
        accept_gpu(SimpleNamespace(launch_ref=launch_ref,capture=capture_ref,output=target))
        recomputed=read(target)
    accepted=read(accepted_ref)
    require(accepted == recomputed and accepted.get('full_protocol_accepted') is True,
            'Complete original BANK24 acceptance must independently reproduce')
    return read(capture_ref), accepted


def deploy_cpu(a):
    package=read(a.package)
    with tempfile.TemporaryDirectory() as tmp:
        current=prepare(Path(tmp)/'package.json')
    require(current == package, 'Prepared source or configuration changed')
    cap, accepted=accepted_bank24(a.bank_launch,a.bank_capture,a.bank_acceptance)
    quote=quote_from_bank24(cap,accepted,read(REPO/OLD_QUOTE))
    quote.update(BANK24_capture_sha256=sha(a.bank_capture),BANK24_acceptance_sha256=sha(a.bank_acceptance))
    require(quote['within_approved_limit'], 'Complete new-host forecast exceeds approved12; retain whole scope and reprice/approve')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    files={}
    for name, expected in package['overlay_sha256'].items():
        raw=subprocess.check_output(['git','show',revision+':'+name],cwd=REPO)
        require(digest(raw)==expected, 'Publish exact new payload before CPU deployment: '+name)
        files[name]=base64.b64encode(raw).decode()
    generated,_=generated_sources(REPO)
    packet=dict(package=package,source_revision=revision,files=files,generated=generated,
        base=BASE,metadata=read(REPO/METADATA),quote=quote,
        upstream=dict(launch=read(a.bank_launch)['dispatch'],accepted=accepted))
    value=ssh(DEPLOY,packet)
    write(a.output,value)
    return value


DEPLOY = r'''
import base64,hashlib,json,os,pathlib,shutil,subprocess,sys,time
p=json.load(sys.stdin);root=pathlib.Path(p['package']['project']);stage=pathlib.Path(p['package']['stage']);base=pathlib.Path(p['base'])
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert stage.parent==root/'.sync' and stage.name=='wc-policy-assets-fourcard-full1624-r1-20261022'
if stage.exists():
 print(json.dumps(dict(status='EXISTING_FULL1624_STAGE_RESTORE_ONLY',stage=str(stage),launch=json.loads((stage/'fourcard-cpu-launch.json').read_text()) if (stage/'fourcard-cpu-launch.json').exists() else None)));sys.exit(0)
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
active=[k for k,j in pool['jobs'].items() if j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False]
assert not active,'Do not overlap actual CPU with a confirmed GPU card: '+repr(active)
up=p['upstream']['launch'];assert pool['jobs'][up['run_id']]['status']=='SETTLED'
assert pool['jobs'][up['run_id']]['launch_id']==up['launch_id']
assert shutil.disk_usage(root).free>=p['quote']['minimum_free_disk_bytes']
memory=int(next(s.split()[1] for s in pathlib.Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
assert memory>=18*2**30
sys.path.insert(0,str(base))
from four_card_bank24_execution_tools_r1 import verify_registration,process_environment,verify_nltk_resources
from four_card_bank24_container_transport_r1 import identity
regbase=verify_registration(base);verify_nltk_resources(root)
bindings=dict(p['metadata']['original_payload_sha256'],**p['metadata']['additional_metadata_sha256'])
for n,h in bindings.items():assert sha(base/'inputs'/n)==h
stage.mkdir(mode=0o700)
for n,h in bindings.items():
 dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/'inputs'/n,dst)
for n,encoded in p['files'].items():
 raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==p['package']['overlay_sha256'][n]
 if n in bindings:assert hashlib.sha256(raw).hexdigest()==bindings[n],'Overlay cannot silently alter accepted base'
 dst=stage/n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
for n,code in p['generated'].items():
 assert hashlib.sha256(code.encode()).hexdigest()==p['package']['generated_sha256'][n]
 (stage/n).write_text(code)
(stage/'fourcard-whole-quote.json').write_text(json.dumps(p['quote'],indent=2)+chr(10))
(stage/'fourcard-BANK24-upstream.json').write_text(json.dumps(p['upstream'],indent=2)+chr(10))
names=set(bindings)|set(p['files'])|set(p['generated'])|{'fourcard-whole-quote.json','fourcard-BANK24-upstream.json'}
reg=dict(namespace='FULL1624_FOUR_CARD_PORT_R1',source_revision=p['source_revision'],stage=str(stage),
 payload_sha256={n:sha(stage/n) for n in sorted(names)},runtime_source_sha256=regbase['runtime_source_sha256'],
 original_payload_sha256=bindings,reversible_substitutions=p['package']['reversible_substitutions'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+chr(10))
sys.path.insert(0,str(stage/'scripts'))
from four_card_policy_assets_port_r1 import container_command
env=process_environment(root,stage/'CPU-caches');command=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),env,os.getuid(),os.getgid())
with (stage/'policy-assets-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
now=time.time();L=dict(status='FULL1624_FOURCARD_CPU_SINGLE_DISPATCHED',project=str(root),stage=str(stage),source_revision=p['source_revision'],
 registration_sha256=sha(stage/'registration.json'),identity=identity(child.pid),container=stage.name+'-cpu',
 started_unix=now,halfway_not_before_unix=now+450,final_not_before_unix=now+1080,GPU_submissions=0,ledger_written=False)
(stage/'fourcard-cpu-launch.json').write_text(json.dumps(L,indent=2)+chr(10))
print(json.dumps(L))
'''


def capture(a):
    L=read(a.launch_ref)
    key={'cpu-halfway':'halfway_not_before_unix','cpu-terminal':'final_not_before_unix',
         'gpu-halfway':'halfway_check_not_before_unix','gpu-terminal':'next_check_not_before_unix'}.get(a.mode)
    require(key is None or time.time()>=L[key], 'Before registered check time')
    code=r'''
import json,pathlib,sys,subprocess,gzip
p=json.load(sys.stdin);L=p['launch'];MODE=p['mode'];stage=pathlib.Path(L['stage'])
sys.path[:0]=[str(stage/'scripts'),str(stage/'src')]
import wc_policy_interval_assets_lifecycle_r1 as original
namespace=dict(L=L,MODE=MODE)
code=original.CAPTURE_CODE.replace("sys.stdout.buffer.write(gzip.compress(json.dumps(v,allow_nan=False).encode()))",'')
exec(compile(code,'<original-full1624-capture>','exec'),namespace)
v=namespace['v'];q=subprocess.run(['docker','inspect',L['container']],capture_output=True,text=True,timeout=15)
assert q.returncode==0
c=json.loads(q.stdout)[0];assert c['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
v['container_binding']=dict(state=c['State'],image=c['Image'],readonly_root=c['HostConfig']['ReadonlyRootfs'],pid_mode=c['HostConfig']['PidMode'],
 device_requests=c['HostConfig'].get('DeviceRequests') or [],devices=c['HostConfig'].get('Devices') or [],registration_sha256=L['registration_sha256'])
v['execution_quote']=json.loads((stage/'fourcard-whole-quote.json').read_text())
if MODE.startswith('gpu-'):v['original_live_handles']['container']=c['State']['Running']
print(json.dumps(v,allow_nan=False))
'''
    value=ssh(code,dict(launch=L,mode=a.mode));write(a.output,value);return value


def recover(a):
    """Read the one existing stage after a lost response; never dispatch."""
    code=r'''
import json,pathlib,sys,subprocess
p=json.load(sys.stdin);stage=pathlib.Path(p['stage'])
names=['fourcard-cpu-launch.json','fourcard-gpu-intent.json','fourcard-gpu-launch.json','policy-assets-admission-failure.json']
value=dict(status='FULL1624_READ_ONLY_ORIGINAL_HANDLE_RECOVERY',stage=str(stage),stage_exists=stage.exists(),handles={},containers={},GPU_submissions=0,ledger_written=False)
for name in names:
 if (stage/name).exists():value['handles'][name]=json.loads((stage/name).read_text())
for mode in ('cpu','gpu'):
 name=stage.name+'-'+mode;q=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=15)
 value['containers'][mode]=json.loads(q.stdout)[0]['State'] if q.returncode==0 else dict(status='UNAVAILABLE',stderr=q.stderr)
print(json.dumps(value))
'''
    value=ssh(code,dict(stage=ROOT+'/.sync/'+STAGE));write(a.output,value);return value


def accept(a):
    sys.path.insert(0,str(REPO/'src'))
    from wcomr.policy_interval_assets_lifecycle_r1 import accept_cpu,accept_terminal
    from four_card_policy_assets_port_r1 import IMAGE
    cap=read(a.capture);binding=cap['container_binding']
    require(binding['image']==IMAGE and binding['readonly_root'] and binding['pid_mode']=='host'
            and binding['registration_sha256']==cap['launch']['registration_sha256'], 'Original container identity differs')
    require(not binding['state']['Running'], 'Original container is still running')
    if a.kind=='cpu':
        require(not binding['device_requests'] and not binding['devices'] and binding['state']['ExitCode']==0,
                'Actual GPU-hidden CPU container must exit successfully')
        value=accept_cpu(cap)
        require(value['production_CPU_accepted'], 'Complete original full CPU required')
        transport=cap['files']['proof']['data'].get('host_transport_CPU',{})
        require(all(transport.get(k) is True for k in ['parent_and_namespace_match','original_fd_inode_match',
            'independent_open_refused','GPU_hidden','child_exited','fixture_lock_released'])
            and transport.get('authority_ledger_opened') is False,'Actual same-container FD/parent/lease CPU proof required')
        value.update(GPU_dispatch_ready=False,full_new_host_scope_production_CPU_accepted=True)
    else:
        value=accept_terminal(cap)
        value['full_protocol_accepted']=bool(value.get('full_protocol_accepted') and binding['state']['ExitCode']==0)
    value.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture),
        container_binding_accepted=True,GPU_submissions=0,ledger_written=False)
    write(a.output,value);return value


def launch_gpu(a):
    from types import SimpleNamespace
    cpu=read(a.cpu_capture);L=read(a.cpu_launch);accepted=read(a.cpu_acceptance)
    require(cpu['launch']==L, 'CPU capture belongs to a different launch')
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'accepted.json'
        accept(SimpleNamespace(kind='cpu',capture=a.cpu_capture,output=path))
        require(read(path)==accepted, 'Recomputed full CPU acceptance differs')
    cap, up=accepted_bank24(a.bank_launch,a.bank_capture,a.bank_acceptance)
    quote=quote_from_bank24(cap,up,read(REPO/OLD_QUOTE))
    quote.update(BANK24_capture_sha256=sha(a.bank_capture),BANK24_acceptance_sha256=sha(a.bank_acceptance))
    require(cpu['execution_quote']==quote and quote['within_approved_limit'], 'Whole execution quote changed')
    approval=read(REPO/APPROVAL)
    require(approval['approved'] and approval['config_sha256']==accepted['config_sha256']
            and approval['billed_limit_GPUh']==12, 'Original specific whole12 approval required')
    c=cpu['files']['config']['data']
    require(c['scope_counts']==quote['scope_counts'], 'No split or reduced card')
    auth=dict(kind='SPECIFIC_WHOLE_CARD_APPROVAL',run_id=RUN,whole_card_run=RUN,
        launch_id=str(uuid.uuid4()),gpu_uuid=a.gpu_uuid,entry_stage=L['stage'],
        source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],
        config_sha256=accepted['config_sha256'],production_CPU_sha256=accepted['proof_sha256'],
        independent_CPU_acceptance_sha256=sha(a.cpu_acceptance),scope_counts=c['scope_counts'],
        bound_input_fingerprint=digest(json.dumps(c['requests'],sort_keys=True).encode()),
        forecast_GPUh=quote['forecast_complete_GPUh'],forecast_complete_GPUh=quote['forecast_complete_GPUh'],
        billed_limit_GPUh=12.,cumulative_cap_GPUh=226,budget_origin_used_GPUh=79.99637737158223,
        direct_user_authorization=True,specific_whole_card_approved=True,user_reply_quote=approval['direct_human_quote'],
        execution_quote_sha256=cpu['registration']['payload_sha256']['fourcard-whole-quote.json'],
        upstream_capture_sha256=sha(a.bank_capture),upstream_acceptance_sha256=sha(a.bank_acceptance),
        upstream_full_protocol_accepted=True,new_host_complete_CPU_accepted=True,
        specific_approval_sha256=sha(REPO/APPROVAL))
    value=ssh(LAUNCH_GPU,dict(launch=L,auth=auth,CPU_acceptance_bytes=base64.b64encode(a.cpu_acceptance.read_bytes()).decode(),base=BASE))
    write(a.output,value);return value


LAUNCH_GPU = r'''
import base64,fcntl,hashlib,json,os,pathlib,subprocess,sys,time,shutil
p=json.load(sys.stdin);L=p['launch'];auth=p['auth'];stage=pathlib.Path(L['stage']);root=pathlib.Path(L['project']);base=pathlib.Path(p['base'])
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
sys.path[:0]=[str(stage/'scripts'),str(stage/'src'),str(base)]
from four_card_policy_assets_port_r1 import container_command,validate,RUN
from four_card_bank24_execution_tools_r1 import process_environment,verify_nltk_resources
from four_card_bank24_gpu_port_r1 import validate_handoff
from supervise_wc_four_card_bank24_gpu_r1 import observe
from four_card_bank24_execution_adapter_r1 import device_gate
from four_card_bank24_container_transport_r1 import identity
with (stage/'fourcard-dispatch.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for name in ['fourcard-gpu-launch.json','fourcard-gpu-intent.json']:
  if (stage/name).exists():
   print(json.dumps(dict(status='EXISTING_GPU_HANDLE_RESTORE_ONLY',original=json.loads((stage/name).read_text()))));sys.exit(0)
 assert sha(stage/'registration.json')==L['registration_sha256']
 c,reg,*_=validate(stage,root);quote=json.loads((stage/'fourcard-whole-quote.json').read_text())
 assert quote['within_approved_limit'] and quote['forecast_complete_GPUh']==auth['forecast_GPUh']
 assert sha(stage/'policy-assets-production-CPU-proof.json')==auth['production_CPU_sha256']
 assert sha(stage/'reports/wc_policy_interval_assets_full1624_specific_whole12_approval_20261020.json')==auth['specific_approval_sha256']
 assert json.loads((stage/'policy-assets-production-CPU-bundle.json').read_text())['exit_code']==0
 verify_nltk_resources(root);validate_handoff(root,json.loads((base/'unique-v2-handoff.json').read_text()))
 pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
 active=[k for k,j in pool['jobs'].items() if j['status']=='RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False]
 assert not active and pool['available_gpu_hours']>=12
 gpu=observe(auth['gpu_uuid'])
 if not device_gate(gpu):
  print(json.dumps(dict(status='FULL1624_RESOURCE_BUSY_NO_DISPATCH',GPU_submissions=0,ledger_written=False)));sys.exit(0)
 assert shutil.disk_usage(root).free>=quote['minimum_free_disk_bytes']
 memory=int(next(s.split()[1] for s in pathlib.Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
 assert memory>=max(quote['minimum_MemAvailable_bytes'],50*2**30)
 assert not (root/'outputs'/RUN).exists()
 raw=base64.b64decode(p['CPU_acceptance_bytes']);assert hashlib.sha256(raw).hexdigest()==auth['independent_CPU_acceptance_sha256']
 (stage/'policy-assets-independent-CPU-acceptance.json').write_bytes(raw)
 with (stage/'policy-assets-GPU-authorization.json').open('x') as f:json.dump(auth,f,indent=2)
 env=process_environment(root,stage/'GPU-caches',auth['gpu_uuid'])
 command=container_command(root,stage,'supervise',L['registration_sha256'],env,os.getuid(),os.getgid(),auth['gpu_uuid'])
 now=time.time()
 with (stage/'fourcard-gpu-intent.json').open('x') as f:
  json.dump(dict(launch_id=auth['launch_id'],started_unix=now,source_revision=L['source_revision'],no_replay=True),f);f.flush();os.fsync(f.fileno())
 with (stage/'fourcard-GPU-container.log').open('x') as log:
  child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 name=stage.name+'-gpu';container=None
 for attempt in range(20):
  q=subprocess.run(['docker','inspect',name],capture_output=True,text=True,timeout=10)
  if q.returncode==0:
   candidate=json.loads(q.stdout)[0]
   if candidate['State']['Running'] and candidate['State']['Pid']>0:container=candidate;break
   if candidate['State']['Status']=='exited':break
  time.sleep(.25)
 assert container is not None,'Dispatch outcome unknown or immediate failure: restore existing intent, never replay'
 who=identity(container['State']['Pid']);assert who
 value=dict(status='FULL1624_ADA_SINGLE_DISPATCHED_ADMISSION_PENDING',project=str(root),stage=str(stage),
  run_id=RUN,launch_id=auth['launch_id'],source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],
  config_sha256=auth['config_sha256'],production_CPU_sha256=auth['production_CPU_sha256'],
  gpu_uuid=auth['gpu_uuid'],scope_counts=c['scope_counts'],supervisor_identity=who,supervisor_pid=who['pid'],
  container=name,docker_client_identity=identity(child.pid),started_unix=now,forecast_GPUh=auth['forecast_GPUh'],billed_limit_GPUh=12,
  halfway_check_not_before_unix=now+auth['forecast_GPUh']*1800,next_check_not_before_unix=now+auth['forecast_GPUh']*3600+900)
 with (stage/'fourcard-gpu-launch.json').open('x') as f:json.dump(value,f,indent=2)
 print(json.dumps(value))
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    q=s.add_parser('prepare');q.add_argument('--output',required=True,type=Path)
    q=s.add_parser('recover');q.add_argument('--output',required=True,type=Path)
    q=s.add_parser('deploy-cpu')
    for n in ['package','bank-launch','bank-capture','bank-acceptance','output']:
        q.add_argument('--'+n,required=True,type=Path)
    q=s.add_parser('capture');q.add_argument('--mode',required=True,choices=['cpu-halfway','cpu-terminal','gpu-admission','gpu-halfway','gpu-terminal'])
    q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    q=s.add_parser('accept');q.add_argument('--kind',required=True,choices=['cpu','gpu'])
    q.add_argument('--capture',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    q=s.add_parser('launch-gpu')
    for n in ['cpu-launch','cpu-capture','cpu-acceptance','bank-launch','bank-capture','bank-acceptance','output']:
        q.add_argument('--'+n,required=True,type=Path)
    q.add_argument('--gpu-uuid',required=True)
    a=p.parse_args();require(not a.output.exists(),'Preserve original output; do not replay')
    try:
        result=prepare(a.output) if a.command=='prepare' else globals()[a.command.replace('-','_')](a)
    except Exception as error:
        if a.command in ('deploy-cpu','launch-gpu','capture','recover') and not a.output.exists():
            write(a.output,dict(status='FULL1624_ACTION_FAILED_OR_UNKNOWN_RESTORE_ONLY',command=a.command,
                stage=ROOT+'/.sync/'+STAGE,error_type=type(error).__name__,error=str(error),no_replay=True))
        raise
    print(json.dumps({k:result.get(k) for k in ['status','production_CPU_accepted','full_protocol_accepted','GPU_submissions']}))


if __name__=='__main__':
    main()
