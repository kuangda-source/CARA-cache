#!/usr/bin/env python3
"""One resident model; fixed two-scene warmups and forward/reverse timed rounds."""
import argparse, copy, inspect, json, os, sys, time
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
        def forbidden(*a,**kw):raise RuntimeError('Production CPU forbids weights/CUDA/downloads')
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
    from wcomr.clean_speed20_production_r1 import CONFIG,UUID,MODE_REF,sha,write,validate,validate_contract
    from wcomr.clean_speed20_r1 import RUN,STRATEGY,execute,matrix
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    if a.cpu_check:
        hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=prev
    c,reg,old,inputs=validate(a.project,a.stage);calibration,specs,refs,evidence=inputs
    samples=[InferenceArguments(**r) for r in c['requests']]
    assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['requests']))
    setupdata=json.loads((a.project/'configs/f1_setup.json').read_text())
    setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    if a.cpu_check:
        from types import SimpleNamespace
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        for method in c['methods']:
            try:execute(dummy,samples[0],method,runtime=a.project/'runtime',wc=wc,rf=rf,settings={},calibration=calibration,specs=specs[STRATEGY],inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=old['expected_real_shape'])
            except ValueError as e:assert str(e)=='Ordinary guardrails required'
            else:raise AssertionError('Guardrail-less path accepted')
        badkeys={'timed_runs':19,'warmup_runs':0,'model_loads':2,'A_method':'W1_ONE_PHASE','early_head_elision':True,'A_strength':[1.,1.],'automatic_single_job_GPUh':4,'methods':c['methods'][:-1],'working_epoch_strategy':'NONZERO','training':True,'forecast_complete_GPUh':9}
        for k,v in badkeys.items():
            bad=copy.deepcopy(c);bad[k]=v
            try:validate_contract(bad)
            except ValueError:pass
            else:raise AssertionError('Changed scope accepted: '+k)
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',{'status':'CLEAN_SPEED20_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU','exit_code':0,'GPU_submissions':0,'CUDA_initialized':False,'ledger_written':False,'config_sha256':sha(a.stage/CONFIG),'registration_sha256':sha(a.stage/'registration.json'),'sampling_CPU_sha256':sha(a.stage/'sampling-CPU-result.json'),'scope':matrix(),'source_revision':reg['source_revision'],'mutations_refused':list(badkeys),'guardrail_less_entries_refused':5,'input_evidence':evidence})
        print('CLEAN_SPEED20_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU');return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['status']=='CLEAN_SPEED20_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['config_sha256']==sha(a.stage/CONFIG) and proof['registration_sha256']==sha(a.stage/'registration.json')
    assert os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid==UUID and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    output=a.project/'outputs'/RUN;assert output.is_dir() and not (output/'runner.json').exists()
    state={'status':'INITIALIZING_SINGLE_RESIDENT_MODEL','pid':os.getpid(),'source_revision':a.source_revision,'config_sha256':sha(a.stage/CONFIG),'matrix':matrix(),'runs':[],'started_unix':time.time()}
    save=lambda:write(output/'runner.json',state)
    save();init_environment();init_output_dir(output,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        begin=time.perf_counter();inf=im.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-begin
        model=inf.pipe.model;net=model.net;scheduler=model.sample_scheduler
        mode=establish_shared_eval(net,json.loads((a.stage/MODE_REF).read_text())['module_types']);verify_shared_eval(net,mode)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert all(b.self_attn.backend=='minimal_a2a' and type(b.self_attn.attn_op).__name__=='MinimalA2AAttnOp' for b in net.blocks)
        settings=old['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fingerprint=initial.fingerprint()
        versions=[(p,p._version) for p in net.parameters()];state['status']='FIXED_40_PATHS_RESIDENT_RUNNING';save()
        expected={k:v['final_latent_sha256'] for k,v in c['old_audit_endpoint_and_action_bindings'].items()}
        for row in matrix():
            r={**row,'status':'RUNNING','started_unix':time.time()};state['runs'].append(r);save()
            begin=time.perf_counter();initial.restore();verify_shared_eval(net,mode)
            assert initial.fingerprint()==fingerprint
            r['cache_rng_reset_seconds']=time.perf_counter()-begin
            sample=next(s for s in samples if s.name==row['scene'])
            result=execute(inf,sample,row['method'],runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,calibration=calibration,specs=specs[STRATEGY],inference_module=im,output=output/row['id'],expected_shape=old['expected_real_shape'],save_video=True)
            begin=time.perf_counter();final=result.pop('final_latent',None)
            if final is not None:
                r['final_latent_sha256']=tree_digest(final)
                r['old_audit_endpoint_equal']=r['final_latent_sha256']==expected[row['scene']+':'+row['method']]
                r['expected_old_endpoint_sha256']=expected[row['scene']+':'+row['method']]
                bind=c['old_audit_endpoint_and_action_bindings'][row['scene']+':'+row['method']]
                r['old_actions_equal']=bind['actions'] is None or bind['actions']==result['actions']
                torch.save({'final_latent':final},output/row['id']/'final-latent.pt')
                del final
            r.update(result,ended_unix=time.time(),outside_timer_endpoint_check_seconds=time.perf_counter()-begin)
            save()
            if r['status']!='COMPLETE':raise ValueError('Guardrail outcome changed; retain full40 and all20 timing slots')
            if not r['old_audit_endpoint_equal'] or not r['old_actions_equal']:raise ValueError('Clean endpoint/action differs from audit; do not report as equivalent algorithm speed')
            if any(p._version!=v for p,v in versions):raise ValueError('Frozen generator parameters changed')
        initial.restore();assert initial.fingerprint()==fingerprint
        state['status']='COMPLETE40_RAW_RESULTS_REQUIRE_CPU93_FRAME_SCORES';save()
    except BaseException as e:
        state.update(status='TECHNICAL_STOP_FULL40_AND20_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise
    finally:
        cleanup_environment();state['ended_unix']=time.time();save()
if __name__=='__main__':main()
