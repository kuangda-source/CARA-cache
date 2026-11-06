"""Affected run-block wiring on one unchanged Toy model per flow/strategy.

Reuse the accepted fixture setup. Compare storage/persistence implementations
on identical live weights and RNG; do not rerun the old full128 method grid.
"""
import ast
import copy
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import e3_complete64_block_sampling_r1 as blocks
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.prepared_input import RNGState


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=module_from_spec(spec);spec.loader.exec_module(module);return module


BODY=r'''    results=[]
    try:
        target_name=scope['sample_names'][2] if strategy==scope['strategies'][0] else scope['sample_names'][0]
        selected_blocks=[b for b in scope['blocks'] if b['strategy']==strategy and b['paths'][0]['sample_name']==target_name]
        assert [len(b['paths']) for b in selected_blocks]==[3,3,2]
        failure_block=next(b for b in selected_blocks if len(b['paths'])==3 and all(p['method']!='SOURCE_RA' for p in b['paths']))
        for block in selected_blocks:
            initial_rng=RNGState();paired=[]
            for original_control in (True,False):
                initial_rng.restore()
                output=Path(artifact_root)/strategy/('flow_ON' if flow else 'flow_OFF')/block['id']/('ORIGINAL_CONTROL' if original_control else 'CPU_PERSIST')
                output.mkdir(parents=True,exist_ok=False)
                state={};saved_prepares=[]
                names,methods=blocks.validate_block(block,scope)
                chosen=[type(samples[0])(n) for n in names]
                local={**config,'sample_names':names}
                contexts=[(local['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in names]
                def save():
                    path=output/'receipt.json';temp=path.with_suffix('.tmp')
                    temp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');temp.replace(path)
                    if state.get('requests') and state['requests'][-1].get('prepared_input_calls'):
                        q=state['requests'][-1]
                        if q['paths'][-1]['status']=='STARTED':saved_prepares.append(len(q['prepared_input_calls']))
                batch,proof=blocks.compile_batch(block,scope,calibration=calibration,
                    policy_specs=policy_specs,CPU_original_control=original_control)
                batch(inference,chosen,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,contexts=contexts,mode_setup=mode,
                    runtime=runtime,config=local,rf_module=rf)
                assert state['initial_state_restored'] and all(float(b)==0 for b in net.buffers())
                assert not any(m.training for m in net.modules())
                assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
                verifier=blocks.make_verifier(block,scope);verdict=verifier(state)
                raw=blocks.audit_vectors(state,block,scope,output,tensor_loader,local['expected_shape'])
                rows=[r for q in state['requests'] for r in q['paths']]
                assert len(rows)==len(block['paths']) and len(state['requests'][0]['prepared_input_calls'])==len(rows)
                assert [r['collect'] for r in rows]==[p['method'] for p in block['paths']]
                restored=0
                for row in rows:
                    assert [r['step'] for r in row['P0_roundtrips']]==[12,30,35,36]
                    if row['collect']=='SOURCE_RA':continue
                    assert all(v['checkpoint_perturbation_executed'] for v in row['P0_roundtrips'])
                    if not original_control:
                        assert all(v['CPU_owned_storage_version']=='R1' for v in row['P0_roundtrips'])
                        restored+=4
                if not original_control:
                    assert set(saved_prepares)==set(range(1,len(rows)+1))
                refusals=[]
                for fault in ('missing_path','wrong_strategy','missing_checkpoint','foreign_birth_rule','missing_head','wrong_A_strength'):
                    bad=copy.deepcopy(state)
                    row=next(r for q in bad['requests'] for r in q['paths'] if r['collect']!='SOURCE_RA')
                    deployment=row['collection_complete']['deployment']
                    if fault=='missing_path':bad['requests'][-1]['paths'].pop()
                    elif fault=='wrong_strategy':deployment['working_epoch_strategy']='FOREIGN'
                    elif fault=='missing_checkpoint':row['P0_roundtrips'].pop()
                    elif fault=='foreign_birth_rule':deployment['current_P_birth_rule']='FOREIGN'
                    elif fault=='missing_head':row['collection_complete']['actual_original_plus_candidate_heads'].pop()
                    else:deployment['history'][0]['A_readout']['shared_alpha']=99
                    try:verifier(bad)
                    except (ValueError,KeyError):refusals.append(fault)
                    else:raise AssertionError('Invalid E3 block evidence accepted: '+fault)
                truncated=Path(raw['files'][-1]['path']);original=truncated.read_bytes()
                try:
                    truncated.write_bytes(original[:-1])
                    try:blocks.audit_vectors(state,block,scope,output,tensor_loader,local['expected_shape'])
                    except ValueError:pass
                    else:raise AssertionError('Truncated E3 vector accepted')
                finally:truncated.write_bytes(original)
                record={'status':'PASS','working_epoch_strategy':strategy,'flow':flow,'block':block,
                    'CPU_original_control':original_control,'receipt':state,'verdict':verdict,
                    'actual_tensor_audit':raw,'scope_mutation_refusals':refusals,
                    'actual_truncation_refused':True,'compiler_proof':proof,
                    'actual_CPU_storage_roundtrips':restored,'prepare_saved_before_path_completion':not original_control}
                results.append(record);paired.append(record)
            comparisons=[]
            for left,right in zip(paired[0]['receipt']['requests'][0]['paths'],paired[1]['receipt']['requests'][0]['paths']):
                parity_keys=('guided_sha256','guided_list_sha256','solver_returns','actions','counters',
                    'final_latent_sha256','conditions_before','conditions_after','rng_after',
                    'condition_fields_before','condition_fields_after','flags_before','flags_after','sample_return_sha256')
                assert all(left[k]==right[k] for k in parity_keys)
                assert left['video_artifact']['sha256']==right['video_artifact']['sha256']
                x,y=[tensor_loader(Path(v['vector_artifact']['path']),map_location='cpu',weights_only=True) for v in (left,right)]
                equal=[torch.equal(v,w) for v,w in zip(x['guided']+[x['final_latent']],y['guided']+[y['final_latent']])]
                assert len(equal)==37 and all(equal)
                comparisons.append({'method':left['collect'],'equal_guided36_and_final':equal,'all_equal':all(equal)})
                del x,y
            paired[1]['actual_direct_numerical_comparisons']=comparisons
        block=failure_block;names,methods=blocks.validate_block(block,scope)
        chosen=[type(samples[0])(n) for n in names];local={**config,'sample_names':names}
        contexts=[(local['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in names]
        output=Path(artifact_root)/strategy/('flow_ON' if flow else 'flow_OFF')/'LAST_WRITER_FAILURE'
        output.mkdir(parents=True,exist_ok=False);state={};disk_counts=[]
        def save():
            p=output/'receipt.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(p)
            q=(state.get('requests') or [{}])[-1]
            disk_counts.append(len(q.get('prepared_input_calls',[])))
        def writer(path,values):
            if path.name==names[0]+'_'+block['paths'][-1]['method']+'.pt':raise ValueError('Injected E3 last vector writer failure')
            return vector_file(path,values)
        batch,proof=blocks.compile_batch(block,scope,calibration=calibration,policy_specs=policy_specs)
        try:
            batch(inference,chosen,wc,settings,state=state,save=save,output=output,
                inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,
                config=local,rf_module=rf,writer=writer)
        except ValueError as error:assert str(error)=='Injected E3 last vector writer failure'
        else:raise AssertionError('E3 injected writer failure swallowed')
        assert state['initial_state_restored'] and state['planned_parent_paths']==3
        assert len(state['requests'][0]['prepared_input_calls'])==3 and max(disk_counts)==3 and disk_counts[0]==0
        rows=state['requests'][0]['paths'];assert len(rows)==3 and all(len(r['guided_sha256'])==36 for r in rows)
        assert rows[-1]['status']=='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED' and 'vector_artifact' not in rows[-1]
        assert len(list(output.rglob('*.pt')))==2
        assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
        results.append({'status':'EXPECTED_FAILURE','working_epoch_strategy':strategy,'flow':flow,
            'block':block,'receipt':state,'complete_declared_block_retained':True,
            'actual_prepare3_before_failure_persisted':True,'initial_state_and_MLP_hooks_restored':True,
            'actual_CPU_storage_roundtrips':12,'compiler_proof':proof})
        return results
'''


