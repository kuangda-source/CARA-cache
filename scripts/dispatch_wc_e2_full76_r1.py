#!/usr/bin/env python3
"""Prepare selected CPU and one whole76 dispatch only after exact approval."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def main():
    root=Path(__file__).resolve().parents[1]
    authority_ref='manifests/wc_e2_full76_direct_authorization_20261011.json'
    authority=root/authority_ref
    if not authority.exists():
        print(json.dumps({'status':'WAIT_EXACT_COMPLETE76_ABOVE8_APPROVAL_NO_DISPATCH',
            'GPU_submissions':0,'SSH_called':False,'ledger_written':False,'new_selected_directory':False}));return 2
    c=json.loads((root/'configs/wc_e2_production_r1_20261011.json').read_text())
    approved=json.loads(authority.read_text())
    from sys import path;path.insert(0,str(root/'src'))
    from wcomr.e2_execution_r1 import binding,sha,UUID
    if (not approved['direct_user_authorization'] or approved['card']!=c['card'] or approved['run_id']!=c['run_id']
            or approved['scope_counts']!=c['scope_counts'] or approved['config_binding_sha256']!=binding(c)
            or approved['forecast_complete_GPUh']!=c['forecast_complete_GPUh']):
        raise ValueError('Direct exact full76 approval does not cover current frozen card')
    proof=json.loads((root/'reports/wc_e2_execution_cpu_r1_terminal_20261011_capture.json').read_text())
    assert proof['exit_code']==0 and proof['original_source_and_execution_protocol_independently_verified']
    reg=json.loads((root/'manifests/wc_e2_execution_cpu_r1_preregistration_20261011.json').read_text())
    original=json.loads((root/'reports/wc_e2_production_cpu_r1_terminal_20261011_capture.json').read_text())
    c.update(GPU_execution_selected=True,gpu_uuid=UUID,
        production_cpu_receipt_sha256=original['files']['receipt.json']['sha256'],
        single_job_exception_authority={'ref':authority_ref,'sha256':sha(authority)})
    assert binding(c)==approved['config_binding_sha256']
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert authority.read_bytes()==subprocess.check_output(['git','show',revision+':'+authority_ref],cwd=root)
    launch=root/'reports/wc_e2_full76_selected_pipeline_launch_20261011.json';assert not launch.exists()
    packet={'stage':'.sync/wc-e2-selected-r1-20261011','original':'.sync/wc-e2-execution-cpu-r1-20261011',
        'original_CPU_receipt_sha256':proof['files']['execution-CPU-receipt.json']['sha256'],
        'method_payload':c['payload_sha256'],'execution_payload':reg['execution_payload_sha256'],
        'selected_config':c,'source_revision':revision,'authority_ref':authority_ref,
        'authority_bytes':authority.read_text(),'execution_protocol_sha256':reg['execution_protocol_sha256']}
    source='P='+repr(packet)+'\n'+r'''import hashlib,json,os,pathlib,shutil,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');old=root/P['original'];stage=root/P['stage']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((old/'execution-CPU-receipt.json').read_text())
assert r['exit_code']==r['last_child_exit_code']==0 and sha(old/'execution-CPU-receipt.json')==P['original_CPU_receipt_sha256']
assert not any(pathlib.Path('/proc/'+str(pid)).exists() for pid in [r['pid'],r['child_pid']])
assert r['method_payload_after_sha256']==P['method_payload'] and r['execution_payload_after_sha256']==P['execution_payload']
assert not stage.exists();stage.mkdir()
for n,h in {**P['method_payload'],**P['execution_payload']}.items():
 assert sha(old/n)==h
 target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old/n,target)
assert sha(old/'execution-protocol.json')==P['execution_protocol_sha256']
shutil.copyfile(old/'execution-protocol.json',stage/'execution-protocol.json')
(stage/'e2-config.json').write_text(json.dumps(P['selected_config'],indent=2)+'\n')
path=stage/P['authority_ref'];path.parent.mkdir(parents=True,exist_ok=True);path.write_text(P['authority_bytes'])
command=['python3',str(stage/'scripts/select_and_launch_wc_e2_full76_r1.py'),'--project',str(root),
 '--stage',str(stage),'--source-revision',P['source_revision']]
with (stage/'selected-driver.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
result={'status':'SELECTED_CPU_PIPELINE_STARTED_GPU_NOT_YET_SUBMITTED','stage':str(stage),
 'selected_driver_pid':child.pid,'source_revision':P['source_revision'],'config_sha256':sha(stage/'e2-config.json'),
 'execution_protocol_sha256':sha(stage/'execution-protocol.json'),'observed_unix':time.time(),
 'GPU_submissions_at_return':0,'ledger_written_by_deployment':False}
(stage/'selected-pipeline-launch.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=source,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2500:])
    value=json.loads(call.stdout);launch.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value));return 0


if __name__=='__main__':raise SystemExit(main())
