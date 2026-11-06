"""Both flows, all eight diagnostic paths and complete prefix failure controls."""
import ast
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import e1_memory_diagnostic_sampling_r1 as diagnostic
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec);spec.loader.exec_module(module);return module


BODY=r'''    results=[];by_arm={}
    try:
        for arm in diagnostic.ARMS:
            names,methods=diagnostic.validate_arm(arm)
            chosen=[type(samples[0])(n) for n in names]
            local={**config,'sample_names':names}
            contexts=[(local['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in names]
            for scenario in ('complete','last_writer_failure') if arm['id'].endswith('PREFIX') else ('complete',):
                output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/arm['id']/scenario
                output.mkdir(parents=True,exist_ok=False)
                events=[];state={}
                def sink(record):
                    assert record['memory']['status']=='CPU_ONLY_NO_CUDA_INITIALIZATION'
                    events.append(record)
                batch,proof=diagnostic.compile_batch(arm,calibration=calibration,policy_specs=policy_specs,sink=sink)
                def save():
                    path=output/'receipt.json';temp=path.with_suffix('.tmp')
                    temp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');temp.replace(path)
                def writer(path,values):
                    if scenario=='last_writer_failure' and path.name=='human_199_A_CPD_BETA1_ONE_PHASE.pt':
                        raise ValueError('Injected E1 final vector writer failure')
                    return vector_file(path,values)
                error=None
                try:
                    batch(inference,chosen,wc,settings,state=state,save=save,output=output,
                        inference_module=inference_module,contexts=contexts,mode_setup=mode,
                        runtime=runtime,config=local,rf_module=rf,writer=writer)
                except BaseException as exc:error=str(exc)
                assert state['planned_parent_paths']==len(arm['paths']) and state['initial_state_restored']
                assert all(float(b)==0 for b in net.buffers()) and not any(m.training for m in net.modules())
                assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
                rows=[r for q in state['requests'] for r in q['paths']]
                assert len(rows)==len(arm['paths'])
                assert [(q['sample_name'],r['collect']) for q in state['requests'] for r in q['paths']]==[
                    (p['sample_name'],p['method']) for p in arm['paths']]
                assert len(events)==12*len(rows)
                assert [e['event'] for e in events[:3]]==[
                    'BEFORE_PHYSICAL_CAPTURE_GATE','BEFORE_ADDITIONAL_STATE','AFTER_ADDITIONAL_RESTORE_AND_RELEASE']
                assert all(e.get('additional_owned_storage',{}).get('unique_GPU_storage_bytes',0)==0 for e in events)
                for row in rows:
                    assert len(row['guided_sha256'])==36 and len(row['solver_returns'])==36
                    assert all(x['checkpoint_perturbation_executed'] for x in row['P0_roundtrips'])
                    assert [x['step'] for x in row['P0_roundtrips']]==[12,30,35,36]
                    if arm['storage'].startswith('CPU_'):
                        assert all(x['CPU_owned_storage_version']=='R1' for x in row['P0_roundtrips'])
                if scenario=='last_writer_failure':
                    assert error=='Injected E1 final vector writer failure',error
                    assert rows[-1]['status']=='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED'
                    assert 'vector_artifact' not in rows[-1] and len(list(output.rglob('*.pt')))==2
                    results.append({'flow':flow,'arm':arm['id'],'scenario':scenario,'status':'EXPECTED_FAILURE',
                        'receipt':state,'error':error,'events':events,'complete_scope_retained':True,'initial_state_restored':True})
                    continue
                assert error is None,error
                verifier=diagnostic.make_verifier(arm)
                verdict=verifier(state);raw=diagnostic.audit_vectors(state,arm,output,tensor_loader,local['expected_shape'])
                assert raw['actual_guided_reloaded']==36*len(rows) and raw['actual_final_latents_reloaded']==len(rows)
                refusals=[]
                for fault in ('missing_path','wrong_sample','wrong_method','missing_checkpoint','wrong_protected_action',
                              'wrong_A_strength','missing_head','wrong_source_age','foreign_birth_rule'):
                    bad=copy.deepcopy(state);row=bad['requests'][-1]['paths'][-1]
                    if fault=='missing_path':bad['requests'][-1]['paths'].pop()
                    elif fault=='wrong_sample':bad['requests'][-1]['sample_name']='OTHER'
                    elif fault=='wrong_method':row['collect']='CPD'
                    elif fault=='missing_checkpoint':row['P0_roundtrips'].pop()
                    elif fault=='wrong_protected_action':row['actions'][0]='CC'
                    elif fault=='wrong_A_strength':row['collection_complete']['deployment']['history'][0]['A_readout']['shared_alpha']=99
                    elif fault=='missing_head':row['collection_complete']['actual_original_plus_candidate_heads'].pop()
                    elif fault=='wrong_source_age':row['collection_complete']['deployment']['history'][0]['source_policy']['working_epoch_basis']['query_anchor']=-99
                    else:row['collection_complete']['deployment']['current_P_birth_rule']='FOREIGN'
                    try:verifier(bad)
                    except (ValueError,KeyError):refusals.append(fault)
                    else:raise AssertionError('Invalid E1 whole diagnostic state accepted: '+fault)
                path=Path(raw['files'][-1]['path']);old=path.read_bytes()
                try:
                    path.write_bytes(old[:-1])
                    try:diagnostic.audit_vectors(state,arm,output,tensor_loader,local['expected_shape'])
                    except ValueError:pass
                    else:raise AssertionError('Truncated E1 vector accepted')
                finally:path.write_bytes(old)
                by_arm[arm['id']]=rows
                results.append({'flow':flow,'arm':arm['id'],'scenario':scenario,'status':'PASS','receipt':state,
                    'verdict':verdict,'actual_tensor_audit':raw,'events':events,'scope_mutation_refusals':refusals,
                    'actual_truncation_refused':True,'compiler_proof':proof})
        parity_keys=('guided_sha256','guided_list_sha256','solver_returns','actions','counters',
                     'final_latent_sha256','conditions_before','conditions_after','rng_after',
                     'condition_fields_before','condition_fields_after','flags_before','flags_after','sample_return_sha256')
        for original,cpu in (('ORIGINAL_COLD','CPU_COLD'),('ORIGINAL_PREFIX','CPU_PREFIX')):
            for left,right in zip(by_arm[original],by_arm[cpu]):
                assert all(left[k]==right[k] for k in parity_keys)
                assert left['video_artifact']['sha256']==right['video_artifact']['sha256']
        for implementation in ('ORIGINAL','CPU'):
            cold=by_arm[implementation+'_COLD'][0];prefix=by_arm[implementation+'_PREFIX'][-1]
            assert all(cold[k]==prefix[k] for k in parity_keys)
            assert cold['video_artifact']['sha256']==prefix['video_artifact']['sha256']
        return results
'''


