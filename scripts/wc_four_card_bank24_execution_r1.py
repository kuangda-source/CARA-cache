#!/usr/bin/env python3
"""Actual four-card BANK24 GPU launch/recovery and once-only capture/accept.

No training, scope reduction, ledger initialization or alternate host route.
The external authoritative handoff is a required input, never made here.
"""
import argparse
import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

from four_card_bank24_execution_tools_r1 import ROOT,TARGET_STAGE,PRODUCTION_SCRIPTS,read,sha,require
from four_card_bank24_gpu_port_r1 import FULL_CPU_STATUS,accept_capture
from four_card_bank24_execution_adapter_r1 import LIFECYCLE_SOURCE
from wc_four_card_resource_cpu_r4 import ssh,write


REMOTE_LAUNCH=r'''
import base64,hashlib,json,pathlib,shutil,sys
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');stage=root/'.sync/wc-bank24-fourcard-full-execution-r1-20261022'
if stage.exists():
 for name in ['scout-GPU-launch.json','scout-GPU-dispatch-fence.json']:
  if (stage/name).is_file():
   print(json.dumps(dict(status='ORIGINAL_STAGE_RESTORE_ONLY',original=json.loads((stage/name).read_text()),no_GPU_relaunch_authority=True)));sys.exit(0)
 ready=stage/'stage-preparation-complete.json'
 if not ready.is_file():raise ValueError('Existing production stage preparation unknown; restore without replacement')
 sys.path.insert(0,str(stage))
 from four_card_bank24_execution_tools_r1 import dispatch,sha,verify_registration
 reg=verify_registration(stage)
 assert reg['source_revision']==p['CPU_accepted']['source_revision'] and sha(stage/'registration.json')==p['CPU_accepted']['registration_sha256']
 assert all(sha(stage/name)==hashlib.sha256(base64.b64decode(encoded)).hexdigest() for name,encoded in p['files'].items())
 print(json.dumps(dispatch(root,stage,p['auth'])));sys.exit(0)
job=pathlib.Path(p['CPU_launch']['job']);assert job.parent.resolve()==(root/'bootstrap').resolve()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
accepted=p['CPU_accepted'];assert accepted['full_new_host_scope_production_CPU_accepted'] is True and all(accepted['checks'].values())
assert accepted['source_revision']==p['CPU_launch']['source_revision'] and sha(job/'result.json')==accepted['proof_sha256']
result=json.loads((job/'result.json').read_text());template=job/'TEST_ONLY/project/.sync/wc-bank24-fourcard-full-execution-r1-20261022'
assert sha(template/'registration.json')==accepted['registration_sha256']==result['target_registration_sha256']
assert result['target_stage']==str(stage) and result['status']=='BANK24_FULL_EXECUTION_TOOLS_CPU_PASS_NOT_NEURAL_OR_GPU'
sys.path.insert(0,str(template))
from four_card_bank24_execution_tools_r1 import validate_handoff,dispatch,verify_registration
verify_registration(template)
handoff=json.loads(base64.b64decode(p['files']['unique-v2-handoff.json']))
# No target write, reservation or process before real complete ledger handoff.
validate_handoff(root,handoff)
assert shutil.disk_usage(root).free>=128*(1<<30)
reg=json.loads((template/'registration.json').read_text());stage.mkdir(mode=0o700)
for name,expected in reg['payload_sha256'].items():
 src=template/name;assert not src.is_symlink() and sha(src)==expected
 dst=stage/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
shutil.copyfile(template/'registration.json',stage/'registration.json')
shutil.copyfile(job/'result.json',stage/'scout-lifecycle-CPU-proof.json')
for name,encoded in p['files'].items():
 assert pathlib.Path(name).name==name
 with (stage/name).open('xb') as f:f.write(base64.b64decode(encoded))
assert sha(stage/'scout-lifecycle-CPU-independent-acceptance.json')==p['auth']['independent_CPU_acceptance_sha256']
with (stage/'stage-preparation-complete.json').open('x') as f:json.dump(dict(source_revision=accepted['source_revision'],registration_sha256=sha(stage/'registration.json'),GPU_Popen_started=False),f)
print(json.dumps(dispatch(root,stage,p['auth'])))
'''


