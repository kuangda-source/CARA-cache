#!/usr/bin/env python3
"""Capture whole64 production CPU bytes and independently verify their source."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    launch_ref=Path('reports/wc_current_birth_full64_production_cpu_r1_launch_20261010.json')
    if not launch_ref.exists():
        print(json.dumps({'status':'WAIT_FULL64_PRODUCTION_CPU_LAUNCH_NO_CAPTURE','GPU_submissions':0}));return 2
    launch=json.loads(launch_ref.read_text())
    code='L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'FULL64_PRODUCTION_CPU_STILL_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(stage/'driver.py')==L['driver_sha256'] and sha(stage/'current-birth-full64-config.json')==L['config_sha256']
c=json.loads((stage/'current-birth-full64-config.json').read_text())
assert {n:sha(stage/n) for n in c['payload_sha256']}==r['payload_after_sha256']==c['payload_sha256']
assert {n:sha(root/'runtime'/n) for n in c['runtime_source_sha256']}==c['runtime_source_sha256']
assert r['GPU_submissions']==0 and not r['ledger_written'] and not r['GPU_lock_acquired'] and not r['CUDA_initialized']
assert r['budget_before_sha256']==r['budget_after_sha256']==sha(root/'reports/budget.json')
files=['receipt.json','current-birth-full64-config.json','driver.py','driver.log','test.log','launch.json']
if (stage/'result.json').exists():files.append('result.json')
native={}
for name in files:
 raw=(stage/name).read_bytes();packed=gzip.compress(raw,compresslevel=1,mtime=0)
 native[name]={'path':str(stage/name),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'status':'FULL64_PRODUCTION_CPU_TERMINAL_ORIGINAL_BYTES','source_revision':r['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'GPU_submissions':0,'budget_sha256_unchanged':r['budget_after_sha256'],'observed_unix':time.time()},'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-2000:])
    packet=json.loads(call.stdout)
    if not packet['native']:print(json.dumps(packet['capture']));return 2
    prefix='reports/wc_current_birth_full64_production_cpu_r1_terminal_20261010_'
    dest=Path(prefix+'capture.json');assert not dest.exists()
    proof=packet['capture'];proof['files']={};objects={}
    for name,item in packet['native'].items():
        packed=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(packed).hexdigest()==item['compressed_sha256']
        target=Path(prefix+name+'.native.gz');assert not target.exists();target.write_bytes(packed)
        proof['files'][name]={k:v for k,v in item.items() if k!='base64'};proof['files'][name]['local_path']=str(target)
        if name.endswith('.json'):objects[name]=json.loads(raw)
    try:
        c=objects['current-birth-full64-config.json'];r=objects['receipt.json']
        original=subprocess.check_output(['git','show',launch['source_revision']+':configs/wc_current_birth_full64_production_r1_20261010.json'])
        assert hashlib.sha256(original).hexdigest()==launch['config_sha256'] and json.loads(original)==c
        for name,digest in c['payload_sha256'].items():
            if name not in ('profile-config.json','current-birth-full64-requests.jsonl','budget-at-preparation.json'):
                assert hashlib.sha256(subprocess.check_output(['git','show',launch['source_revision']+':'+name])).hexdigest()==digest
        deploy=subprocess.check_output(['git','show',launch['source_revision']+':scripts/deploy_wc_current_birth_full64_production_cpu_r1.py'])
        tree=ast.parse(deploy);driver=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='DRIVER' for t in n.targets))
        assert hashlib.sha256(driver.encode()).hexdigest()==launch['driver_sha256']
        assert objects['launch.json']==launch
        if proof['exit_code']==0:
            value=objects['result.json'];assert r['child_exit_code']==0 and r['status']=='CURRENT_BIRTH_FULL64_PRODUCTION_CPU_PASS_NOT_GPU'
            assert proof['files']['result.json']['sha256']==r['result_sha256']
            sys_path='src/wcomr/current_birth_real_production_r1.py'
            source=ast.parse(subprocess.check_output(['git','show',launch['source_revision']+':'+sys_path]))
            dynamic=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='DYNAMIC' for t in n.targets))
            binding=hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in dynamic},sort_keys=True,
                separators=(',',':'),allow_nan=False).encode()).hexdigest()
            assert binding==r['config_binding_sha256']==value['config_binding_sha256']
            runner=ast.parse(subprocess.check_output(['git','show',launch['source_revision']+':scripts/run_wc_current_birth_full64_r1.py']))
            mutations=next(n.value for n in ast.walk(runner) if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='mutations' for t in n.targets))
            expected=[ast.literal_eval(k) for k in mutations.keys]+['request_'+k for k in ('seed','guidance','num_steps','name')]
            assert value['production_contract_mutation_refusals']==expected==r['production_contract_mutation_refusals']
            assert value['registered_scope']==c['preregistration']['scope_counts'] and value['registered_scope']['complete_paths']==64
            assert value['complete_method_parameter_sets']==16 and value['guardrail_less_entry_refused_both_strategies']
            assert value['actual_guardrail_Blocklist_four_CAL_and_original_forward_origin_checked']
            assert value['compatibility_wrapper_execution_callables_identical'] and not value['CUDA_initialized']
            assert value['actual_input_evidence']['binding_fingerprint']==c['input_binding_fingerprint']
            proof.update(independent_complete_source_contract_and_fixed_inputs_verified=True,
                config_binding_sha256=binding,actual_contract_refusals=expected,complete_parameter_sets=16)
    except BaseException as error:
        proof['independent_check_error']={'type':type(error).__name__,'message':str(error)}
        dest.write_text(json.dumps(proof,indent=2)+'\n');raise
    dest.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
