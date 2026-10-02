#!/usr/bin/env python3
"""Independent r3: shared official preparation, full-state/input parity, shortest prefix."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import statistics
import sys
import time
import traceback


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','runtime','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--gpu-uuid');p.add_argument('--validate-only',action='store_true')
    p.add_argument('--cpu-import-check',action='store_true')
    a=p.parse_args()
    spec=importlib.util.spec_from_file_location('historical_asset_gate',a.stage/'scripts/run_wc_s0_profile.py')
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    # Reuse identity validation only, never execute the historical S0 job.
    old,sampling=base.validate(a.project,a.stage,a.runtime)
    c=json.loads((a.stage/'mid-config.json').read_text())
    gate_spec=importlib.util.spec_from_file_location('mid_gate',a.stage/'src/wcomr/mid_parity_scope.py')
    gate=importlib.util.module_from_spec(gate_spec);gate_spec.loader.exec_module(gate);gate.validate_parity_scope(c)
    if sha(a.runtime/'cosmos_predict2/_src/predict2/inference/video2world.py')!=c['request_lifecycle_source_sha256']:
        raise ValueError('Official request reset source changed')
    for name,digest in c['payload_sha256'].items():
        if sha(a.stage/name)!=digest:raise ValueError('New payload changed: '+name)
    build=a.project/'.sync/wc-s1-source-build-r1'
    lock=json.loads((build/'build-audit-r2.json').read_text())
    imported=json.loads((build/'import-r2/receipt.json').read_text())
    if imported['package_lock_sha256']!=sha(build/'build-audit-r2.json'):raise ValueError('Package import lock differs')
    for name,item in lock['package_files'].items():
        if sha(build/'build-r1/lib'/name)!=item['sha256']:raise ValueError('Built package changed')
    if a.validate_only:
        print(json.dumps({'status':'NEW_SCOPE_ASSETS_SOURCE_PACKAGE_PASS_NO_TORCH_OR_CUDA','config_sha256':sha(a.stage/'mid-config.json')}));return
    if a.cpu_import_check:
        sys.argv=[str(a.stage/'scripts/run_wc_s0_profile.py'),'--project',str(a.project),'--stage',str(a.stage),
                  '--runtime',str(a.runtime),'--output',str(a.output),'--cpu-import-check']
        base.main();return
    if not a.gpu_uuid or os.environ.get('CUDA_VISIBLE_DEVICES')!=a.gpu_uuid or Path.cwd().resolve()!=a.runtime.resolve():
        raise ValueError('Explicit supervised GPU and runtime required')
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'src'),str(a.runtime),str(a.runtime/'packages/cosmos-oss'),
                  str(a.runtime/'packages/cosmos-cuda'),str(build/'build-r1/lib')]
    a.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    state={'status':'INITIALIZING','pid':os.getpid(),'started_unix':time.time(),'scope':c,'phases':[],
           'cases':[],'snapshots':[],'quality_evaluation':False,'complete_video':False}
    def save():
        tmp=a.output/'receipt.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(a.output/'receipt.json')
    save()
    try:
        import numpy as np
        import torch
        from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
        init_environment();init_output_dir(a.output,profile=False)
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        from cosmos_predict2.inference import Inference
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.measurement import BlockCounts
        from wcomr.mid_coverage import StateRoundtrip,PrefixComplete,tree_digest,compare_prefix
        from wcomr.mid_scope import request_wc_gate
        from wcomr.mid_parity_scope import validate_parity_scope
        from wcomr.prepared_input import RNGState,PreparedInputReplay,input_signatures
        from wcomr.mid_prefix_audit import state_components
        from wcomr.wc_qkv_snapshot import dump_qkv
        from wcomr.sparge_routed_no_pv import routed_no_pv
        expected=validate_parity_scope(c)
        if torch.__version__!='2.7.1+cu128' or torch.cuda.get_device_capability()!=(8,6):raise ValueError('Actual Torch/sm86 differs')
        params=json.loads((a.project/'configs/f1_setup.json').read_text())
        if params['disable_guardrails'] or params['use_torch_compile']:raise ValueError('Frozen safety/eager required')
        params.update(keep_going=True,worldcache_enabled=True,output_dir=str(a.output))
        setup=SetupArguments(**params)
        state['registration']=install_core_inference_registration(setup.model,setup.experiment)
        sample=InferenceArguments.from_files([a.project/'configs/cal_w1d8.jsonl'])[0]
        start=time.perf_counter();inference=Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-start
        model,net=inference.pipe.model,inference.pipe.model.net
        if len(net.blocks)!=28 or model.config.use_torch_compile:raise ValueError('Model structure differs')
        for block in net.blocks:
            attn=block.self_attn
            if (attn.backend,attn.n_heads,attn.head_dim,type(attn.attn_op).__name__)!=('minimal_a2a',16,128,'MinimalA2AAttnOp'):
                raise ValueError('Attention binding differs')
        wc_settings={k:getattr(net,k) for k in ['worldcache_num_steps','worldcache_rel_l1_thresh','worldcache_ret_ratio',
                    'probe_depth','worldcache_motion_sensitivity','worldcache_flow_enabled','worldcache_flow_scale',
                    'worldcache_saliency_enabled','worldcache_saliency_weight','worldcache_osi_enabled','worldcache_dynamic_decay']}
        state['wc_settings']=wc_settings
        if wc_settings['worldcache_num_steps']!=params['worldcache_num_steps'] or wc_settings['probe_depth']!=params['worldcache_probe_depth']:
            raise ValueError('WC constructor differs from frozen setup')
        common_rng=RNGState()
        prepared=PreparedInputReplay(inference.pipe._get_data_batch_input)
        prepare_owned='_get_data_batch_input' in vars(inference.pipe)
        prepare_prior=vars(inference.pipe).get('_get_data_batch_input')
        inference.pipe._get_data_batch_input=prepared
        for phase in c['phases']:
            common_rng.restore()
            wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in wc_settings.items()})
            # apply_worldcache argument names for relative threshold/ratio are compatible after prefix removal.
            result={'phase':phase,'output_hashes':[],'input_hashes':[],'state_fingerprints':[],
                    'roundtrips':[],'field_signatures':[],'named_inputs':[],'conditions':[],'solver_steps':0,'status':'GENERATING_PREFIX'}
            state['phases'].append(result);state['status']=phase.upper();save()
            counts=BlockCounts(net.blocks,cache_model=net)
            call=0;step=0;restores=[]
            def replace(owner,name,value):
                own=name in vars(owner);prior=vars(owner).get(name)
                restores.append(lambda:(setattr(owner,name,prior) if own else delattr(owner,name)))
                setattr(owner,name,value)
            original_forward=net.forward
            def forward(*args,**kwargs):
                nonlocal call
                call+=1
                if call==1:request_wc_gate(net,sample.num_steps,params['worldcache_probe_depth'])
                result['named_inputs'].append(input_signatures(args,kwargs))
                result['input_hashes'].append(tree_digest([x for x in list(args)+list(kwargs.values()) if isinstance(x,torch.Tensor)]))
                output=original_forward(*args,**kwargs)
                result['output_hashes'].append(tree_digest(output))
                return output
            replace(net,'forward',forward)
            original_denoise=model.denoise
            def denoise(*args,**kwargs):
                condition=kwargs.get('condition',args[3] if len(args)>3 else None)
                if condition is None:raise ValueError('Condition identity missing')
                result['conditions'].append(input_signatures((),condition.to_dict(skip_underscore=False)))
                return original_denoise(*args,**kwargs)
            replace(model,'denoise',denoise)
            scheduler=model.sample_scheduler
            original_step=scheduler.step
            def solver_step(*args,**kwargs):
                nonlocal step
                output=original_step(*args,**kwargs);step+=1
                result['solver_steps']=step
                if step in c['state_steps']:
                    latent=output[0] if isinstance(output,tuple) else output.prev_sample
                    generator=kwargs.get('generator')
                    snapshot=StateRoundtrip(net,scheduler,latent,generators=[generator] if generator is not None else [])
                    before=snapshot.fingerprint()
                    fields=state_components(snapshot)
                    result['field_signatures'].append({'solver_step':step,'call':call,'components':fields})
                    if phase=='observed_prefix':
                        restored=snapshot.restore()
                        if snapshot.fingerprint()!=before or tree_digest(restored)!=tree_digest(latent):raise ValueError('State roundtrip drift')
                        result['roundtrips'].append({'solver_step':step,'call':call,'net_keys':snapshot.keys,
                            'solver_keys':sorted(vars(scheduler)),'fingerprint':before,'status':'ROUNDTRIP_PASS'})
                    result['state_fingerprints'].append({'solver_step':step,'call':call,'sha256':before})
                    del snapshot
                if step==c['stop_after_solver_steps']:raise PrefixComplete()
                return output
            replace(scheduler,'step',solver_step)
            if phase=='observed_prefix':
                for layer in c['capture_layers']:
                    op=net.blocks[layer].self_attn.attn_op;original=op.forward
                    def observed(*args,_layer=layer,_original=original,**kwargs):
                        dense_output=_original(*args,**kwargs)
                        if call not in c['capture_calls']:return dense_output
                        context={'call':call,'layer':_layer,'cfg_slot':(call-1)%2,'cache_counter_before':net.cnt}
                        target=a.output/('qkv-call%02d-layer%02d.pt'%(call,_layer))
                        entry=dump_qkv(args,target,old['expected_qkv_shape'],old['expected_qkv_dtype'])
                        state['snapshots'].append(dict(context,**entry));save()
                        q,k,v=args;full=torch.ones(1,16,243,486,device=q.device,dtype=torch.bool)
                        reference=dense_output.reshape(1,31104,2048)
                        pair=None
                        cpu_rng=torch.random.get_rng_state();cuda_rng=torch.cuda.get_rng_state_all()
                        try:
                            with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
                                for arm in ['dense','matched_full','sparse']:
                                    def operation():
                                        if arm=='dense':return _original(*args,**kwargs).reshape(1,31104,2048),{'selected_fraction':1.,'executed_fraction':1.}
                                        return routed_no_pv(q,k,v,full,c['policy']['sim'],c['policy']['cdf'],arm=='matched_full')
                                    for _ in range(c['warmups']):candidate,meta=operation();torch.cuda.synchronize()
                                    wall=[]
                                    for _ in range(c['repeats']):
                                        torch.cuda.synchronize();start=time.perf_counter();candidate,meta=operation();torch.cuda.synchronize()
                                        wall.append((time.perf_counter()-start)*1000)
                                    def error(ref):return float(((candidate.float()-ref.float()).square().mean()/ref.float().square().mean().clamp_min(1e-20)).sqrt())
                                    row=dict(context,arm=arm,input_sha256=entry['sha256'],wall_ms=wall,
                                        median_wall_ms=statistics.median(wall),routing=meta,rmse_vs_dense=error(reference),
                                        finite=bool(torch.isfinite(candidate).all()),output_sha256=tree_digest(candidate))
                                    if arm=='matched_full':pair=candidate.clone()
                                    if arm=='sparse':row['rmse_vs_matched_full']=error(pair)
                                    state['cases'].append(row);save()
                                    if not row['finite']:raise ValueError('Nonfinite shadow output')
                        finally:
                            if not torch.equal(cpu_rng,torch.random.get_rng_state()) or not all(torch.equal(x,y) for x,y in zip(cuda_rng,torch.cuda.get_rng_state_all())):
                                raise ValueError('Shadow changed RNG')
                        del pair,candidate,full
                        return dense_output
                    replace(op,'forward',observed)
            begin=time.perf_counter()
            try:
                inference.generate([sample],output_dir=a.output/phase)
                raise ValueError('Expected controlled solver-prefix completion absent')
            except PrefixComplete:
                torch.cuda.synchronize()
                result.update(status='EXPECTED_PREFIX_COMPLETE_NOT_VIDEO',wall_seconds=time.perf_counter()-begin,
                    trace=counts.trace,block_counts=counts.result())
                result['sampling']={'scheduler_class':type(scheduler).__name__,'requested_steps':sample.num_steps,
                    'actual_schedule_steps':len(scheduler.timesteps),'timesteps':scheduler.timesteps.cpu().tolist(),
                    'worldcache_horizon':net.worldcache_num_steps,'use_kerras_sigma':model.config.use_kerras_sigma_at_inference}
                if call!=26 or len(counts.trace)!=26 or not all(counts.trace[t-1]['deep_executed'] for t in c['capture_calls']):
                    raise ValueError('Prefix/actual middle full calls differ from frozen trace')
                if len(scheduler.timesteps)!=36 or not model.config.use_kerras_sigma_at_inference:raise ValueError('Frozen solver grid differs')
                save()
            finally:
                for restore in reversed(restores):restore()
                counts.close()
        left,right=state['phases']
        state['all_gate_checks']={k:left[k]==right[k] for k in
            ['input_hashes','output_hashes','trace','block_counts','state_fingerprints','sampling','named_inputs','conditions','field_signatures']}
        state['prepared_input_calls']=prepared.calls
        if len(prepared.calls)!=2 or prepared.calls[0]['prepared']!=prepared.calls[1]['prepared']:
            raise ValueError('Shared official preparation contract differs')
        state['parity']=compare_prefix(left,right)
        if not all(state['all_gate_checks'].values()):
            raise ValueError('r3 fieldwise/input/condition gate differs: '+json.dumps(state['all_gate_checks']))
        if state['phases'][0]['input_hashes']!=state['phases'][1]['input_hashes']:raise ValueError('Prefix inputs differ')
        if len(state['snapshots'])!=len(expected) or {(x['call'],x['layer']) for x in state['snapshots']}!=expected or len(state['cases'])!=3*len(expected):
            raise ValueError('Middle all-depth coverage incomplete')
        state['status']='R3_SHARED_INPUT26_FORWARD13_STEP_ALL_STATE_FIELDWISE_PARITY_2QKV6CASES_REQUIRES_AUDIT'
        if prepare_owned:setattr(inference.pipe,'_get_data_batch_input',prepare_prior)
        else:delattr(inference.pipe,'_get_data_batch_input')
        cleanup_environment()
    except BaseException as exc:
        state.update(status='TECH_BLOCKED',error_type=type(exc).__name__,error=str(exc));traceback.print_exc();raise
    finally:
        state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()


if __name__=='__main__':main()
