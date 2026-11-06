"""Affected E5 full UniPC CPU: fixed C/P/D and current-birth controllers.

One declared Toy request per family, three A modes, both versions and flows.
Real native head AdaLN/Wan flags, ordinary guarded sampler and complete owned
checkpoints run; Toy weights/attention/prepare/unpatchify/decode/writer remain.
"""
import ast
import copy
import inspect
import json
from pathlib import Path
import sys
from textwrap import dedent

import torch

from wcomr import partial_mlp_deployment_sampling as p0
from wcomr.partial_mlp_guided_sampling import GuidedSamplingOwner
from wcomr.source_aware_CPU_storage_sampling_r1 import CPUStorageSamplingOwner
from wcomr.early_head_elision_sampling_r2 import (FixedEarlyHeadSamplingOwner,
    CurrentBirthEarlyHeadSamplingOwner,prototype,VERSION,DERIVATION_PROOFS,native_checkpoint_head)
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.mid_coverage import tree_digest

MODES=('OFF','W1_ONE_PHASE','BETA1_ONE_PHASE')
METHODS=tuple(v+'_'+a for a in MODES for v in ('LEGACY','FAST'))


def verify(state):
    if state['planned_parent_paths']!=6 or len(state['requests'])!=1:
        raise ValueError('Whole declared six-path family required')
    req=state['requests'][0];rows=req['paths']
    if tuple(x['collect'] for x in rows)!=METHODS or len(req['prepared_input_calls'])!=6:
        raise ValueError('All three A versions and actual input replay records required')
    for row in rows:
        d=row['collection_complete']['deployment'];a=d['A_readout'];c=row['collection_complete']
        if (row['status']!='COMPLETE_PARENT_PATH' or len(row['guided_sha256'])!=36
                or len(row['solver_returns'])!=36 or len(a['history'])!=36
                or len(row['P0_roundtrips'])!=4 or len(row['checkpoints'])!=4
                or row['conditions_before']!=row['conditions_after']
                or row['condition_fields_before']!=row['condition_fields_after']
                or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                or a['teacher_calls'] or a['extra_candidate_deep_blocks']
                or len(c['actual_original_plus_candidate_heads'])!=72+a['extra_candidate_heads']
                or row['own_history']!=d['history']
                or not all(x['physical_state_restored'] and x['complete_additional_state_restored']
                           and x['checkpoint_perturbation_executed'] for x in row['P0_roundtrips'])):
            raise ValueError('Incomplete E5 full sampler/head/owned-state contract')
        if row['collect'].startswith('FAST_'):
            if not a['candidate_original_head_elision_implemented'] or a['native_head_contract']!={
                'use_adaln_lora':True,'use_wan_fp32_strategy':True,'unpatchify':'DECLARED_CPU_TEST_BOUNDARY','checkpoint_wrapper':'PINNED_NATIVE_NON_REENTRANT_SELECTIVE'}:
                raise ValueError('Actual native head mode or new owner missing')
            if len(c['actual_original_plus_candidate_heads'])!=a['total_head_calls']:
                raise ValueError('Paid head source records differ from full A accounting')
            if row['collect']!='FAST_OFF' and not any(any(h['original_head_elided']) for h in a['history']):
                raise ValueError('Registered full sampler failed to exercise head elision')
        for h in d['history']:
            if h['action']!='DD' and h['true_D_before']!=h['true_D_after']:
                raise ValueError('C/P changed actual D calibration')
            if h['action']=='PP' and (h['A_readout']['extra_heads'] or
                                     any(v['RA_zero_risk_reset_allowed'] for v in h['working_sources'])):
                raise ValueError('P became a true D or executed a candidate readout')
    return {'complete_paths':6,'complete_UniPC_updates':216,'actual_CFG_calls':432,
            'complete_owned_and_physical_restores':24,'new_real_GPU_acceptance':False}


