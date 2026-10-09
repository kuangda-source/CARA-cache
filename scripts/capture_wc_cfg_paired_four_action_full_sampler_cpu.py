#!/usr/bin/env python3
"""Original H-T60 CPU handles and native evidence; full-scope independent checks."""
import base64
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

PREFIX='reports/wc_cfg_paired_four_action_full_sampler_cpu_r1_terminal_20261009_'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',choices=('r1','r2'),default='r1');args=parser.parse_args()
    prefix=PREFIX.replace('_r1_','_'+args.attempt+'_')
    launch=json.loads(Path('reports/wc_cfg_paired_four_action_full_sampler_cpu_'+args.attempt+'_launch_20261009.json').read_text())
    source='L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:print(json.dumps({'capture':{'status':'ORIGINAL_PAIRED_PRODUCTION_CPU_STILL_LIVE','original_live_PIDs':live,'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((stage/'paired-four-action-full-sampler-preregistration.json').read_text())
assert sha(stage/'paired-four-action-full-sampler-preregistration.json')==L['registration_sha256']
assert r['payload_after_sha256']==reg['payload_sha256']=={n:sha(stage/n) for n in reg['payload_sha256']}
assert r['runtime_after_sha256']==reg['runtime_source_sha256']=={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
assert r['planned_scope']==reg['CPU_scope']==L['CPU_scope']
files={n:stage/n for n in ['receipt.json','core.log','driver.log','launch.json','paired-four-action-full-sampler-preregistration.json']}
for n in ['result.json','result.failure.json']:
 if (stage/n).exists():files[n]=stage/n
if r['exit_code']==0:
 assert r['status']=='PAIRED_FOUR_ACTION_FULL_SAMPLER_CPU_NOT_REAL_MODEL' and r['child_exit_code']==0
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
        core=objects['result.json'];reg=objects['paired-four-action-full-sampler-preregistration.json']
        assert core['status']=='PAIRED_FOUR_ACTION_FULL_SAMPLER_CPU_NOT_REAL_MODEL'
        assert core['planned_scope']==reg['CPU_scope'] and core['payload_sha256']==reg['payload_sha256']
        assert not core['CUDA_initialized'] and core['GPU_submissions']==0
        if True:
            adapter=core['actual_import_only_adapter']
            assert adapter['installed_package_present'] and adapter['CUDA_hardware_availability_not_overridden']
            assert adapter['original_helpers_and_current_device_restored'] and adapter['weights_load_forbidden']
            assert not adapter['GPU_runtime_adapter'] and not adapter['CUDA_initialized'] and not adapter['model_instantiated_by_actual_import']
        rows=core['checks'][:68];assert len(core['checks'])==112;main=[r for r in rows if r['kind']=='main_pair'];initial=[r for r in rows if r['kind']=='protected_initialization']
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
        full=[r for r in rows if r['kind']=='full_sampler_comparison']
        refused=[r for r in rows if r['kind']=='full_sampler_failure']
        assert len(full)==24 and len(refused)==8
        assert {(r['flow'],r['schedule'],r['observers'],r['repetition']) for r in full}=={(f,s,o,n) for f in (False,True) for s in ('CC','DD','ALTERNATING') for o in (False,True) for n in (0,1)}
        expected_steps={'selector_step23':22,'solver_tail':35,'net_binding':0,'condition_construction':0}
        assert {(r['flow'],r['failure']) for r in refused}=={(f,s) for f in (False,True) for s in expected_steps}
        for row in refused:
            assert row['status']=='EXPECTED_REJECTION' and row['whole_fixture_copy_discarded'] and not row['arbitrary_fault_full_rollback_claim']
            assert row['planned_solver_steps']==36 and row['completed_solver_steps']==expected_steps[row['failure']]
        path_keys=('velocity','solver_returns','checkpoints','actions','counters','block_visits','condition_before','condition_after','roundtrip_step22_complete','final_latent_sha256','final_components','final_solver_sha256','generator_state_sha256','global_rng_sha256')
        for row in full:
            ref,new=row['original'],row['paired']
            assert row['status']=='PASS' and row['solver_updates_per_path']==36 and row['net_calls_per_path']==72
            assert all(ref[k]==new[k] for k in path_keys)
            assert len(new['velocity'])==len(new['solver_returns'])==36 and new['counters']==list(range(0,70,2))+[0]
            assert [r['step'] for r in new['checkpoints']]==[13,21,33,35,36]
            assert new['condition_before']==new['condition_after'] and new['roundtrip_step22_complete']
            assert new['parameter_versions_unchanged'] and new['all_modules_eval']
            if row['observers']:
                assert len(ref['net_events'])==len(new['net_events'])==144
                assert {(r['kind'],r['call']):r for r in ref['net_events']}=={(r['kind'],r['call']):r for r in new['net_events']}
                assert {(r['kind'],r['call']) for r in new['net_events']}=={(k,c) for k in ('before','after') for c in range(72)}
            else:assert not ref['net_events'] and not new['net_events']
            proof=new['velocity_compiler']
            assert proof['velocity_inverse_AST_equal'] and proof['condition_construction_and_CFG_arithmetic_unchanged']
            assert proof['two_adjacent_denoise_assignments_replaced'] and not proof['real_model_or_policy_claim']
            assert all(v['binding'] in ('actual_module_global','builtin','explicit_compiler_helper') for v in proof['production_velocity_globals'].values())
            expected_actions=['DD' if c<4 or c>=68 else (row['schedule'] if row['schedule']!='ALTERNATING' else ('CC' if (c//2)%2==0 else 'DD')) for c in new['counters']]
            assert new['actions']==expected_actions
            assert new['block_visits']==[([2.,2.,2.,2.] if a=='DD' else [2.,2.,0.,0.]) for a in expected_actions]
        invariant=('velocity','solver_returns','checkpoints','actions','block_visits','final_latent_sha256','final_components','final_solver_sha256','generator_state_sha256','global_rng_sha256')
        for flow in (False,True):
            for schedule in ('CC','DD','ALTERNATING'):
                group=[r['paired'] for r in full if r['flow']==flow and r['schedule']==schedule]
                assert len(group)==4 and all(all(r[k]==group[0][k] for k in invariant) for r in group)
        origins=[r for r in rows if r['kind']=='local_interface_origin']
        parents=[r for r in rows if r['kind']=='local_interface_full_parent_parity']
        assert len(rows)==68 and {r['flow'] for r in origins}=={False,True} and len(origins)==2
        assert {r['flow'] for r in parents}=={False,True} and len(parents)==2
        expected=[(a,o,q,p) for a in ('CC','DD') for o in (False,True) for q in ('first','second') for p in ('ORIGINAL','PAIRED')]
        same=('origin_components','origin_fingerprint','origin_solver_configuration','pair_end_components',
              'pair_end_fingerprint','pair_end_solver_configuration','branch_sha256','guided_sha256','block_visits')
        for origin in origins:
            local=origin['comparisons']
            assert len(local)==16 and [(r['action'],r['observers'],r['repetition'],r['order']) for r in local]==expected
            assert origin['direct_tensor_equality_all_orders_observers_and_repeats'] and origin['binding_objects_restored']
            for action in ('CC','DD'):
                group=[r for r in local if r['action']==action]
                assert len(group)==8 and all(all(r[k]==group[0][k] for k in same) for r in group)
                for row in group:
                    assert row['status']=='COMPLETE_LOCAL_INTERFACE_REQUIRES_AUDIT' and row['parent_restored'] and row['bindings_restored']
                    assert row['parent_after_components']==row['origin_components']
                    assert not row['endpoint_label'] and not row['future_cost_label']
                    assert row['block_visits']==([2,2,0,0] if action=='CC' else [2,2,2,2])
                    assert row['current_velocity_instrumented_wall_seconds']>0
                    if row['order']=='PAIRED':
                        assert row['direct_torch_equal_against_original'] and row['selector_calls']==1
                        assert [(p['slot'],p['counter']) for p in row['paid_probes']]==[(0,44),(1,45)]
                        assert row['compiler']['actual_original_WC_RF_function_origins_verified']
                    else:assert row['selector_calls']==0 and not row['paid_probes']
                for observer in (False,True):
                    for repeat in ('first','second'):
                        old,new=[r for r in group if r['observers']==observer and r['repetition']==repeat]
                        if observer:
                            assert [(e['kind'],e['slot']) for e in old['observer_events']]==[('before',0),('after',0),('before',1),('after',1)]
                            assert [(e['kind'],e['slot']) for e in new['observer_events']]==[('before',0),('before',1),('after',0),('after',1)]
                            assert {(e['kind'],e['slot']):e for e in old['observer_events']}=={(e['kind'],e['slot']):e for e in new['observer_events']}
                        else:assert not old['observer_events'] and not new['observer_events']
            failures=origin['declared_failures']
            assert len(failures)==2 and {r['failure'] for r in failures}=={'selector','after_first'}
            assert all(r['status']=='LOCAL_INTERFACE_FAILED_SCOPE_RETAINED' and r['executor_poisoned'] and r['parent_restored']
                       and r['bindings_restored'] and r['parent_after_components']==r['origin_components'] for r in failures)
        for parent in parents:
            trace=parent['trace']
            assert parent['status']=='PASS' and parent['both_full36_72_parents_equal'] and parent['final_latent_direct_torch_equal']
            assert not parent['real_model_or_decode_video_claim']
            assert len(trace['velocity'])==len(trace['solver_returns'])==36 and len(trace['net'])==len(trace['branches'])==72
            assert [r['step'] for r in trace['checkpoints']]==[13,21,33,35,36]
            assert trace['condition_before']==trace['condition_after']
        batches=[r for r in rows if r['kind']=='actual_interface_batch']
        assert len(batches)==4 and {(r['flow'],r['scenario']) for r in batches}=={(f,s) for f in (False,True) for s in ('complete','writer_failure')}
        for row in batches:
            state=row['receipt']
            assert (state['planned_parents'],state['planned_videos'],state['planned_local_pairs'])==(2,2,16)
            local=state['parents'][-1]['origin']['pairs']
            assert len(local)==16 and all(r['parent_restored'] and r['bindings_restored'] for r in local)
            if row['scenario']=='complete':
                assert row['status']=='PASS' and row['raw_tensors_reloaded']==48 and row['guided_and_cross_order_observer_repeats_direct_equal']
                assert len(row['semantic_evidence_mutations_refused'])==10 and state['verdict']['raw_tensor_count']==48
                assert all(state['verdict']['full_parent_parity'].values())
                assert all(len(p['inputs'])==72 and len(p['solver_outputs'])==36 for p in state['parents'])
            else:
                assert row['status']=='EXPECTED_FAILURE' and row['complete_scope_retained'] and row['initial_full_state_restored']
                assert 'artifact' not in local[-1] and state['parents'][-1]['origin']['status']=='INTERFACE_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED'
        result.update(actual_new_batch_successful_full_parents=4,actual_new_batch_pairs=32,actual_Toy_raw_tensors_reloaded=96,actual_new_batch_writer_failures=2,actual_new_batch_semantic_mutation_refusals=20)
        result.update(complete_full_sampler_comparisons=24,complete_parent_paths=48,solver_updates=1728,branch_net_calls=3456,
                      new_complete_failure_controls=8,complete_velocity_full_sampler_audit=True,
                      full_repetitions_and_observer_ON_OFF_equal=True)
        result.update(local_complete_scope_and_branch_observer_audit=True,main_pairs=8,initial_pairs=2,failure_controls=16,
                      original_order_and_paired_branch_input_output_all_equal=True,
                      real_model_output_or_latency_claim=False,local_second_tensor_reconstruction=False)
        result.update(new_S22_origins=2,new_local_comparisons=16,new_local_pairs=32,new_declared_failure_controls=4,
                      new_full_original_parents=4,new_parent_solver_updates=144,new_parent_net_calls=288,
                      full_S22_binding_observer_repeat_and_original_parent_audit=True)
        new_rows=core['checks'][68:];full=[r for r in new_rows if r['kind']=='four_action_full_sampler_comparison'];refused=[r for r in new_rows if r['kind']=='four_action_full_sampler_failure']
        assert len(full)==32 and len(refused)==12
        config=json.loads(Path('configs/wc_paired_four_action_full_sampler_cpu_schedules_20261009.json').read_text())
        assert hashlib.sha256(Path('configs/wc_paired_four_action_full_sampler_cpu_schedules_20261009.json').read_bytes()).hexdigest()==reg['payload_sha256']['configs/wc_paired_four_action_full_sampler_cpu_schedules_20261009.json']==core['action_schedules_sha256']
        assert {(r['flow'],r['schedule'],r['observers'],r['repetition']) for r in full}=={(f,s,o,q) for f in (False,True) for s in config['schedules'] for o in (False,True) for q in (0,1)}
        expected_failures={'selector_step23':22,'solver_tail':35,'net_binding':0,'condition_construction':0,'invalid_action_step23':22,'selector_rng_step23':22}
        assert {(r['flow'],r['failure']) for r in refused}=={(f,s) for f in (False,True) for s in expected_failures}
        for row in refused:
            assert row['status']=='EXPECTED_REJECTION' and row['whole_fixture_copy_discarded'] and not row['arbitrary_fault_full_rollback_claim']
            assert row['planned_solver_steps']==36 and row['completed_solver_steps']==expected_failures[row['failure']]
        for row in full:
            ref,new=row['original'],row['paired'];assert row['status']=='PASS' and row['all_36_guided_tensors_direct_equal']
            assert all(ref[k]==new[k] for k in path_keys)
            assert len(new['velocity'])==len(new['solver_returns'])==36 and new['counters']==list(range(0,70,2))+[0]
            assert [x['step'] for x in new['checkpoints']]==[13,21,33,35,36]
            assert all(len(x['components'])==50 for x in new['checkpoints']) and len(new['final_components'])==50
            assert new['roundtrip_step22_complete'] and new['condition_before']==new['condition_after']
            if row['observers']:
                assert len(ref['net_events'])==len(new['net_events'])==144
                assert {(x['kind'],x['call']):x for x in ref['net_events']}=={(x['kind'],x['call']):x for x in new['net_events']}
            else:assert not ref['net_events'] and not new['net_events']
            sequence=config['schedules'][row['schedule']];assert row['full_action_sequence']==sequence
            expected=['DD' if c<14 or c>=68 else sequence[i] for i,c in enumerate(new['counters'])]
            assert new['actions']==expected and new['block_visits']==[[2.,2.,float(a.count('D')),float(a.count('D'))] for a in expected]
            assert len(new['prefix_decisions'])==27
            for d in new['prefix_decisions']:
                assert d['actual_prefix_visits_before_any_deep']==[2.,2.,0.,0.] and d['paid_slots']==[0,1] and d['paid_counters']==[d['counter'],d['counter']+1]
                assert d['chosen_action']==sequence[d['step']-1]
            assert new['mixed_compiler']['inverse_AST_equal'] and new['mixed_compiler']['allowed_actions']==['CC','DC','CD','DD']
            assert new['velocity_compiler']['velocity_inverse_AST_equal']
        for flow in (False,True):
            for schedule in config['schedules']:
                group=[r['paired'] for r in full if r['flow']==flow and r['schedule']==schedule]
                assert len(group)==4 and all(all(r[k]==group[0][k] for k in invariant) for r in group)
        result.update(new_four_action_comparisons=32,new_four_action_full_paths=64,new_four_action_solver_updates=2304,new_four_action_net_calls=4608,new_four_action_failure_controls=12,all_legacy_68_controls_and_complete_new_matrix_verified=True,full_four_action_cpu_not_real_model=True)
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'}))
    return result['exit_code']


if __name__=='__main__':raise SystemExit(main())
