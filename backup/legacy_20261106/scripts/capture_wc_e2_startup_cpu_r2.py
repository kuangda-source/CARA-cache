#!/usr/bin/env python3
"""Capture original R2 CPU handles; independently check old and new bytes."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    launch=json.loads((root/'reports/wc_e2_startup_cpu_r2_launch_20261011.json').read_text())
    prefix=root/'reports/wc_e2_startup_cpu_r2_terminal_20261011_';target=Path(str(prefix)+'capture.json');assert not target.exists()
    code='L='+repr(launch)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,sys,time
stage=pathlib.Path(L['stage']);root=stage.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'startup-CPU-receipt.json').read_text())
w=json.loads((stage/'execution-CPU-receipt.json').read_text()) if (stage/'execution-CPU-receipt.json').exists() else {}
pids=[r['pid'],r.get('child_pid'),r.get('meta_child_pid'),w.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_E2_STARTUP_CPU_R2_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
c=json.loads((stage/'e2-config.json').read_text());p=json.loads((stage/'execution-protocol.json').read_text())
reg=json.loads((stage/'registration.json').read_text())
assert sha(stage/'registration.json')==L['registration_sha256']==r['registration_sha256']
assert sha(stage/'e2-config.json')==L['config_sha256']==reg['method_config_sha256']
assert sha(stage/'execution-protocol.json')==L['execution_protocol_sha256']==reg['execution_protocol_sha256']==r['execution_protocol_sha256']
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']==r['method_payload_after_sha256']
assert {n:sha(stage/n) for n in p['execution_payload_sha256']}==p['execution_payload_sha256']==reg['execution_payload_sha256']==r['execution_payload_after_sha256']
assert {n:sha(root/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
assert not c['GPU_execution_selected'] and not r['GPU_submissions'] and not r['ledger_written']
assert r['budget_before_sha256']==r['budget_after_sha256']
if r['exit_code']==0:
 assert r['status']=='E2_STARTUP_WRAPPER_R2_CPU_PASS_NOT_GPU' and not r['CUDA_initialized']
 assert w['pid']==r['child_pid'] and w['exit_code']==w['last_child_exit_code']==0
 assert r['wrapper_child_exit_code']==r['meta_child_exit_code']==0
 assert sha(stage/'execution-CPU-receipt.json')==r['original_execution_CPU_receipt_sha256']
 assert sha(stage/'execution-CPU-result.json')==r['original_execution_CPU_result_sha256']==w['result_sha256']
 assert w['budget_before_sha256']==w['budget_after_sha256']==r['budget_before_sha256']
 assert w['method_payload_after_sha256']==c['payload_sha256'] and w['execution_payload_after_sha256']==p['execution_payload_sha256']
 expected=[{'asset':n,'control':action} for n in reg['required_startup_assets'] for action in ('missing','changed')]
 assert r['required_startup_asset_refusals']==expected
 meta=r['native_mode_meta_CPU_result'];assert meta['parameter_count']==2059174912
 assert meta['mode']['before']['module_count']==meta['mode']['before']['training_modules']==1173
 assert meta['mode']['after']['training_modules']==0 and not meta['cuda_initialized'] and not meta['weights_loaded'] and not meta['forward_executed']
 assert meta['contract_sha256']==reg['required_startup_assets']['manifests/wc_h0_eval_mode_contract_20261003.json']
 assert sum(json.loads(line).get('status')=='ACTUAL_NATIVE_META_DEFAULT_MODE_AND_SHARED_EVAL_STARTUP_CPU_PASS'
  for line in (stage/'native-mode-meta-CPU.log').read_text().splitlines() if line.startswith('{'))==1
 result=json.loads((stage/'execution-CPU-result.json').read_text());scalar=json.loads((stage/'scalar-CPU-result.json').read_text())
 assert sha(stage/'scalar-CPU-result.json')==result['scalar_result_sha256']
 assert scalar['full_original_positions']==76 and scalar['scalar_pair_positions']==68 and scalar['scalar_frame_distances']==6324
 assert scalar['admission_refusals']==17 and scalar['scalar_refusals']==8 and scalar['actual_memory_boundaries']==152
 assert scalar['primary_prompt_units']==4 and scalar['primary_seed_units']==8 and scalar['bootstrap_resamples_per_candidate']==256
 actual=result['original_guarded_entry_CPU_result']
 assert actual['status']=='E2_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
 assert actual['actual_ten_requests_parsed'] and actual['actual_guardrail_resource_and_Native_origin_checked']
 assert actual['five_guardrail_less_methods_refused'] and len(actual['contract_mutation_refusals'])==13
 assert actual['actual_real_prior_fingerprint']==c['RA_calibration_fingerprint'] and actual['actual_threshold']['threshold']==c['RA_threshold']
 assert not actual['CUDA_initialized'] and not actual['GPU_submissions']
 binding=hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in
  {'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 assert binding==r['config_binding_sha256']==actual['config_binding_sha256']==reg['method_config_binding_sha256']
 sys.path.insert(0,str(stage/'src'));from wcomr.lpips_resource_identity import audit
 assert audit(root/'.sync/wc-rv0-lpips-resource-v2',p['execution_payload_sha256']['src/wcomr/rv0_lpips.py'])==result['actual_offline_metric_resource_identity']
names=['startup-CPU-receipt.json','registration.json','launch.json','e2-config.json','execution-protocol.json','driver.log']
names += [n for n in ('startup-wrapper-CPU.log','execution-CPU-receipt.json','execution-CPU-result.json','execution-CPU.log',
 'scalar-CPU-result.json','native-mode-meta-CPU.log') if (stage/n).exists()]
native={}
for n in names:
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,compresslevel=6,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'packed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
capture={'status':'E2_ORIGINAL_STARTUP_R2_CPU_TERMINAL_NOT_GPU','source_revision':L['source_revision'],
 'original_PIDs_absent':[pid for pid in pids if pid],'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'method_payload_files':len(c['payload_sha256']),'execution_payload_files':len(p['execution_payload_sha256']),
 'config_binding_sha256':r['config_binding_sha256'],'execution_protocol_sha256':r['execution_protocol_sha256'],
 'budget_sha256':r['budget_after_sha256'],'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
print(json.dumps({'capture':capture,'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2500:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    proof=value['capture'];proof['files']={};objects={}
    # Verify all small bytes before saving any; transport failures cannot leave
    # half a new capture that is mistaken for accepted CPU evidence.
    decoded={}
    for n,v in value['native'].items():
        packed=base64.b64decode(v['base64'],validate=True);raw=gzip.decompress(packed)
        assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256']
        assert hashlib.sha256(packed).hexdigest()==v['packed_sha256'];decoded[n]=packed
        if n.endswith('.json'):objects[n]=json.loads(raw)
    assert objects['launch.json']==launch
    reg=objects['registration.json'];c=objects['e2-config.json'];p=objects['execution-protocol.json']
    assert reg==json.loads((root/'manifests/wc_e2_startup_cpu_r2_preregistration_20261011.json').read_text())
    assert c==json.loads((root/reg['method_config_ref']).read_text())
    assert p==json.loads((root/reg['generated_protocol_cache']/'execution-protocol.json').read_text())
    for revision,payload in ((launch['source_revision'],reg['new_payload_sha256']),
                             (reg['original_execution_source_revision'],reg['original_execution_payload_sha256'])):
        for n,h in payload.items():
            assert hashlib.sha256(subprocess.check_output(['git','show',revision+':'+n],cwd=root)).hexdigest()==h,n
    if proof['exit_code']==0:
        assert objects['scalar-CPU-result.json']==json.loads((root/'reports/wc_e2_full76_execution_reporting_cpu_r2_20261011.json').read_text())
    for n,packed in decoded.items():
        path=Path(str(prefix)+n+'.native.gz');assert not path.exists();path.write_bytes(packed)
        proof['files'][n]={k:v for k,v in value['native'][n].items() if k!='base64'}
        proof['files'][n]['local_path']=str(path.relative_to(root))
    proof['original_method_source_startup_assets_and_wrapper_independently_verified']=True
    target.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
