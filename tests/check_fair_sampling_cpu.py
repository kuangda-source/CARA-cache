"""Pinned Native and complete sampler CPU controls; no weights or GPU evidence."""
import ast
import copy
import importlib.util
from pathlib import Path
import tempfile
import types

import torch

from wcomr.fair_sampling import native_forward, run_fair_request
from wcomr.fair_workpoints import FAIR_WORKPOINTS, Workpoint, validate_workpoints
from wcomr.h0_mode import establish_shared_eval
from wcomr.light_sampling import Hooks
from wcomr.mid_coverage import tree_digest
from wcomr.prepared_input import RNGState, input_signatures
from wcomr.stage_refresh_policy import StageRefreshPolicy


NATIVE_SOURCES = {
    'cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py': '2d3ddcf94158c61223bc610f31ede475f7e4e27cc3b604ff3557b73d891e665f',
    'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py': 'a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071',
}


def native_toy_class(runtime, original, namespace):
    """Unchanged two official forward bodies; only class constructors are omitted."""
    for (relative,digest),name in zip(reversed(list(NATIVE_SOURCES.items())),('MiniTrainDIT','MinimalV1LVGDiT')):
        import hashlib
        path=runtime/relative
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
        tree=ast.parse(path.read_text())
        cls=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name==name)
        forward=copy.deepcopy(next(f for f in cls.body if isinstance(f,ast.FunctionDef) and f.name=='forward'))
        base='ToyNet' if name=='MiniTrainDIT' else 'MiniTrainDIT'
        new=ast.ClassDef(name=name,bases=[ast.Name(id=base,ctx=ast.Load())],keywords=[],body=[forward],decorator_list=[])
        module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),new],type_ignores=[])
        namespace['ToyNet']=original
        namespace['__name__']='cosmos_predict2._src.predict2.networks.'+path.stem
        exec(compile(ast.fix_missing_locations(module),str(path),'exec'),namespace)
    return namespace['MinimalV1LVGDiT']