def fixture(calibration,policy_specs):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise));start=source.index('    results=[]\n')
    end=source.index('    finally:\n        inference.pipe._get_data_batch_input=original_prepare',start)
    previous=source[start:end];changed=source[:start]+BODY+source[end:]
    inverse=changed.replace(BODY,previous)
    assert inverse==source and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(source))
    ns={**original.exercise.__globals__,'diagnostic':diagnostic,'calibration':calibration,'policy_specs':policy_specs}
    exec(compile(changed,__file__+'#E1-full-Toy-fixture','exec'),ns)
    return ns['exercise']


def run(runtime,tensor_loader,artifact_root):
    calibration=Calibration('SYNTHETIC_E1_CURRENT_BIRTH_PRIOR',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},{s:1. for s in range(1,37)})
    baseline={'threshold':.07,'costs':Costs('SYNTHETIC_REFERENCE_RA_FULL_PAIR',1.,4.),'partial_prior':None}
    partial={'threshold':2.,'costs':Costs('SYNTHETIC_CPD_FULL_PAIR',3.,4.,1.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_CURRENT_BIRTH_FLOOR',.005,.3,early_creation_floor=.005,late_creation_floor=.02)}
    dense={'threshold':2.,'costs':Costs('SYNTHETIC_ACTUAL_D_CHEAPEST',4.,1.),'partial_prior':None}
    specs={m:{**dict(baseline if m in ('SOURCE_RA','DYNAMIC_NO_P') else dense if m=='DENSE_CONTROL' else partial),
        'working_epoch_strategy':'WORKING_P_AGE_KEEP_INTERVAL'} for m in diagnostic.original.METHODS}
    exercise=fixture(calibration,specs)
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(runtime=Path(runtime),
        tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    checks=result['checks'];success=[c for c in checks if c['status']=='PASS'];failures=[c for c in checks if c['status']=='EXPECTED_FAILURE']
    assert len(success)==8 and len(failures)==4
    assert sum(c['actual_tensor_audit']['actual_final_latents_reloaded'] for c in success)==16
    arm_refusals=0
    for arm in diagnostic.ARMS:
        for fault in ('missing_path','other_storage','wrong_method'):
            bad=copy.deepcopy(arm)
            if fault=='missing_path':bad['paths'].pop()
            elif fault=='other_storage':bad['storage']='OTHER'
            else:bad['paths'][-1]['method']='CPD'
            try:diagnostic.validate_arm(bad)
            except ValueError:arm_refusals+=1
            else:raise AssertionError('Unregistered E1 selector accepted')
    assert arm_refusals==12 and not torch.cuda.is_initialized()
    return {**result,'successful_complete_CPU_paths':16,'writer_failure_attempted_CPU_paths':12,
        'actual_complete_CPU_solver_updates':1008,'actual_normal_CPU_CFG_calls':2016,
        'actual_guided_reloaded':576,'actual_final_latents_reloaded':16,
        'scope_mutation_refusals':72,'arm_contract_refusals':arm_refusals,'actual_truncation_refusals':8,
        'metadata_observer_events':336,'original_CPU_and_cold_prefix_numerical_parity':True,
        'CPU_fixture_reuses_Toy_model_between_arms_not_real_four_model_loads':True,
        'real_GPU_capacity_or_failure_repair_claim':False,'GPU_submissions':0}