def batch_for(family):
    base_source=dedent(inspect.getsource(p0.parent.run_batch))
    changed=base_source.replace('len(samples) != 4 or len(contexts) != 4',
                                'len(samples) != 1 or len(contexts) != 1')
    assert changed!=base_source and changed.replace('len(samples) != 1 or len(contexts) != 1',
        'len(samples) != 4 or len(contexts) != 4')==base_source
    calibration=Calibration('SYNTHETIC_E5_FULL_SAMPLER_ONLY',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},{s:1. for s in range(1,37)})
    spec={'threshold':2.,'costs':Costs('SYNTHETIC_CHEAP_C_WITH_P',1.,4.,2.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_POSITIVE_P_FLOOR',.005,.3,
            early_creation_floor=.005,late_creation_floor=.02),
        'working_epoch_strategy':'WORKING_P_AGE_KEEP_INTERVAL'}
    def owner(model,method,context,runtime,wc,rf):
        fast=method.startswith('FAST_');a=method.split('_',1)[1]
        if family=='FIXED':
            cls=FixedEarlyHeadSamplingOwner if fast else GuidedSamplingOwner
            return cls(model,method='A_P0_'+a,context=context,runtime=runtime,wc=wc,rf=rf)
        cls=CurrentBirthEarlyHeadSamplingOwner if fast else CPUStorageSamplingOwner
        return cls(model,method='A_CPD_'+a,context=context,runtime=runtime,wc=wc,rf=rf,
                   calibration=calibration,spec=spec)
    source=dedent(inspect.getsource(p0._derive))
    old='source = dedent(inspect.getsource(parent.run_batch))';new='source = _e5_cpu_parent_source()'
    old_count='planned_parent_paths=52,planned_origins=0';new_count='planned_parent_paths=6,planned_origins=0'
    assert source.count(old)==source.count(old_count)==1
    modified=source.replace(old,new).replace(old_count,new_count)
    assert modified.replace(new,old).replace(new_count,old_count)==source
    namespace={**p0._derive.__globals__,'_e5_cpu_parent_source':lambda:changed,
        'METHODS':METHODS,'_owner':owner,'verify_batch':verify,'__file__':__file__}
    exec(compile(modified,__file__+'#registered_scope_only','exec'),namespace)
    batch,proof=namespace['_derive']()
    return batch,{**proof,'CPU_scope_derivation_inverse_bytes_AST_equal':True}


BODY=r'''    results=[]
    model.E5_declared_CPU_unpatchify=True
    try:
        for family in ('FIXED','CURRENT_BIRTH'):
            selected=[type(samples[0])('E5_CPU')]
            local={**config,'sample_names':['E5_CPU'],'run_id':'E5_'+family+'_CPU'}
            contexts=[(local['run_id']+':E5_CPU','Toy_actual_modules','same_actual_condition')]
            output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/family
            output.mkdir(parents=True,exist_ok=False);state={};counts={}
            def save():
                q=output/'receipt.json';q.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')
            code=type(net.final_layer._checkpoint_wrapped_module).forward.__code__
            def profile(frame,event,arg):
                if event=='call' and frame.f_code is code:
                    key=state['requests'][-1]['paths'][-1]['collect']
                    counts[key]=counts.get(key,0)+1
            assert sys.getprofile() is None
            batch,proof=batch_for(family)
            sys.setprofile(profile)
            try:
                batch(inference,selected,wc,settings,state=state,save=save,output=output,
                    inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,
                    config=local,rf_module=rf)
            finally:sys.setprofile(None)
            verdict=verify(state);loaded={};files=[];compares=0
            for row in state['requests'][0]['paths']:
                art=row['vector_artifact'];q=Path(art['path'])
                assert q.resolve().is_relative_to(output.resolve())
                assert hashlib.sha256(q.read_bytes()).hexdigest()==art['sha256']
                x=tensor_loader(q,map_location='cpu',weights_only=True)
                assert len(x['guided'])==36 and {k:tree_digest(v) for k,v in x.items()}==art['tensor_sha256']
                assert all(t.dtype==torch.float32 and list(t.shape)==local['expected_shape'] and torch.isfinite(t).all()
                           for t in x['guided']+[x['final_latent']])
                loaded[row['collect']]=x;files.append({'path':str(q),'sha256':art['sha256']})
                assert counts[row['collect']]==len(row['collection_complete']['actual_original_plus_candidate_heads'])
            changes=[]
            for a in MODES:
                left=loaded['LEGACY_'+a];right=loaded['FAST_'+a]
                assert all(torch.equal(x,y) for x,y in zip(left['guided']+[left['final_latent']],right['guided']+[right['final_latent']]))
                compares+=37
                l,r=[next(x for x in state['requests'][0]['paths'] if x['collect']==v+'_'+a) for v in ('LEGACY','FAST')]
                for key in ('actions','solver_returns','condition_fields_before','condition_fields_after',
                            'actual_raw_solver_configuration','rng_after','final_latent_sha256'):
                    assert l[key]==r[key],key
                lh=l['collection_complete']['deployment']['history'];rh=r['collection_complete']['deployment']['history']
                for x,y in zip(lh,rh):
                    for key in ('true_D_before','true_D_after','working_source_ages','working_sources','actual_projection_records'):
                        assert x[key]==y[key],key
                    if family=='CURRENT_BIRTH':assert x['source_policy']==y['source_policy']
                changes.append({'method':a,'actual_legacy_heads':counts['LEGACY_'+a],'actual_new_heads':counts['FAST_'+a],
                    'saved_native_heads':counts['LEGACY_'+a]-counts['FAST_'+a]})
            assert state['initial_state_restored'] and not any(m.training for m in net.modules())
            assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
            results.append({'flow':flow,'family':family,'status':'PASS','receipt':state,'verdict':verdict,
                'actual_direct_equalities':compares,'head_call_changes':changes,'files':files,'compiler_proof':proof})
        return results
'''