def launch_gpu(a):
    require(not a.output.exists(),'Never overwrite a dispatch receipt')
    L=read(a.CPU_launch_ref);cap=read(a.CPU_capture);accepted=read(a.CPU_acceptance)
    require(accepted['status']==FULL_CPU_STATUS and accepted['full_new_host_scope_production_CPU_accepted'] is True
        and all(accepted['checks'].values()) and accepted['capture_sha256']==sha(a.CPU_capture)
        and accepted['launch_sha256']==sha(a.CPU_launch_ref) and cap['launch']==L,'Actual new-host complete CPU three-piece proof required')
    require(accepted['source_revision']==L['source_revision'] and accepted['unique_v2_handoff_accepted'] is False,'Do not invent a budget handoff from CPU acceptance')
    r=cap['result'];quote=r['production_template']['planning_quote']
    for name in PRODUCTION_SCRIPTS:
        require(Path('scripts',name).read_bytes()==subprocess.check_output(['git','show',L['source_revision']+':scripts/'+name]),'Use the exact CPU-accepted production tools source')
    auth=dict(direct_user_authorization=True,user_reply_quote='Existing direct authorization: complete single cards strictly below12 GPUh execute when prerequisites pass',
        autonomy_exclusive_upper_GPUh=12,source_revision=L['source_revision'],registration_sha256=accepted['registration_sha256'],
        scope_counts=L['scope_counts'],config_sha256=cap['target_registration']['payload_sha256']['inputs/configs/wc_scout_bank24_production_entry_r1_20261018.json'],
        production_CPU_sha256=accepted['proof_sha256'],independent_CPU_acceptance_sha256=sha(a.CPU_acceptance),
        unique_handoff_sha256=sha(a.unique_handoff),planning_quote_sha256=r['production_template']['planning_quote_sha256'],
        forecast_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'],launch_id=str(uuid.uuid4()),gpu_uuid=a.gpu_uuid,
        upstream_capture_sha256=sha(a.upstream_capture),upstream_acceptance_sha256=sha(a.upstream_acceptance),frozen_gate_sha256=sha(a.frozen_gate))
    files={'scout-lifecycle-CPU-independent-acceptance.json':a.CPU_acceptance,'unique-v2-handoff.json':a.unique_handoff,
        'scout-upstream-capture.json.gz':a.upstream_capture,'scout-upstream-acceptance.json':a.upstream_acceptance,'scout-frozen-CAL-gate.json':a.frozen_gate}
    value=ssh(REMOTE_LAUNCH,dict(CPU_launch=L,CPU_accepted=accepted,auth=auth,
        files={n:base64.b64encode(Path(p).read_bytes()).decode() for n,p in files.items()}),timeout=180)
    write(a.output,dict(dispatch=value,authorization=auth,no_retry_after_unknown=True));return dict(output=str(a.output),status=value.get('status'))


def recover(a):
    require(not a.output.exists(),'Read existing recovery receipt offline')
    code="""import json,pathlib
stage=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/wc-bank24-fourcard-full-execution-r1-20261022')
result=dict(status='ORIGINAL_FOUR_CARD_STAGE_READONLY_RECOVERY',stage_exists=stage.exists(),GPU_submissions=0,ledger_written=False)
for name in ['registration.json','scout-GPU-dispatch-fence.json','scout-GPU-launch.json','scout-admission-failure.json','post-CPU-exit.json']:
 p=stage/name
 if p.is_file():result[name]=json.loads(p.read_text())
print(json.dumps(result))
"""
    value=ssh(code,timeout=180);write(a.output,value);return dict(output=str(a.output),status=value['status'])


