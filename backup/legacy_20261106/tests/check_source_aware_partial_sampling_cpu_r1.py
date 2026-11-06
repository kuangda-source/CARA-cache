"""New complete dynamic full sampler scope; explicit Toy weights/attention only."""
import ast
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import source_aware_partial_sampling as dynamic
from wcomr.source_aware_cpd_control import Costs,PartialPrior
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.partial_mlp_deployment_state import plain


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m


BODY=r'''    results=[]
    try:
        for scenario in ('complete','last_parent_writer_failure'):
            output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario
            output.mkdir(parents=True,exist_ok=False)
            state={};error=None
            def save():
                p=output/'receipt.json';tmp=p.with_suffix('.tmp')
                tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(p)
            def writer(path,values):
                if scenario=='last_parent_writer_failure' and path.name=='AV51_CPU_DENSE_CONTROL.pt':
                    raise ValueError('Injected final full-parent vector writer failure')
                return vector_file(path,values)
            try:
                run_batch(inference,selected,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,contexts=contexts,mode_setup=mode,
                    runtime=runtime,config=config,rf_module=rf,writer=writer)
            except BaseException as exc:error=str(exc)
            assert state['planned_parent_paths']==32 and len(state['requests'])==4,(error,state.get('status'))
            assert state['initial_state_restored'] and all(float(b)==0 for b in net.buffers())
            assert not any(m.training for m in net.modules())
            assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
            if scenario=='complete':
                assert error is None,error
                verdict=verify_batch(state);raw=audit_vectors(state,output,tensor_loader,config['expected_shape'])
                assert (raw['actual_guided_reloaded'],raw['actual_latents_reloaded'])==(1152,32)
                assert (raw['full_GEMM_partial_trajectory_references'],raw['original_RA_trajectory_references'],raw['A_OFF_trajectory_references'])==(4,4,4)
                P_reuses=consecutive_P=actual_P=actual_A_heads=source_RA_comparisons=0
                for request in state['requests']:
                    for row in request['paths']:
                        assert all(v['finite'] and v['nonzero_elements']==0 for v in row['actual_condition_masks'])
                        assert all(r['checkpoint_perturbation_executed'] for r in row['P0_roundtrips'])
                        assert row['condition_fields_before']==row['condition_fields_after']
                        assert row['actual_raw_solver_configuration']['raw_values']
                        c=row['collection_complete'];d=c.get('deployment')
                        for step in range(1,37):
                            entries=[v for v in c['Linear_inputs'] if v['step']==step]
                            action=row['actions'][step-1]
                            if action=='CC':assert not entries
                            else:
                                active=256 if action=='PP' and row['collect']!='REF_CPD' else 512
                                assert len(entries)==16 and all(v['rows']==active for v in entries)
                        if not d:continue
                        actual_A_heads+=d['A_readout']['extra_candidate_heads']
                        if row['collect']=='DYNAMIC_NO_P':
                            source=request['paths'][0]['collection_complete']['source_RA_history']
                            for a,b in zip(source,d['source_policy_history']):
                                assert a['step']==b['step'] and a['action']==b['action']*2
                                assert a['anchor_before']==b['state_before'][0]
                                assert a['accumulated_before']==b['state_before'][4]
                                source_RA_comparisons+=1
                        for h in d['history']:
                            p=h['source_policy']
                            if h['action']=='CC' and all(v['kind']=='P' for v in h['working_sources']):
                                P_reuses+=1;assert p['creation_floor_proxy_after']>0
                            if h['action']=='PP':
                                actual_P+=1;assert p['creation_floor_proxy_after']>0
                                if h['step']>1 and d['history'][h['step']-2]['action']=='PP':consecutive_P+=1
                        assert d['history'][34]['native_cycle_reset'] and d['history'][35]['true_D_after']==[[36],[36]]
                assert source_RA_comparisons==144 and actual_P>0 and P_reuses>0 and consecutive_P>0
                assert actual_A_heads>0
                refused=[]
                for fault in ('missing_method','P_zero_floor','P_dense_anchor','P_interval_reset',
                              'A_head_cost_missing','A_wrong_strength','missing_roundtrip','wrong_Linear_rows'):
                    bad=copy.deepcopy(state);row=bad['requests'][-1]['paths'][2]
                    h=next(h for h in row['collection_complete']['deployment']['history'] if h['action']=='PP')
                    if fault=='missing_method':bad['requests'][-1]['paths'].pop()
                    elif fault=='P_zero_floor':h['source_policy']['creation_floor_proxy_after']=0
                    elif fault=='P_dense_anchor':h['source_policy']['dense_anchor_after']=h['step']
                    elif fault=='P_interval_reset':
                        h['source_policy']['accumulated_interval_proxy_after']=-1
                    elif fault=='missing_roundtrip':row['P0_roundtrips'].pop()
                    elif fault=='wrong_Linear_rows':
                        next(v for v in row['collection_complete']['Linear_inputs'] if v['step']==h['step'])['rows']+=1
                    else:
                        row=bad['requests'][-1]['paths'][5]
                        if fault=='A_head_cost_missing':row['collection_complete']['actual_original_plus_candidate_heads'].pop()
                        else:
                            next(h for h in row['collection_complete']['deployment']['history'] if h['action']=='CC')['A_readout']['shared_alpha']=99
                    try:verify_batch(bad)
                    except ValueError:refused.append(fault)
                    else:raise AssertionError('Invalid dynamic scope accepted: '+fault)
                p=Path(raw['files'][-1]['path']);old=p.read_bytes()
                try:
                    p.write_bytes(old[:-1])
                    try:audit_vectors(state,output,tensor_loader,config['expected_shape'])
                    except ValueError as exc:assert 'truncated' in str(exc)
                    else:raise AssertionError('Truncated dynamic vector accepted')
                finally:p.write_bytes(old)
                results.append({'flow':flow,'scenario':scenario,'status':'PASS','receipt':state,
                    'verdict':verdict,'actual_tensor_audit':raw,'actual_P_pairs':actual_P,
                    'P_source_C_pairs':P_reuses,'consecutive_P_pairs':consecutive_P,
                    'actual_A_extra_heads':actual_A_heads,'original_RA_policy_comparisons':source_RA_comparisons,
                    'mutation_refusals':refused,'actual_artifact_truncation_refused':True,
                    'fixture_compiler_proof':FIXTURE_PROOF,'synthetic_policy_specs':plain(policy_specs)})
            else:
                assert error=='Injected final full-parent vector writer failure',error
                row=state['requests'][-1]['paths'][-1]
                assert row['status']=='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED' and len(row['guided_sha256'])==36
                assert len(list(output.rglob('*.pt')))==31 and len(list(output.rglob('*.mp4')))==32
                results.append({'flow':flow,'scenario':scenario,'status':'EXPECTED_FAILURE','receipt':state,
                    'complete_scope_retained':True,'initial_full_state_restored':True,
                    'installed_MLP_methods_restored':True,'error':error})
        return results
'''


