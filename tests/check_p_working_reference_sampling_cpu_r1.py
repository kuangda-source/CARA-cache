"""Both-flow full UniPC P-reference integration with explicit Toy boundaries."""
import copy
import hashlib
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import partial_mlp_deployment_sampling as p0
from wcomr.partial_mlp_guided_sampling import GuidedSamplingOwner
from wcomr.p_working_reference_readout_r1 import WorkingReferenceSamplingOwner, VERSION
from wcomr.early_head_elision_sampling_r4 import native_checkpoint_head
from wcomr.partial_mlp_deployment_state import plain
from wcomr.mid_coverage import tree_digest

METHODS = ('OFF', 'D_REFERENCE_W1_ONE_PHASE', 'P_REFERENCE_W1_ONE_PHASE',
           'D_REFERENCE_BETA1_ONE_PHASE', 'P_REFERENCE_BETA1_ONE_PHASE')


def verify(state):
    assert state['planned_parent_paths'] == 5 and len(state['requests']) == 1
    req = state['requests'][0]
    assert tuple(r['collect'] for r in req['paths']) == METHODS
    assert len(req['prepared_input_calls']) == 5
    assert all(x['prepared'] == req['prepared_input_calls'][0]['prepared'] for x in req['prepared_input_calls'])
    for row in req['paths']:
        c = row['collection_complete']; d = c['deployment']; a = d['A_readout']
        assert row['status'] == 'COMPLETE_PARENT_PATH'
        assert len(row['guided_sha256']) == len(row['solver_returns']) == len(d['history']) == 36
        assert row['condition_fields_before'] == row['condition_fields_after']
        assert row['conditions_before'] == row['conditions_after']
        assert row['all_modules_eval'] and row['parameter_versions_unchanged']
        assert len(row['P0_roundtrips']) == 4
        assert all(x['physical_state_restored'] and x['complete_additional_state_restored']
                   and x['checkpoint_perturbation_executed'] for x in row['P0_roundtrips'])
        assert a['teacher_calls'] == a['extra_candidate_deep_blocks'] == 0
        assert len(c['actual_original_plus_candidate_heads']) == 72+a['extra_candidate_heads']
        assert row['own_history'] == d['history']
        for h in d['history']:
            if h['action'] != 'DD': assert h['true_D_before'] == h['true_D_after']
            if h['action'] == 'PP':
                assert not h['A_readout']['extra_heads']
                assert all(not s['RA_zero_risk_reset_allowed'] and s['creation_error'] == 'UNKNOWN_NOT_ZERO'
                           for s in h['working_sources'])
        if row['collect'].startswith('P_REFERENCE'):
            assert a['P_reference_version'] == VERSION and a['P_reference_successful_branch_reads'] > 0
            for h in a['history']:
                for p in h['P_reference']:
                    if p is not None:
                        assert p['true_D_full_state_before_sha256'] == p['true_D_full_state_after_sha256']
                        assert p['working_age'] > 0 and max(p['true_D_steps']) < p['working_created_step']
    return {'paths':5, 'updates':180, 'CFG_calls':360, 'full_restores':20}


def batch_for(observations):
    parent = dedent(inspect.getsource(p0.parent.run_batch))
    changed = parent.replace('len(samples) != 4 or len(contexts) != 4',
                            'len(samples) != 1 or len(contexts) != 1')
    assert changed != parent and changed.replace('len(samples) != 1 or len(contexts) != 1',
                                                'len(samples) != 4 or len(contexts) != 4') == parent
    def owner(model, method, context, runtime, wc, rf):
        mode = 'OFF' if method == 'OFF' else method.split('_REFERENCE_', 1)[1]
        cls = WorkingReferenceSamplingOwner if method.startswith('P_REFERENCE') else GuidedSamplingOwner
        o = cls(model, method='A_P0_'+mode, context=context, runtime=runtime, wc=wc, rf=rf)
        readout = o.deployment.readout
        original = readout.semantic_hidden
        pending = []
        def watch_head(module, values):
            if pending:
                assert torch.equal(values[0], pending.pop(0)), 'Wrong prewarp source or candidate warp'
        o.hooks.append(o.net.final_layer.register_forward_pre_hook(watch_head))
        def observe(net, skipped, branch, ori, probe, hidden, kw, emb, adaln):
            d = o.deployment
            full_D = tree_digest(plain([vars(c) for c in d.dense]))
            cache = tree_digest((net.probe_residual_cache, net.residual_cache))
            rng = tree_digest(torch.get_rng_state())
            expected = None
            if (method.startswith('P_REFERENCE') and d.current['action'] == 'C'
                    and d.working[branch]['kind'] == 'P'):
                c = d.dense[branch]
                beta = (1. if mode.startswith('BETA1') else
                        max(-c.clip, min(c.clip, c.numerator/(c.denominator+c.ridge))))
                # Independently reconstruct from the live physical P caches.
                residual = net.residual_cache[branch] + beta*((probe-ori)-net.probe_residual_cache[branch])
                expected = d.warp(net, ori+residual, net.residual_cache[branch], ori.shape[1])
                pending.append(expected.detach().clone())
            original(net, skipped, branch, ori, probe, hidden, kw, emb, adaln)
            assert not pending, 'Candidate failed to enter the actual native head'
            if d.current['action'] == 'C':
                assert tree_digest(plain([vars(c) for c in d.dense])) == full_D
                assert tree_digest((net.probe_residual_cache, net.residual_cache)) == cache
                assert tree_digest(torch.get_rng_state()) == rng
            observations.append({'method':method, 'step':d.current['step'], 'slot':branch,
                'action':d.current['action'], 'source_kind':d.working[branch]['kind'] if d.working[branch] else None,
                'independent_actual_P_formula_and_head_checked':expected is not None})
        readout.semantic_hidden = observe
        return o
    source = dedent(inspect.getsource(p0._derive))
    old = 'source = dedent(inspect.getsource(parent.run_batch))'; new = 'source = _p_reference_parent()'
    count = 'planned_parent_paths=52,planned_origins=0'; new_count = 'planned_parent_paths=5,planned_origins=0'
    assert source.count(old) == source.count(count) == 1
    edited = source.replace(old,new).replace(count,new_count)
    assert edited.replace(new,old).replace(new_count,count) == source
    ns = {**p0._derive.__globals__, '_p_reference_parent':lambda:changed,
          'METHODS':METHODS, '_owner':owner, 'verify_batch':verify, '__file__':__file__}
    exec(compile(edited,__file__+'#registered-five-method-scope','exec'),ns)
    batch, proof = ns['_derive']()
    return batch, {**proof, 'scope_only_inverse_bytes_equal':True}