def capture(a):
    require(not a.output.exists(),'Once-only original observation already exists; read offline')
    raw=read(a.launch_ref);L=raw.get('dispatch',raw)
    require(L.get('status')=='SCOUT_COMPLETE_CARD_DISPATCHED_ADMISSION_PENDING','A real original whole-card handle is required')
    key={'halfway':'halfway_check_not_before_unix','terminal':'next_check_not_before_unix'}.get(a.mode)
    if key:require(time.time()>=L[key],'Before original check not-before; no SSH')
    code='L='+repr(L)+'\nMODE='+repr(a.mode)+'\nOBS='+repr('capture-'+uuid.uuid4().hex)+'\n'+r'''
import json,sys
from pathlib import Path
stage=Path(L['stage']);sys.path.insert(0,str(stage))
from four_card_bank24_execution_tools_r1 import collect_once
value=collect_once(Path(L['project']),stage,L,MODE,stage/OBS)
print(json.dumps(value,allow_nan=False))
'''
    value=ssh(code,timeout=180);write(a.output,value);return dict(output=str(a.output),status=value.get('status'),mode=a.mode)


def accept_gpu(a):
    os.environ['WC_SCOUT_KIND']='BANK24'
    require(not a.output.exists(),'Independent original acceptance already exists')
    raw=read(a.launch_ref);L=raw.get('dispatch',raw);cap=read(a.capture)
    require(not cap.get('CPU_FIXTURE_ONLY_NOT_SCIENTIFIC_CAPTURE') and not L.get('CPU_FIXTURE_ONLY_NOT_GPU'),'CPU fixtures cannot become a scientific GPU acceptance')
    binding=cap.get('CPU_collector_binding') or {};peer=binding.get('host_verified_Docker_peer') or {}
    require(binding.get('host_verified_CPU_container_exit') is True and peer.get('socket_peer_PID_matches_actual_Docker_PID') is True
        and peer.get('container_actual_readonly_root') is True and peer.get('container_devices')==[] and peer.get('container_device_requests')==[],
        'Actual host-bound, GPU-hidden CPU collector proof required')
    require(cap.get('GPU_telemetry_calls')==1 and not any(cap['original_live_handles'].values()),'Once-only telemetry and all original exits required')
    for name in PRODUCTION_SCRIPTS:require(sha(Path('scripts')/name)==cap['registration']['payload_sha256'][name],'Use exact published CPU-accepted tools for offline audit')
    # Only immutable source is materialized. No video/model is copied to Mac.
    with tempfile.TemporaryDirectory(prefix='wc-bank24-offline-source-') as tmp:
        directory=Path(tmp);blob=subprocess.check_output(['git','archive',LIFECYCLE_SOURCE,'src','scripts/run_wc_drop1_full18_r1.py','scripts/postprocess_wc_scout_gpu_r1.py','src/wcomr/gpu_budget_pool_v2.py'])
        with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
            require(all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and (m.isfile() or m.isdir()) for m in archive.getmembers()),'Unsafe immutable source archive')
            archive.extractall(directory)
        try:value=accept_capture(cap,L,directory)
        except (ValueError,KeyError,AssertionError) as error:
            value=dict(status='BANK24_INDEPENDENT_SCIENTIFIC_AUDIT_NOT_ACCEPTED_ALL24_RETAINED',full_protocol_accepted=False,
                registered_paths=24,formal_denominator=18,error_type=type(error).__name__,error=str(error),
                all_paths=[dict(r,status='AUDIT_NOT_ACCEPTED_OR_NOT_REACHED_RETAINED') for r in L['matrix']])
    value.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture),launch_ref=str(a.launch_ref),GPU_submissions=0,ledger_written=False)
    write(a.output,value);return dict(output=str(a.output),status=value['status'],full_protocol_accepted=value.get('full_protocol_accepted'))


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('launch-gpu')
    for name in ['CPU-launch-ref','CPU-capture','CPU-acceptance','unique-handoff','upstream-capture','upstream-acceptance','frozen-gate','output']:q.add_argument('--'+name,required=True,type=Path)
    q.add_argument('--gpu-uuid',required=True)
    q=sub.add_parser('recover');q.add_argument('--output',required=True,type=Path)
    q=sub.add_parser('capture');q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--mode',choices=['admission','halfway','terminal'],required=True);q.add_argument('--output',required=True,type=Path)
    q=sub.add_parser('accept');q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--capture',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.command=='launch-gpu':v=launch_gpu(a)
    elif a.command=='recover':v=recover(a)
    elif a.command=='capture':v=capture(a)
    else:v=accept_gpu(a)
    print(json.dumps(v))


if __name__=='__main__':main()