def fixture(calibration,policy_specs):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n')
    end=source.index('    finally:\n        inference.pipe._get_data_batch_input=original_prepare',start)
    old=source[start:end];changed=source[:start]+BODY+source[end:]
    before,after="'A_P0_FULL_SAMPLER_CPU'","'SOURCE_AWARE_FULL_SAMPLER_CPU'"
    assert changed.count(before)==1;changed=changed.replace(before,after)
    inverse=changed.replace(after,before).replace(BODY,old)
    assert inverse==source and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(source))
    proof={'inverse_AST_equal':True,'explicit_fixture_sites':2,
        'original_fixture_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'ordinary_Toy_prepare_conditions_Block_cleanup_unchanged':True}
    def bound_run(*args,**kwargs):
        return dynamic.run_batch(*args,calibration=calibration,policy_specs=policy_specs,**kwargs)
    ns={**original.exercise.__globals__,'run_batch':bound_run,'verify_batch':dynamic.verify_batch,
        'audit_vectors':dynamic.audit_vectors,'METHODS':dynamic.METHODS,'FIXTURE_PROOF':proof,
        'policy_specs':policy_specs,'plain':plain}
    exec(compile(changed,__file__+'#dynamic-CPU-fixture','exec'),ns)
    return ns['exercise']


def run(runtime,tensor_loader,artifact_root):
    calibration=Calibration('SYNTHETIC_SOURCE_AWARE_FULL36_RA_PRIOR',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},{s:1. for s in range(1,37)})
    base={'threshold':.07,'costs':Costs('SYNTHETIC_REFERENCE_RA_FULL_PAIR',1.,4.),'partial_prior':None}
    p={'threshold':2.,'costs':Costs('SYNTHETIC_CPD_FULL_PAIR',3.,4.,1.),
       'partial_prior':PartialPrior('SYNTHETIC_CPD_SAME_UNIT_FLOOR',.005,.3)}
    dense={'threshold':2.,'costs':Costs('SYNTHETIC_ACTUAL_D_CHEAPEST',4.,1.),'partial_prior':None}
    specs={m:dict(base if m in ('SOURCE_RA','DYNAMIC_NO_P') else dense if m=='DENSE_CONTROL' else p) for m in dynamic.METHODS}
    exercise=fixture(calibration,specs)
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:exercise(runtime=Path(runtime),
        tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert not torch.cuda.is_initialized()
    return result
