#!/usr/bin/env python3
"""Preserve original CPU evidence and independently compare the complete paths."""
import base64
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=('r1','r2'),default='r1');args=parser.parse_args()
    prefix='reports/wc_cfg_complete_native_policy_cpu_'+args.attempt+'_terminal_20261009_'
    launch=json.loads(Path('reports/wc_cfg_complete_native_policy_cpu_'+args.attempt+'_launch_20261009.json').read_text())
    remote='L='+repr(launch)+'\n'+r'''
import json,pathlib,hashlib,gzip,base64,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_COMPLETE_NATIVE_POLICY_CPU_STILL_LIVE','original_live_PIDs':live,'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((stage/'complete-native-policy-preregistration.json').read_text())
assert sha(stage/'complete-native-policy-preregistration.json')==L['registration_sha256']
assert r['planned_scope']==reg['CPU_scope']==L['CPU_scope']
assert r['payload_after_sha256']==reg['payload_sha256']=={n:sha(stage/n) for n in reg['payload_sha256']}
assert r['runtime_after_sha256']==reg['runtime_source_sha256']=={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
files={n:stage/n for n in ('receipt.json','core.log','driver.log','launch.json','complete-native-policy-preregistration.json')}
for n in ('result.json','result.failure.json'):
 if (stage/n).exists():files[n]=stage/n
if r['exit_code']==0:
 assert r['status']=='COMPLETE_NATIVE_POLICY_INTERFACE_CPU_NOT_REAL_MODEL' and r['child_exit_code']==0
 assert sha(stage/'result.json')==r['result_sha256']
items={}
for n,p in files.items():
 raw=p.read_bytes();z=gzip.compress(raw,mtime=0);items[n]={'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(z).hexdigest(),'base64':base64.b64encode(z).decode()}
capture={'status':'COMPLETE_NATIVE_POLICY_CPU_TERMINAL_SUCCESS' if r['exit_code']==0 else 'COMPLETE_NATIVE_POLICY_CPU_FAILURE_COMPLETE_SCOPE_RETAINED','source_revision':r['source_revision'],'exit_code':r['exit_code'],'original_PIDs_absent':pids,'CPU_wall_seconds':r['CPU_wall_seconds'],'payload_files':len(reg['payload_sha256']),'runtime_sources':len(reg['runtime_source_sha256']),'planned_scope':reg['CPU_scope'],'budget_before_sha256':r['budget_before_sha256'],'budget_after_sha256':r['budget_after_sha256'],'CPU_never_writes_ledger':r['ledger_written_by_this_driver'] is False,'GPU_submissions':0,'observed_unix':time.time()}
print(json.dumps({'capture':capture,'native':items}))
'''
    run=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=remote,text=True,capture_output=True,timeout=55)
    if run.returncode:raise RuntimeError(run.stderr[-4000:])
    result=json.loads(run.stdout);proof=result['capture']
    if not result['native']:print(json.dumps(proof));return 2
    target=Path(prefix+'capture_and_independent_audit.json');assert not target.exists()
    proof['files']={};objects={}
    for name,item in result['native'].items():
        z=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(z)
        assert hashlib.sha256(z).hexdigest()==item['compressed_sha256']
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        p=Path(prefix+name+'.native.gz');assert not p.exists();p.write_bytes(z)
        proof['files'][name]={k:v for k,v in item.items() if k!='base64'};proof['files'][name]['local_path']=str(p)
        if name.endswith('.json'):objects[name]=json.loads(raw)
    if proof['exit_code']==0:
        core=objects['result.json'];reg=objects['complete-native-policy-preregistration.json'];rows=core['checks']
        assert core['planned_scope']==reg['CPU_scope'] and core['payload_sha256']==reg['payload_sha256']
        assert not core['CUDA_initialized'] and core['GPU_submissions']==0 and len(rows)==20
        failures=[r for r in rows if r['kind']=='native_policy_tail_failure']
        rows=[r for r in rows if r['kind']=='complete_native_policy_full_sampler_comparison']
        assert len(rows)==16 and len(failures)==4
        assert {(r['flow'],r['failure']) for r in failures}=={(f,n) for f in (False,True) for n in ('selector_tail35','invalid_action_tail35')}
        assert all(r['status']=='EXPECTED_REJECTION' and r['completed_solver_steps']==34
            and r['whole_fixture_copy_discarded'] and r['poisoned_continuation_rejected']
            and not r['arbitrary_fault_full_rollback_claim'] for r in failures)
        assert {(r['flow'],r['profile'],r['observers'],r['repetition']) for r in rows}=={(f,p,o,n) for f in (False,True) for p in ('NATIVE_THRESHOLD','HIGH_THRESHOLD') for o in (False,True) for n in (0,1)}
        invariant=('velocity','solver_returns','checkpoints','actions','block_visits','final_latent_sha256','final_components','final_solver_sha256','generator_state_sha256','global_rng_sha256')
        summaries=[]
        for row in rows:
            original,paired=(row[k] for k in ('original_native','complete_paired_native_selector'))
            assert row['status']=='COMPLETE_NATIVE_POLICY_PARITY_NOT_POLICY_BENEFIT'
            assert row['solver_updates_per_path']==36 and row['net_calls_per_path']==72
            direct=row['all_36_guided_tensor_direct_equality'];assert direct==[True]*36
            assert all(d==(x==y) for d,x,y in zip(direct,original['velocity'],paired['velocity']))
            assert row['different_guided_steps']==[i+1 for i,d in enumerate(direct) if not d]
            assert row['different_action_steps']==[i+1 for i,(a,b) in enumerate(zip(original['actions'],paired['actions'])) if a!=b]
            assert row['final_latent_direct_equal']==(original['final_latent_sha256']==paired['final_latent_sha256'])
            assert row['final_latent_direct_equal'] and row['all_registered_state_fields_equal']
            assert not row['different_guided_steps'] and not row['different_action_steps'] and not row['different_state_steps']
            assert all(original[k]==paired[k] for k in invariant)
            assert original['condition_before']==paired['condition_before']
            assert original['condition_after']==paired['condition_after']
            for path in (original,paired):
                assert len(path['velocity'])==len(path['solver_returns'])==36 and len(path['final_components'])==50
                assert [x['step'] for x in path['checkpoints']]==[13,21,33,35,36]
                assert path['counters']==list(range(0,70,2))+[0] and len(path['actions'])==36
                assert path['roundtrip_step22_complete'] and path['condition_before']==path['condition_after']
                assert path['all_modules_eval'] and path['parameter_versions_unchanged']
                if row['observers']:
                    assert len(path['net_events'])==144
                    assert {(x['kind'],x['call']) for x in path['net_events']}=={(k,c) for k in ('before','after') for c in range(72)}
                else:assert not path['net_events']
            assert len(paired['prefix_decisions'])==28
            assert all(x['actual_prefix_visits_before_any_deep']==[2.,2.,0.,0.] for x in paired['prefix_decisions'])
            tail=paired['prefix_decisions'][-1]
            assert tail['step']==35 and tail['counter']==68 and tail['paid_counters']==[68,69]
            assert row['tail_two_prefixes_and_cycle_reset_covered']
            assert paired['native_policy_compiler']['inverse_AST_equal']
            assert paired['native_policy_compiler']['registered_transformation_sites']==5
            summaries.append({k:row[k] for k in ('flow','profile','observers','repetition','different_guided_steps','different_action_steps','different_state_steps','final_latent_direct_equal')})
        for flow in (False,True):
            for profile in ('NATIVE_THRESHOLD','HIGH_THRESHOLD'):
                group=[r for r in rows if r['flow']==flow and r['profile']==profile];assert len(group)==4
                for side in ('original_native','complete_paired_native_selector'):
                    assert all(all(r[side][k]==group[0][side][k] for k in invariant) for r in group)
        proof.update(complete_comparisons=16,complete_paths=32,solver_updates=1152,net_calls=2304,
            complete_36_tensor_direct_equality_and_full_state_records_verified=True,
            complete_observer_and_strict_repeat_groups_equal=True,all_registered_rows=summaries,
            local_second_tensor_loading=False,real_model_or_endpoint_or_policy_benefit_claim=False)
        proof.update(complete_tail_failure_controls=4,complete_rows=20,
            complete_native_policy_parity_and_tail_cycle_verified=True)
    target.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k not in ('files','all_registered_rows','planned_scope')}))
    return proof['exit_code']


if __name__=='__main__':raise SystemExit(main())