BODY = r'''    results=[]
    try:
        selected=[type(samples[0])('P_REFERENCE_CPU')]
        local={**config,'sample_names':['P_REFERENCE_CPU'],'run_id':'P_REFERENCE_CPU'}
        contexts=[(local['run_id'],'Toy_actual_modules','same_actual_condition')]
        output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')
        output.mkdir(parents=True,exist_ok=False);state={};observations=[]
        def save():
            (output/'receipt.json').write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')
        batch,proof=batch_for(observations)
        batch(inference,selected,wc,settings,state=state,save=save,output=output,
              inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,
              config=local,rf_module=rf)
        verdict=verify(state);loaded={};files=[]
        for row in state['requests'][0]['paths']:
            art=row['vector_artifact'];path=Path(art['path'])
            assert path.resolve().is_relative_to(output.resolve())
            assert hashlib.sha256(path.read_bytes()).hexdigest()==art['sha256']
            value=tensor_loader(path,map_location='cpu',weights_only=True)
            assert len(value['guided'])==36 and {k:tree_digest(v) for k,v in value.items()}==art['tensor_sha256']
            assert all(t.dtype==torch.float32 and list(t.shape)==local['expected_shape'] and torch.isfinite(t).all()
                       for t in value['guided']+[value['final_latent']])
            loaded[row['collect']]=value;files.append({'path':str(path),'sha256':art['sha256']})
        comparisons=[]
        for mode in ('W1_ONE_PHASE','BETA1_ONE_PHASE'):
            old,new=[loaded[v+'_REFERENCE_'+mode] for v in ('D','P')]
            assert all(torch.equal(x,y) for x,y in zip(old['guided'][:10],new['guided'][:10]))
            assert any(not torch.equal(x,y) for x,y in zip(old['guided'][10:],new['guided'][10:]))
            checks=[x for x in observations if x['method']=='P_REFERENCE_'+mode
                    and x['independent_actual_P_formula_and_head_checked']]
            assert checks and {x['slot'] for x in checks}=={0,1}
            comparisons.append({'mode':mode,'first_ten_updates_equal':True,
                                'P_readout_changes_real_later_solver_outputs':True,
                                'actual_P_formula_and_native_head_checks':len(checks)})
        assert len(observations)==360 and state['initial_state_restored']
        assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
        results.append({'flow':flow,'status':'PASS','receipt':state,'verdict':verdict,
            'observations':observations,'comparisons':comparisons,'files':files,'compiler_proof':proof})
        return results
'''


def run(runtime, tensor_loader, artifact_root):
    from check_partial_mlp_guided_sampling_cpu_r1 import exercise
    from check_full_sampling import run as full
    source = dedent(inspect.getsource(exercise)); start = source.index('    results=[]\n')
    end = source.index('    finally:\n        inference.pipe._get_data_batch_input=original_prepare', start)
    old_head = 'net.final_layer=DeclaredIdentityHead().eval()'
    new_head = 'net.final_layer=_native_head(runtime,8,1,1,8,use_adaln_lora=True,adaln_lora_dim=4,use_wan_fp32_strategy=True).eval()'
    old_emb = 'net.t_embedder=lambda t:((t.float()/1000).unsqueeze(-1).expand(*t.shape,8),None)'
    new_emb = 'net.t_embedder=lambda t:((t.float()/1000).unsqueeze(-1).expand(*t.shape,8),.02*torch.ones(*t.shape,24))'
    assert source.count(old_head) == source.count(old_emb) == 1
    changed = (source[:start]+BODY+source[end:]).replace(old_head,new_head).replace(old_emb,new_emb)
    assert changed.replace(BODY,source[start:end]).replace(new_head,old_head).replace(new_emb,old_emb) == source
    ns = {**exercise.__globals__, '_native_head':native_checkpoint_head, 'batch_for':batch_for,
          'verify':verify,'hashlib':hashlib,'tree_digest':tree_digest}
    exec(compile(changed,__file__+'#registered-body-and-native-head','exec'),ns)
    result = full(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),
        tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert len(result['checks']) == 2
    return {'status':'P_WORKING_REFERENCE_FULL_UNIPC_TWO_FLOW_CPU_PASS_NOT_GPU',
        'complete_paths':10,'updates':360,'CFG_calls':720,'written_tensors':370,'written_files':10,
        'full_physical_and_owned_restores':40,'checks':result['checks'],
        'explicit_Toy_boundaries':result['limits'],'native_checkpoint_head_used':True,
        'refresh_selection_changed':False,'GPU_submissions':0}