def exercise(*, inference, samples, wc, settings, inference_module, mode_setup, kernel, flow, runtime,
             extra_exercise=None):
    model,net=inference.pipe.model,inference.pipe.model.net
    cls=type(net);prepare=net.prepare_embedded_sequence
    conditioner=model.conditioner.get_condition_with_negative_prompt
    block_forwards=[b.forward for b in net.blocks]
    sample_cls=type(samples[0]);sentinel=object()
    old_copy=vars(sample_cls).get('model_copy',sentinel)
    def model_copy(self,*,update):
        value=copy.copy(self)
        for k,v in update.items():setattr(value,k,v)
        return value
    sample_cls.model_copy=model_copy
    net.__class__=native_toy_class(runtime,cls,dict(vars(wc)))
    net.timestep_scale=.001
    # Explicit CPU patch embedding stand-in: discard the synthetic mask channel,
    # preserve the 2048-feature Toy geometry, and never force a WC threshold.
    net.prepare_embedded_sequence=lambda x,**kwargs:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    for b,original in zip(net.blocks,block_forwards):
        def block_forward(x,*args,_original=original,**kwargs):
            if args:
                assert len(args)==2
                kwargs.update(emb_B_T_D=args[0],crossattn_emb=args[1])
            return _original(x,**kwargs)
        b.forward=block_forward
    def conditions(batch):
        values=conditioner(batch)
        for value in values:
            original=value.to_dict
            def to_dict(_original=original,**kwargs):
                data=_original(**kwargs)
                data['condition_video_input_mask_B_C_T_H_W']=torch.zeros(1,1,2,8,8)
                return data
            value.to_dict=to_dict
        return values
    model.conditioner.get_condition_with_negative_prompt=conditions
    mode=establish_shared_eval(net)
    common_settings={**settings,'worldcache_rel_l1_thresh':.06}
    policy=StageRefreshPolicy((1,3),every=1,first_solver_step=23,last_solver_step=27)
    originals=(net.forward,inference.pipe.worldcache_enabled,model.decode,inference_module.save_img_or_video,
               model.sample_scheduler.set_timesteps)
    initial_hooks=(len(net._forward_hooks),len(net._forward_pre_hooks))
    checks=[]
    try:
        contexts=('CPU_FAIR:'+samples[0].name,'toy_model','cond:'+samples[0].name)
        entry=RNGState()
        refs=[];observations=[];active=[None]
        hooks=Hooks()
        def prepared(value):
            row={'prepared':input_signatures((),value),'inputs':[],'outputs':[]}
            observations.append(row);active[0]=row
        hooks.wrap(inference.pipe,'_get_data_batch_input',after=prepared)
        pre=net.register_forward_pre_hook(lambda module,args,kwargs:active[0]['inputs'].append(input_signatures(args,kwargs)),with_kwargs=True)
        post=net.register_forward_hook(lambda module,args,kwargs,value:active[0]['outputs'].append(tree_digest(value)),with_kwargs=True)
        hooks.wrap(model,'decode',before=lambda a,k:active[0].update(decode_input=tree_digest(a[0])),
                   after=lambda v:active[0].update(decode_output=tree_digest(v)))
        try:
            with tempfile.TemporaryDirectory(prefix='fair-native-reference-cpu-') as directory:
                for point in FAIR_WORKPOINTS[:2]:
                    entry.restore()
                    for b in net.buffers():b.zero_()
                    wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in common_settings.items()})
                    net.forward=native_forward(net);net.worldcache_enabled=False
                    inference.pipe.worldcache_enabled=False
                    paths=inference.generate([samples[0].model_copy(update={'num_steps':point.requested_steps})],output_dir=Path(directory)/point.name)
                    refs.append({'observation':copy.deepcopy(observations[-1]),'raw_mock_artifact':Path(paths[0]).read_bytes(),
                                 'actual_updates':len(model.sample_scheduler.timesteps),'rng':RNGState().signatures()})
            # Restore the same entry handles as a real caller before composition.
            net.forward=originals[0];inference.pipe.worldcache_enabled=originals[1]
            for b in net.buffers():b.zero_()
            entry.restore();start=len(observations);state={}
            with tempfile.TemporaryDirectory(prefix='fair-workpoints-cpu-') as directory:
                run_fair_request(inference,samples[0],wc,common_settings,FAIR_WORKPOINTS,policy,
                    state=state,save=lambda:None,output=Path(directory),inference_module=inference_module,
                    context=contexts,mode_setup=mode,fallback=(2,),kernel=kernel,expected_video=(93,16,16))
                phases=state['phases']
                assert len(phases)==6 and state['planned_outputs']==6
                assert [p['solver_steps'] for p in phases]==[36,24,36,36,36,36]
                assert [p['CFG_calls'] for p in phases]==[72,48,72,72,72,72]
                assert all(p['prepare_calls']==1 and p['status'].startswith('COMPLETE_FULL93') for p in phases)
                assert all(p['sampling']['worldcache_horizon'] is None for p in phases[:2])
                assert all(p['block_counts']['full_calls']==p['CFG_calls'] for p in phases[:2])
                assert all(p['sampling']['worldcache_horizon']==70 for p in phases[2:])
                actual=observations[start:]
                assert len(actual)==6
                assert all(v['prepared']==actual[0]['prepared'] for v in actual)
                assert all(v['inputs'][0]==actual[0]['inputs'][0] for v in actual)
                for i,ref in enumerate(refs):
                    assert ref['observation']==actual[i] # Full tensors, not saturated mock pixels only.
                    assert ref['rng']==phases[i]['rng_after']
                    point=FAIR_WORKPOINTS[i]
                    path=Path(directory)/(str(i).zfill(3)+'_'+point.name)/(samples[0].name+'.mp4')
                    assert path.read_bytes()==ref['raw_mock_artifact']
                bridge=phases[3]['artifacts'][0]['sha256']
                checks.append({'flow':flow,'case':'six_workpoints_and_direct_native_reference',
                    'solver_updates':[p['solver_steps'] for p in phases],'CFG_calls':[p['CFG_calls'] for p in phases],
                    'direct_native35_and23_all_prepared_inputs_forward_tensors_final_latents_decode_RNG_mock_artifact_equal':True,
                    'all_six_same_prepared_and_initial_net_input':True,
                    'Native_uses_original_class_body_all_deep_not_WC_forced_full':True,
                    'thresholds_retained':[p['workpoint']['threshold'] for p in phases[2:]],
                    'CPU_sparse_calls':[e['call'] for e in phases[-1]['refresh_provenance']['events'] if e['sparse_layers']],
                    'real_kernel_or_video':False})
        finally:
            pre.remove();post.remove();hooks.close()
        scenarios=['bridge_mismatch'] if not flow else ['bridge_mismatch','native23_writer_failure','native23_wrong_grid']
        for scenario in scenarios:
            state={};n=[0]
            hooks=Hooks()
            def prepared_counter(v):n[0]+=1
            hooks.wrap(inference.pipe,'_get_data_batch_input',after=prepared_counter)
            if scenario=='native23_writer_failure':
                original=inference_module.save_img_or_video
                inference_module.save_img_or_video=lambda *a,**k:None if n[0]==2 else original(*a,**k)
            if scenario=='native23_wrong_grid':
                original_grid=model.sample_scheduler.set_timesteps
                model.sample_scheduler.set_timesteps=lambda count,*a,**k:original_grid(35 if count==23 else count,*a,**k)
            error=None
            before_settings={name:getattr(net,name) for name in set(common_settings)|{'worldcache_enabled'}}
            try:
                with tempfile.TemporaryDirectory(prefix='fair-negative-cpu-') as directory:
                    try:
                        run_fair_request(inference,samples[0],wc,common_settings,FAIR_WORKPOINTS,policy,
                            state=state,save=lambda:None,output=Path(directory),inference_module=inference_module,
                            context=contexts,mode_setup=mode,fallback=(2,),kernel=kernel,expected_video=(93,16,16),
                            expected_WC_sha256='0'*64 if scenario=='bridge_mismatch' else bridge)
                    except ValueError as exc:error=str(exc)
                    assert error and state['status']=='TECH_BLOCKED_FAIR_SIX_WORKPOINT_DENOMINATOR_PRESERVED'
                    assert state['planned_outputs']==6 and state['phases'][0]['status'].startswith('COMPLETE_FULL93')
                    assert len(state['phases'])==(4 if scenario=='bridge_mismatch' else 2)
                    assert state['phases'][-1]['status']=='TECH_BLOCKED'
                    checks.append({'flow':flow,'case':scenario,'error':error,
                                   'six_output_denominator_and_prior_output_preserved':True})
            finally:
                hooks.close();inference_module.save_img_or_video=originals[3]
                model.sample_scheduler.set_timesteps=originals[4]
            assert net.forward==originals[0] and inference.pipe.worldcache_enabled==originals[1]
            assert before_settings=={name:getattr(net,name) for name in before_settings}
            assert (len(net._forward_hooks),len(net._forward_pre_hooks))==initial_hooks
            assert not hasattr(net,'_wc_refresh_adapter')
            assert all(float(v)==0 for v in net.buffers())
        invalid=(FAIR_WORKPOINTS[:-1],list(FAIR_WORKPOINTS),
                 tuple(Workpoint(p.name,p.mode,True,p.threshold) if i==0 else p for i,p in enumerate(FAIR_WORKPOINTS)),
                 tuple(Workpoint(p.name,p.mode,p.requested_steps,.05) if i==2 else p for i,p in enumerate(FAIR_WORKPOINTS)))
        for points in invalid:
            try:validate_workpoints(points)
            except ValueError:pass
            else:raise AssertionError('Incorrect fair allocation accepted')
        checks.append({'flow':flow,'case':'four_invalid_workpoint_allocations_refused'})
        if extra_exercise is not None:
            checks.extend(extra_exercise(inference=inference,samples=samples,wc=wc,
                settings=common_settings,inference_module=inference_module,mode_setup=mode,
                kernel=kernel,flow=flow))
        return checks
    finally:
        net.__class__=cls;net.prepare_embedded_sequence=prepare
        if hasattr(net,'timestep_scale'):delattr(net,'timestep_scale')
        for b,original in zip(net.blocks,block_forwards):b.forward=original
        model.conditioner.get_condition_with_negative_prompt=conditioner
        if old_copy is sentinel:delattr(sample_cls,'model_copy')
        else:sample_cls.model_copy=old_copy
        net.forward=originals[0];inference.pipe.worldcache_enabled=originals[1]


def run(runtime):
    runtime=Path(runtime)
    spec=importlib.util.spec_from_file_location('fair_official_sampler_fixture',Path(__file__).with_name('check_full_sampling.py'))
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    r=fixture.run(runtime,exercise=lambda **kwargs:exercise(runtime=runtime,**kwargs))
    r['status']='SIX_FAIR_WORKPOINT_PINNED_NATIVE35_23_AND_SAMPLER_CPU_PASS_NOT_GPU_PARITY'
    r['upstream_sha256'].update(NATIVE_SOURCES)
    r['limits']+=' Unchanged two Native forward bodies with Toy constructors/CPU mask and patch embedding/positional Toy block adapters. Native all-deep and direct CPU reference equality are not real weights, GPU parity, encoded video quality or speed.'
    return r
