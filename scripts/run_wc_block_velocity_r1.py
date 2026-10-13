#!/usr/bin/env python3
"""One model; four bound B prefixes, twelve saved-velocity suffixes and unchanged C state."""
import argparse,copy,json,os,sys,time
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--cpu-check',action='store_true');p.add_argument('--source-revision');p.add_argument('--gpu-uuid');a=p.parse_args()
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
    import torch
    if a.cpu_check:
        os.environ['CUDA_VISIBLE_DEVICES']=''
        def forbidden(*a,**k):raise RuntimeError('Production CPU forbids CUDA/weights/downloads')
        torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,n):raise RuntimeError('No CPU Triton execution: '+n)
        triton.runtime.driver.active=ImportOnlyDriver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        prev=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
        hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from wcomr.block_velocity_production_r1 import CONFIG,RUN,UUID,MODE_REF,COUNTS,STRATEGY,sha,write,validate,validate_contract
    from wcomr import clean_speed20_r1 as clean
    from wcomr.math_n2_batch_r1 import execute
    from wcomr.block_velocity_suffix3_r1 import block_velocity_suffix_install
    from wcomr.block_saved_reference_r1 import load_reference
    from wcomr.rv0_causal import original_decode_tails
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    if a.cpu_check:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=prev
    c,reg,old,inputs,params,baseline=validate(a.project,a.stage)
    cal,specs,refs,evidence=inputs;samples=[InferenceArguments(**r) for r in c['requests']]
    assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['requests']))
    setupdata=json.loads((a.project/'configs/f1_setup.json').read_text())
    setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    if a.cpu_check:
        from importlib.util import spec_from_file_location,module_from_spec
        from types import SimpleNamespace
        sp=spec_from_file_location('suffix8_supervisor',a.stage/'scripts/supervise_wc_block_velocity_r1.py');m=module_from_spec(sp);sp.loader.exec_module(m)
        cmd=m.child_command(SimpleNamespace(project=a.project,stage=a.stage,source_revision=reg['source_revision']),UUID)
        assert Path(cmd[2])==a.stage/'scripts/run_wc_block_velocity_r1.py' and sha(Path(cmd[2]))==reg['payload_sha256']['scripts/run_wc_block_velocity_r1.py']
        assert cmd[3:]==['--project',str(a.project),'--stage',str(a.stage),'--source-revision',reg['source_revision'],'--gpu-uuid',UUID]
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:execute(dummy,samples[0],'P_OFF',parameters=params,runtime=a.project/'runtime',wc=wc,rf=rf,settings={},calibration=cal,specs=specs[STRATEGY],inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=old['expected_real_shape'])
        except ValueError as e:assert str(e)=='Ordinary guardrails required'
        else:raise AssertionError('Unguarded production accepted')
        mutations={'scope_counts':{**COUNTS,'suffixes':0},'states':c['states'][:-1],
            'head_elision':True,'training':True,'fit_in_parent':True,'online_teachers':True,
            'only_first_returned_velocity_changed':False,'saved_vectors_committed_to_anchor':True,'first_branch_readouts':['A','C','C'],'automatic_single_job_GPUh':4,'cumulative_cap_GPUh':77.89524658965853,'forecast_complete_GPUh':9.}
        for k,v in mutations.items():
            bad=copy.deepcopy(c);bad[k]=v
            try:validate_contract(bad)
            except ValueError:pass
            else:raise AssertionError('Changed complete contract accepted: '+k)
        from wcomr.block_velocity_production_r1 import LABELS
        sp=spec_from_file_location('B_actual_post_watcher',a.stage/'scripts/watch_wc_block_velocity_cpu_r1.py')
        watcher=module_from_spec(sp);sp.loader.exec_module(watcher)
        post_output,post_command=watcher.paths(a.stage,a.project)
        assert post_output==a.project/'outputs'/RUN and post_command[1]==str(a.stage/'scripts/postprocess_wc_block_velocity_cpu_r1.py')
        assert sha(Path(post_command[1]))==reg['payload_sha256']['scripts/postprocess_wc_block_velocity_cpu_r1.py']
        watcher_proof={'output':str(post_output),'command':post_command,'actual_config_derived_paths_verified':True}
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',{'status':'BLOCK_SAVED_VELOCITY_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU','exit_code':0,
            'GPU_submissions':0,'CUDA_initialized':False,'ledger_written':False,'scope_counts':COUNTS,
            'source_revision':reg['source_revision'],'config_sha256':sha(a.stage/CONFIG),'registration_sha256':sha(a.stage/'registration.json'),
            'sampling_CPU_sha256':sha(a.stage/'sampling-CPU-result.json'),'saved_reference_CPU_sha256':sha(a.stage/'saved-reference-CPU-result.json'),'mutations_refused':list(mutations),'input_evidence':evidence,'watcher_proof':watcher_proof})
        print('BLOCK_SAVED_VELOCITY_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU');return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['status']=='BLOCK_SAVED_VELOCITY_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['config_sha256']==sha(a.stage/CONFIG) and proof['registration_sha256']==sha(a.stage/'registration.json')
    assert proof['saved_reference_CPU_sha256']==sha(a.stage/'saved-reference-CPU-result.json')
    assert a.source_revision==reg['source_revision'] and os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid==UUID and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    root=a.project/'outputs'/RUN;assert root.is_dir() and not (root/'runner.json').exists()
    state={'status':'BLOCK_SAVED_VELOCITY_INITIALIZING','pid':os.getpid(),'runs':[],'source_revision':a.source_revision,
        'scope_counts':COUNTS,'parameters_fingerprint':params['fingerprint'],'started_unix':time.time()}
    save=lambda:write(root/'runner.json',state);save();init_environment();init_output_dir(root,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        start=time.perf_counter();inf=im.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-start
        model=inf.pipe.model;net=model.net;scheduler=model.sample_scheduler
        mode=establish_shared_eval(net,json.loads((a.stage/MODE_REF).read_text())['module_types']);verify_shared_eval(net,mode)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert all(b.self_attn.backend=='minimal_a2a' and type(b.self_attn.attn_op).__name__=='MinimalA2AAttnOp' for b in net.blocks)
        settings=old['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint();versions=[(p,p._version) for p in net.parameters()]
        decoder,writer,tails=original_decode_tails(a.project/'runtime',im)
        ordinary_writer=im.save_img_or_video
        for i,sample in enumerate(samples):
            initial.restore();assert initial.fingerprint()==fp;verify_shared_eval(net,mode)
            directory=root/str(i);directory.mkdir();holder={};point=c['states'][i]
            row={'scene':sample.name,'point':point,'status':'RUNNING','started_unix':time.time()}
            state['runs'].append(row);state['status']='BLOCK_SAVED_VELOCITY_FOUR_PARENTS_EIGHT_ENDPOINTS_RUNNING';save()
            def save_branch(step,label,tensors):
                d=directory/'branches'/label;d.mkdir(parents=True);raw=d/'vectors.pt';assert not raw.exists()
                start=time.perf_counter();torch.save(tensors,raw);raw_write=time.perf_counter()-start
                raw_bound={'path':str(raw),'sha256':sha(raw),'bytes':raw.stat().st_size,'tensor_sha256':tree_digest(tensors)}
                begin=time.perf_counter();latent=tensors['final_latent'].to(model.tensor_kwargs['device']);torch.cuda.synchronize()
                upload=time.perf_counter()-begin
                with clean.patched(im,'save_img_or_video',ordinary_writer):
                    torch.cuda.synchronize();begin=time.perf_counter();video=decoder(inf.pipe,latent);torch.cuda.synchronize()
                    decode_seconds=time.perf_counter()-begin
                    begin=time.perf_counter();path=writer(inf,video,d/sample.name)
                    write_seconds=time.perf_counter()-begin
                video_path=None if path is None else Path(path)
                if video_path is not None:assert video_path.is_file()
                return {**raw_bound,'video_artifact':None if video_path is None else {'path':str(video_path),'sha256':sha(video_path),'bytes':video_path.stat().st_size},'video_status':'VIDEO_REJECTED' if video_path is None else 'COMPLETE',
                    'original_tails':tails,'research_raw_write_seconds':raw_write,'research_CPU_to_GPU_upload_seconds':upload,
                    'VAE_decoder_seconds':decode_seconds,'guarded_writer_seconds':write_seconds,
                    'main_cost_boundary':'INSTRUMENTED_REMAINING_SAMPLING_PLUS_DECODER_ONLY_GUARDED_WRITER_SEPARATE_NOT_CLEAN_END_TO_END'}
            common=dict(runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,calibration=cal,
                specs=specs[STRATEGY],inference_module=im,expected_shape=old['expected_real_shape'],audit=True)
            reference=load_reference(c['point_records'][i],a.project)
            with block_velocity_suffix_install(clean,scheduler,point,reference,c['checkpoint_reserves'],save_branch,params,holder,
                    runtime=a.project/'runtime',reverse_order=c['mirror_order'][i]):
                result=clean.execute(inf,sample,'KEEP_A_P',output=directory/'parent',**common)
            final=result.pop('final_latent',None);guided=result.pop('guided',None);owner=holder['owner']
            assert final is not None and guided is not None and len(guided)==36 and result['status'] in ('COMPLETE','VIDEO_REJECTED')
            vec=directory/'parent-vectors.pt';torch.save({'final_latent':final,'guided':guided},vec)
            bind=baseline['bindings'][sample.name];event=owner.event_records[0];n=point['chosen']['step']
            row.update(result,parent_vectors={'path':str(vec),'sha256':sha(vec),'bytes':vec.stat().st_size},
                final_latent_sha256=tree_digest(final),guided_sha256=[tree_digest(g) for g in guided],event=event,
                actual_pair_computations=owner.actual_pair_computations,
                original_parent_all36_guided_equal=[tree_digest(g) for g in guided]==bind['guided_sha256'],
                original_parent_final_actions_equal=tree_digest(final)==bind['final_latent_sha256'] and result['actions']==bind['actions'],
                ended_unix=time.time());save()
            assert row['original_parent_all36_guided_equal'] and row['original_parent_final_actions_equal']
            assert len(owner.event_records)==1 and len(event['branches'])==3 and owner.actual_pair_computations==36+3*(37-n)
            assert event['actual_teacher_calls']==event['actual_B_executor_calls']==0
            assert event['first_physical_action']=='CC' and event['only_first_returned_velocity_changed']
            assert event['offline_saved_vectors_not_new_D_or_P_anchor']
            assert owner.injections==dict(C_REPLAY=0,DENSE_VELOCITY=1,L2_VELOCITY=1)
            assert all(p._version==v for p,v in versions)
        initial.restore();assert initial.fingerprint()==fp
        assert len(state['runs'])==4 and sum(r['actual_pair_computations'] for r in state['runs'])==312
        state['status']='BLOCK_SAVED_VELOCITY_ALL4_PARENTS12_SUFFIXES16_OUTPUTS_GPU_COMPLETE_CPU_PENDING';save()
    except BaseException as e:
        state.update(status='BLOCK_SAVED_VELOCITY_TECHNICAL_STOP_FULL312_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise
    finally:cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