def run(runtime,tensor_loader,artifact_root):
    from check_partial_mlp_guided_sampling_cpu_r1 import exercise
    from check_full_sampling import run as full
    source=dedent(inspect.getsource(exercise));start=source.index('    results=[]\n')
    end=source.index('    finally:\n        inference.pipe._get_data_batch_input=original_prepare',start)
    old_head='net.final_layer=DeclaredIdentityHead().eval()'
    new_head='net.final_layer=_e5_native_head(runtime,8,1,1,8,use_adaln_lora=True,adaln_lora_dim=4,use_wan_fp32_strategy=True).eval()'
    old_emb='net.t_embedder=lambda t:((t.float()/1000).unsqueeze(-1).expand(*t.shape,8),None)'
    new_emb='net.t_embedder=lambda t:((t.float()/1000).unsqueeze(-1).expand(*t.shape,8), .02*torch.ones(*t.shape,24))'
    assert source.count(old_head)==source.count(old_emb)==1
    changed=(source[:start]+BODY+source[end:]).replace(old_head,new_head).replace(old_emb,new_emb)
    assert changed.replace(BODY,source[start:end]).replace(new_head,old_head).replace(new_emb,old_emb)==source
    cleanup='    finally:\n        inference.pipe._get_data_batch_input=original_prepare'
    changed=changed.replace(cleanup,'    finally:\n        vars(model).pop("E5_declared_CPU_unpatchify",None)\n        inference.pipe._get_data_batch_input=original_prepare')
    namespace={**exercise.__globals__,'_e5_native_head':native_checkpoint_head,'batch_for':batch_for,
        'verify':verify,'MODES':MODES,'hashlib':__import__('hashlib'),'tree_digest':tree_digest,'sys':sys}
    exec(compile(changed,__file__+'#affected_head_and_registered_body','exec'),namespace)
    result=full(runtime,exercise=lambda **kw:namespace['exercise'](runtime=Path(runtime),
        tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert len(result['checks'])==4 and sum(c['actual_direct_equalities'] for c in result['checks'])==444
    return {'status':'E5_FULL_UNIPC_NATIVE_HEAD_CPU_PASS_NOT_GPU_ACCEPTANCE','checks':result['checks'],
        'complete_paths':24,'updates':864,'CFG_calls':1728,'direct_equalities':444,
        'full_physical_and_owned_restores':96,'written_tensors':888,'written_files':24,
        'source_derivation_proofs':DERIVATION_PROOFS,'explicit_Toy_boundaries':result['limits'],
        'native_head_AdaLN_and_Wan_flags':True,'ordinary_full_pipeline_used':True,'GPU_submissions':0}
