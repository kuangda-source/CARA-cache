#!/usr/bin/env python3
"""Capture/verify the original source-bound production CPU terminal; no dispatch."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

PREFIX='reports/wc_cfg_confirmation_selected_cpu_r1_terminal_20261009_'


def main():
    launch=json.loads(Path('reports/wc_cfg_confirmation_selected_cpu_r1_launch_20261009.json').read_text())
    source='L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_PRODUCTION_CPU_STILL_LIVE_NO_CAPTURE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert r['budget_before_sha256']==r['budget_after_sha256']==L['budget_before_sha256']==sha(root/'reports/budget.json')
c=json.loads((stage/'teacher-config.json').read_text())
assert {n:sha(stage/n) for n in c['payload_sha256']}==r['payload_after_sha256']==c['payload_sha256'] and len(c['payload_sha256'])==77
assert {n:sha(root/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
assert sha(stage/'teacher-config.json')==r['config_sha256']==L['config_sha256']
if r['exit_code']==0:
 assert r['status']=='TEACHER_PRODUCTION_CPU_PASS_NOT_GPU' and r['child_exit_code']==0
 assert sha(stage/'CPU-result.json')==r['result_sha256']
 v=json.loads((stage/'CPU-result.json').read_text());assert not v['CUDA_initialized'] and v['GPU_submissions']==0
 assert len(v['production_contract_mutation_refusals'])==12 and v['payload_sha256']==c['payload_sha256']
 assert v['registered_scope']==c['preregistration']['scope_counts']
files={n:stage/n for n in ['receipt.json','teacher-config.json','launch.json','deployment.json','production-CPU.log','driver.log']}
if (stage/'CPU-result.json').exists():files['CPU-result.json']=stage/'CPU-result.json'
native={}
for n,p in files.items():
 raw=p.read_bytes();compressed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'base64':base64.b64encode(compressed).decode()}
print(json.dumps({'capture':{'status':'CONFIRMATION_PRODUCTION_CPU_NATIVE_TERMINAL_SUCCESS' if r['exit_code']==0 else 'CONFIRMATION_PRODUCTION_CPU_NATIVE_FAILURE_SCOPE_RETAINED',
 'original_PIDs_absent':pids,'source_revision':r['source_revision'],'stage':str(stage),'CPU_wall_seconds':r['CPU_wall_seconds'],'exit_code':r['exit_code'],
 'payload_files':77,'budget_sha256_unchanged':r['budget_after_sha256'],'config_binding_sha256':r.get('config_binding_sha256'),'GPU_submissions':0},'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=source,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    proof=value['capture'];dest=Path(PREFIX+'capture.json');assert not dest.exists();proof['files']={};objects={}
    for name,item in value['native'].items():
        compressed=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(compressed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(compressed).hexdigest()==item['compressed_sha256']
        path=Path(PREFIX+name+'.native.gz');assert not path.exists();path.write_bytes(compressed)
        proof['files'][name]={k:v for k,v in item.items() if k!='base64'};proof['files'][name]['local_path']=str(path)
        if name.endswith('.json'):objects[name]=json.loads(raw)
    if proof['exit_code']==0:
        c=objects['teacher-config.json'];r=objects['receipt.json'];v=objects['CPU-result.json']
        dynamic={'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}
        binding=hashlib.sha256(json.dumps({k:x for k,x in c.items() if k not in dynamic},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert binding==proof['config_binding_sha256']==r['config_binding_sha256']==v['config_binding_sha256']
        assert v['request']['name']=='human_199_seed3' and v['request']['seed']==3
        proof['local_native_bytes_binding_scope_and_request_verified']=True
        proof['actual_contract_refusals']=v['production_contract_mutation_refusals']
    dest.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
