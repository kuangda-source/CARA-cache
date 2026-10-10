#!/usr/bin/env python3
"""Capture only original CPU handles and independently recheck source bytes."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    launch=json.loads((root/'reports/wc_e2_execution_cpu_r1_launch_20261011.json').read_text())
    prefix=root/'reports/wc_e2_execution_cpu_r1_terminal_20261011_'
    target=Path(str(prefix)+'capture.json');assert not target.exists()
    code='L='+repr(launch)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);project=stage.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'execution-CPU-receipt.json').read_text());pids=[r['pid'],r['child_pid']]
live=[p for p in pids if pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_EXECUTION_CPU_STILL_RUNNING','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
c=json.loads((stage/'e2-config.json').read_text());p=json.loads((stage/'execution-protocol.json').read_text())
reg=json.loads((stage/'registration.json').read_text())
assert sha(stage/'registration.json')==L['registration_sha256']
assert sha(stage/'e2-config.json')==r['config_sha256']==L['config_sha256']==reg['method_config_sha256']
assert sha(stage/'execution-protocol.json')==r['execution_protocol_sha256']==L['execution_protocol_sha256']==reg['execution_protocol_sha256']
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']==r['method_payload_after_sha256']
assert {n:sha(stage/n) for n in p['execution_payload_sha256']}==p['execution_payload_sha256']==r['execution_payload_after_sha256']==reg['execution_payload_sha256']
assert {n:sha(project/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
assert r['budget_before_sha256']==r['budget_after_sha256']==sha(project/'reports/budget.json')
assert not c['GPU_execution_selected'] and r['GPU_submissions']==0 and not r['ledger_written'] and not r['CUDA_initialized']
if r['exit_code']==0:
 assert r['status']=='E2_EXECUTION_ACTUAL_CPU_PASS_NOT_GPU' and r['last_child_exit_code']==0
 result=json.loads((stage/'execution-CPU-result.json').read_text());scalar=json.loads((stage/'scalar-CPU-result.json').read_text())
 assert sha(stage/'execution-CPU-result.json')==r['result_sha256'] and sha(stage/'scalar-CPU-result.json')==result['scalar_result_sha256']
 assert scalar['status']=='E2_COMPLETE76_EXECUTION_REPORTING_SCALAR_CPU_PASS_NOT_GPU_OR_METRIC'
 assert scalar['full_original_positions']==76 and scalar['scalar_pair_positions']==68 and scalar['scalar_frame_distances']==6324
 assert scalar['primary_prompt_units']==4 and scalar['primary_seed_units']==8 and scalar['bootstrap_resamples_per_candidate']==256
 assert scalar['admission_refusals']==17 and scalar['scalar_refusals']==8 and scalar['actual_memory_boundaries']==152
 assert not scalar['Torch_imported'] and scalar['CAL_bridges_and_distances_are_synthetic']
 assert result['status']=='E2_ACTUAL_EXECUTION_WRAPPER_CPU_PASS_NOT_GPU_OR_LPIPS_SCORE'
 actual=result['original_guarded_entry_CPU_result']
 assert actual['status']=='E2_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
 assert actual['payload_sha256']==c['payload_sha256'] and actual['scope_counts']==c['scope_counts']
 assert actual['actual_ten_requests_parsed'] and actual['actual_guardrail_resource_and_Native_origin_checked']
 assert actual['five_guardrail_less_methods_refused'] and len(actual['contract_mutation_refusals'])==13
 assert actual['actual_real_prior_fingerprint']==c['RA_calibration_fingerprint'] and actual['actual_threshold']['threshold']==c['RA_threshold']
 assert not actual['CUDA_initialized'] and actual['GPU_submissions']==0
 binding=hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in
  {'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 assert binding==r['config_binding_sha256']==actual['config_binding_sha256']==p['method_config_binding_sha256']
 import sys;sys.path.insert(0,str(stage/'src'))
 from wcomr.lpips_resource_identity import audit
 assert audit(project/'.sync/wc-rv0-lpips-resource-v2',p['execution_payload_sha256']['src/wcomr/rv0_lpips.py'])==result['actual_offline_metric_resource_identity']
native={}
names=['execution-CPU-receipt.json','registration.json','launch.json','e2-config.json','execution-protocol.json','driver.log','execution-CPU.log']
names += [n for n in ('execution-CPU-result.json','scalar-CPU-result.json') if (stage/n).exists()]
for n in names:
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,compresslevel=9,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'packed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
capture={'status':'E2_ORIGINAL_EXECUTION_CPU_TERMINAL_NOT_GPU_OR_LPIPS_SCORE','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'method_payload_files':len(c['payload_sha256']),'execution_payload_files':len(p['execution_payload_sha256']),
 'config_binding_sha256':r['config_binding_sha256'],'execution_protocol_sha256':r['execution_protocol_sha256'],
 'budget_sha256':r['budget_after_sha256'],'GPU_execution_selected':False,'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
print(json.dumps({'capture':capture,'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2500:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    proof=value['capture'];proof['files']={};objects={}
    for n,item in value['native'].items():
        packed=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(packed).hexdigest()==item['packed_sha256']
        path=Path(str(prefix)+n+'.native.gz');assert not path.exists();path.write_bytes(packed)
        proof['files'][n]={k:v for k,v in item.items() if k!='base64'}
        proof['files'][n]['local_path']=str(path.relative_to(root))
        if n.endswith('.json'):objects[n]=json.loads(raw)
    assert objects['launch.json']==launch
    reg=objects['registration.json'];c=objects['e2-config.json'];protocol=objects['execution-protocol.json']
    assert reg==json.loads((root/'manifests/wc_e2_execution_cpu_r1_preregistration_20261011.json').read_text())
    assert c==json.loads((root/reg['method_config_ref']).read_text())
    assert protocol==json.loads((root/reg['generated_protocol_cache']/'execution-protocol.json').read_text())
    for n,h in reg['execution_payload_sha256'].items():
        original=subprocess.check_output(['git','show',launch['source_revision']+':'+n],cwd=root)
        assert hashlib.sha256(original).hexdigest()==h,n
    if proof['exit_code']==0:
        assert objects['scalar-CPU-result.json']==json.loads((root/'reports/wc_e2_full76_execution_reporting_cpu_r2_20261011.json').read_text())
    proof['original_source_and_execution_protocol_independently_verified']=True
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