def fixture(scope,strategy,calibration,policy_specs):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise));start=source.index('    results=[]\n')
    end=source.index('    finally:\n        inference.pipe._get_data_batch_input=original_prepare',start)
    previous=source[start:end];changed=source[:start]+BODY+source[end:]
    assert changed.replace(BODY,previous)==source and ast.dump(ast.parse(changed.replace(BODY,previous)))==ast.dump(ast.parse(source))
    ns={**original.exercise.__globals__,'blocks':blocks,'scope':scope,'strategy':strategy,
        'calibration':calibration,'policy_specs':policy_specs,'RNGState':RNGState}
    exec(compile(changed,__file__+'#affected-block-CPU-fixture','exec'),ns)
    return ns['exercise']


def run(runtime,tensor_loader,artifact_root):
    scope=json.loads((Path(__file__).resolve().parents[1]/'manifests/wc_e3_complete64_reuse10_fresh54_blocks_r1_20261011.json').read_text())
    calibration=Calibration('SYNTHETIC_CREATION_PHASE_FULL36_RA_PRIOR',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},{s:1. for s in range(1,37)})
    baseline={'threshold':.07,'costs':Costs('SYNTHETIC_REFERENCE_RA_FULL_PAIR',1.,4.),'partial_prior':None}
    partial={'threshold':2.,'costs':Costs('SYNTHETIC_CPD_FULL_PAIR',3.,4.,1.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_CREATION_PHASE_FLOOR',.005,.3,early_creation_floor=.005,late_creation_floor=.02)}
    dense={'threshold':2.,'costs':Costs('SYNTHETIC_ACTUAL_D_CHEAPEST',4.,1.),'partial_prior':None}
    checks=[]
    for strategy in scope['strategies']:
        specs={m:{**dict(baseline if m in ('SOURCE_RA','DYNAMIC_NO_P') else dense if m=='DENSE_CONTROL' else partial),
                  'working_epoch_strategy':strategy} for m in scope['methods']}
        exercise=fixture(scope,strategy,calibration,specs)
        value=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(runtime=Path(runtime),
            tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
        checks.extend(value['checks'])
    good=[c for c in checks if c['status']=='PASS'];bad=[c for c in checks if c['status']=='EXPECTED_FAILURE']
    assert len(good)==24 and len(bad)==4
    assert sum(c['actual_tensor_audit']['actual_final_latents_reloaded'] for c in good)==64
    paired=[c for c in good if not c['CPU_original_control']]
    assert sum(len(c['actual_direct_numerical_comparisons']) for c in paired)==32
    assert sum(c['actual_CPU_storage_roundtrips'] for c in good)==112
    assert sum(c['actual_CPU_storage_roundtrips'] for c in bad)==48
    assert not torch.cuda.is_initialized()
    return {'checks':checks,'successful_complete_CPU_paths':64,'writer_failure_attempted_CPU_paths':12,
        'actual_complete_CPU_solver_updates':2736,'actual_normal_CPU_CFG_calls':5472,
        'actual_guided_reloaded':2304,'actual_final_latents_reloaded':64,'actual_all_tensors_reloaded':2368,
        'actual_direct_guided36_and_final_comparisons':1184,'actual_CPU_storage_roundtrips':160,
        'path_semantic_mutation_refusals':144,'actual_truncation_refusals':24,
        'registered_GPU_scientific_scope':blocks.validate_scope(scope),
        'existing_full128_algorithm_matrix_not_rerun':True,'small_affected_scope_not_real_GPU_model_lifetime':True,
        'actual_original_and_CPU_persistence_pairing_passed':True,'GPU_submissions':0}
