#!/usr/bin/env python3
"""Capture the one original production CPU terminal and verify frozen bytes."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    launch=json.loads((root/'reports/wc_e2_production_cpu_r1_launch_20261011.json').read_text())
    prefix=root/'reports/wc_e2_production_cpu_r1_terminal_20261011_'
    target=Path(str(prefix)+'capture.json');assert not target.exists()
    code='L='+repr(launch)+'\n'+r'''import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);project=stage.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r['child_pid']]
live=[p for p in pids if pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_E2_PRODUCTION_CPU_STILL_RUNNING','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(stage/'registration.json')==L['registration_sha256']
c=json.loads((stage/'e2-config.json').read_text());reg=json.loads((stage/'registration.json').read_text())
assert sha(stage/'e2-config.json')==r['config_sha256']==L['config_sha256']==reg['config_sha256']
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']==r['payload_after_sha256']==reg['payload_sha256']
assert {n:sha(project/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
assert sha(project/'reports/budget.json')==r['budget_before_sha256']==r['budget_after_sha256']
assert r['GPU_submissions']==0 and not r['CUDA_initialized'] and not r['ledger_written']
assert not c['GPU_execution_selected']
if r['exit_code']==0:
 assert r['child_exit_code']==0 and r['status']=='E2_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
 result=json.loads((stage/'CPU-result.json').read_text());assert sha(stage/'CPU-result.json')==r['result_sha256']
 assert result['status']=='E2_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
 assert result['payload_sha256']==c['payload_sha256'] and result['scope_counts']==c['scope_counts']
 assert result['actual_ten_requests_parsed'] and result['actual_guardrail_resource_and_Native_origin_checked']
 assert result['five_guardrail_less_methods_refused'] and len(result['contract_mutation_refusals'])==13
 assert result['actual_real_prior_fingerprint']==c['RA_calibration_fingerprint']
 assert result['actual_threshold']['threshold']==c['RA_threshold']
 assert not result['CUDA_initialized'] and result['GPU_submissions']==0
 binding=hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in
  {'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 assert binding==r['config_binding_sha256']==result['config_binding_sha256']
 inputs=json.loads((stage/c['inputs_ref']).read_text());actual=[json.loads(s) for s in (stage/'e2-requests.jsonl').read_text().splitlines() if s]
 base=json.loads((project/c['base_dependency_stage']/'ra-plus-a-config.json').read_text())
 assert sha(project/c['base_dependency_stage']/'ra-plus-a-config.json')==c['base_dependency_config_sha256']
 names=list(dict.fromkeys(v['CAL_name'] for v in inputs['timing_slots']))
 assert actual==inputs['requests']+[next(v for v in base['preregistration']['requests'] if v['name']==n) for n in names]
 assert len(actual)==10 and len({v['name'] for v in actual})==10
 assert c['scope_counts']=={'scientific_paths':72,'confirmation_paths':40,'timing_paths':32,'parity_paths':4,'complete_actual_GPU_paths':76,'solver_updates':2736,'CFG_calls':5472}
native={}
for n in ['receipt.json','registration.json','launch.json','e2-config.json','e2-requests.jsonl','driver.log','production-CPU.log']+(['CPU-result.json'] if (stage/'CPU-result.json').exists() else []):
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,compresslevel=9,mtime=0)
 native[n]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'packed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
capture={'status':'E2_ORIGINAL_PRODUCTION_CPU_TERMINAL','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'payload_files':len(c['payload_sha256']),'config_binding_sha256':r.get('config_binding_sha256'),
 'budget_sha256':r['budget_after_sha256'],'GPU_execution_selected':False,
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()}
print(json.dumps({'capture':capture,'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-2200:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    proof=value['capture'];proof['files']={};objects={}
    for n,item in value['native'].items():
        packed=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(packed).hexdigest()==item['packed_sha256']
        p=Path(str(prefix)+n+'.native.gz');assert not p.exists();p.write_bytes(packed)
        proof['files'][n]={k:v for k,v in item.items() if k!='base64'}
        proof['files'][n]['local_path']=str(p.relative_to(root))
        if n.endswith('.json'):objects[n]=json.loads(raw)
    assert objects['launch.json']==launch
    reg=objects['registration.json'];c=objects['e2-config.json']
    assert c==json.loads((root/reg['config_ref']).read_text())
    assert reg==json.loads((root/'manifests/wc_e2_production_cpu_r1_preregistration_20261011.json').read_text())
    for n,h in reg['copies_readonly_sha256'].items():
        if n!='plans/WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md':
            raw=subprocess.check_output(['git','show',reg['copy_original_E2_CPU_source']+':'+n],cwd=root)
            assert hashlib.sha256(raw).hexdigest()==h,n
    for n in reg['new_local_files']:
        raw=subprocess.check_output(['git','show',launch['source_revision']+':'+n],cwd=root)
        assert hashlib.sha256(raw).hexdigest()==c['payload_sha256'][n],n
    proof['original_source_raw_identity_requests_and_scope_independently_verified']=True
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
