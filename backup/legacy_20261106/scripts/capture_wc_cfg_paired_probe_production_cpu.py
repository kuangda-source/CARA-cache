#!/usr/bin/env python3
"""Original H-T54 CPU handles and native evidence; full-scope independent checks."""
import base64
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

PREFIX='reports/wc_cfg_paired_probe_production_cpu_r1_terminal_20261009_'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=('r1','r2'),default='r1');args=parser.parse_args()
    prefix=PREFIX.replace('_r1_','_'+args.attempt+'_')
    launch=json.loads(Path('reports/wc_cfg_paired_probe_production_cpu_'+args.attempt+'_launch_20261009.json').read_text())
    source='L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_PAIRED_PRODUCTION_CPU_STILL_LIVE','original_live_PIDs':live,'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((stage/'paired-probe-production-preregistration.json').read_text())
assert sha(stage/'paired-probe-production-preregistration.json')==L['registration_sha256']
assert r['payload_after_sha256']==reg['payload_sha256']=={n:sha(stage/n) for n in reg['payload_sha256']}
assert r['runtime_after_sha256']==reg['runtime_source_sha256']=={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
assert r['planned_scope']==reg['CPU_scope']==L['CPU_scope']
files={n:stage/n for n in ['receipt.json','core.log','driver.log','launch.json','paired-probe-production-preregistration.json']}
for n in ['result.json','result.failure.json']:
 if (stage/n).exists():files[n]=stage/n
if r['exit_code']==0:
 assert r['status']=='PAIRED_PROBE_ACTUAL_GLOBALS_OBSERVER_COMPLETE_CPU_NOT_REAL_MODEL' and r['child_exit_code']==0
 assert sha(stage/'result.json')==r['result_sha256']
items={}
for n,p in files.items():
 raw=p.read_bytes();compressed=gzip.compress(raw,mtime=0)
 items[n]={'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'base64':base64.b64encode(compressed).decode()}
capture={'status':'PAIRED_PRODUCTION_CPU_ORIGINAL_NATIVE_TERMINAL_SUCCESS' if r['exit_code']==0 else 'PAIRED_PRODUCTION_CPU_ORIGINAL_NATIVE_FAILURE_COMPLETE_SCOPE_RETAINED',
 'source_revision':r['source_revision'],'exit_code':r['exit_code'],'original_PIDs_absent':pids,'CPU_wall_seconds':r['CPU_wall_seconds'],
 'payload_files':len(reg['payload_sha256']),'runtime_sources':len(reg['runtime_source_sha256']),
 'budget_before_sha256':r['budget_before_sha256'],'budget_after_sha256':r['budget_after_sha256'],
 'CPU_never_writes_ledger':r['ledger_written_by_this_driver'] is False,'current_budget_sha256':sha(root/'reports/budget.json'),
 'planned_scope':reg['CPU_scope'],'observed_unix':time.time(),'GPU_submissions':0}
print(json.dumps({'capture':capture,'native':items}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=source,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    result=value['capture'];output=Path(prefix+'capture_and_independent_audit.json');assert not output.exists()
    result['files']={};objects={}
    for name,item in value['native'].items():
        compressed=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest()==item['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest()==item['sha256'] and len(raw)==item['bytes']
        target=Path(prefix+name+'.native.gz');assert not target.exists();target.write_bytes(compressed)
        result['files'][name]={k:v for k,v in item.items() if k!='base64'};result['files'][name]['local_path']=str(target)
        if name.endswith('.json'):objects[name]=json.loads(raw)
    if result['exit_code']==0:
        core=objects['result.json'];reg=objects['paired-probe-production-preregistration.json']
        assert core['status']=='PAIRED_PROBE_ACTUAL_GLOBALS_AND_OBSERVERS_COMPLETE_TOY_CPU_NOT_REAL_MODEL_OR_POLICY'
        assert core['planned_scope']==reg['CPU_scope'] and core['payload_sha256']==reg['payload_sha256']
        assert not core['CUDA_initialized'] and core['GPU_submissions']==0
        if args.attempt=='r2':
            adapter=core['actual_import_only_adapter']
            assert adapter['installed_package_present'] and adapter['CUDA_hardware_availability_not_overridden']
            assert adapter['original_helpers_and_current_device_restored'] and adapter['weights_load_forbidden']
            assert not adapter['GPU_runtime_adapter'] and not adapter['CUDA_initialized'] and not adapter['model_instantiated_by_actual_import']
        rows=core['checks'];main=[r for r in rows if r['kind']=='main_pair'];initial=[r for r in rows if r['kind']=='protected_initialization']
        failures=[r for r in rows if r['kind']=='failure_control'];contracts=[r for r in rows if r['kind']=='source_contract']
        assert (len(main),len(initial),len(failures),len(contracts))==(8,2,16,2)
        assert {(r['flow'],r['action'],r['repetition']) for r in main}=={(f,m,q) for f in (False,True) for m in ('CC','DD') for q in (0,1)}
        expected_failures={'selector_exception','mixed_action','counter_mutation','outer_net_hook','forward_attribute_wrapper','denoise_attribute_wrapper','before_second','after_first'}
        assert {(r['flow'],r['failure']) for r in failures}=={(f,x) for f in (False,True) for x in expected_failures}
        for row in main:
            assert row['status']=='PASS' and row['counter']==46
            assert row['outputs_equal'] and row['guided_FP32_equal'] and row['input_conditions_equal'] and row['CPU_RNG_equal']
            for key in ('outputs','guided','state'):assert row['original_order_'+key+'_sha256']==row['paired_order_'+key+'_sha256']
            ref,new=row['reference_observer_events'],row['paired_observer_events']
            assert [(r['kind'],r['slot']) for r in ref]==[('before',0),('after',0),('before',1),('after',1)]
            assert [(r['kind'],r['slot']) for r in new]==[('before',0),('before',1),('after',0),('after',1)]
            assert {(r['kind'],r['slot']):r for r in ref}=={(r['kind'],r['slot']):r for r in new}
            assert row['block_visit_delta']==([2.,2.,0.,0.] if row['action']=='CC' else [2.,2.,2.,2.])
            assert [(p['slot'],p['counter']) for p in row['paid_probes']]==[(0,44),(1,45)]
        for row in initial:
            assert row['status']=='PASS' and row['counter']==2
            assert row['original_order_outputs_sha256']==row['paired_order_outputs_sha256']
            assert row['original_order_state_sha256']==row['paired_order_state_sha256']
        assert all(r['status']=='EXPECTED_REJECTION' and r['poisoned_continuation_rejected'] and r['whole_fixture_copy_discarded'] and not r['arbitrary_fault_rollback_claim'] for r in failures)
        for row in contracts:
            p=row['compiler'];assert p['actual_original_WC_RF_function_origins_verified'] and p['explicit_net_observers']
            assert p['WC_inverse_AST_equal'] and p['RF_inverse_AST_equal']
            assert all(v['binding'] in ('actual_module_global','builtin','explicit_compiler_helper') for k in ('production_WC_globals','production_RF_globals') for v in p[k].values())
        result.update(local_complete_scope_and_branch_observer_audit=True,main_pairs=8,initial_pairs=2,failure_controls=16,
                      original_order_and_paired_branch_input_output_all_equal=True,
                      real_model_output_or_latency_claim=False,local_second_tensor_reconstruction=False)
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))
    return result['exit_code']


if __name__=='__main__':raise SystemExit(main())
