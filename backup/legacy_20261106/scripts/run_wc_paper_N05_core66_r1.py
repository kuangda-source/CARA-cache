#!/usr/bin/env python3
"""One resident model, eleven finite workpoints, all66 guarded requests."""
import argparse
import copy
import inspect
import json
import os
from pathlib import Path
import sys
import time

def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--cpu-check',action='store_true');p.add_argument('--source-revision');p.add_argument('--gpu-uuid')
    a=p.parse_args()
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
    import torch
    if a.cpu_check:
        os.environ['CUDA_VISIBLE_DEVICES']=''
        def forbidden(*args,**kw):raise RuntimeError('N05 production CPU forbids CUDA/model weights/downloads')
        torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,n):raise RuntimeError('N05 CPU denies Triton execution: '+n)
        triton.runtime.driver.active=ImportOnlyDriver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        prior=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
        hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True
        torch.cuda.current_device=lambda:0
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_predict2._src.predict2.models.fm_solvers_unipc import FlowUniPCMultistepScheduler
    from cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit import MinimalV1LVGDiT
    from wcomr.paper_baseline_production_r1 import CONFIG,RUN,COUNTS,STRATEGY,DEFAULTS,PRODUCTION_CPU_STATUS,sha,write,validate,validate_contract,matrix,diagnostic_warm,audit_row
    from wcomr.paper_baseline_grid_r1 import execute,point
    from wcomr.w1_native_reference_sampling import NATIVE_FORWARD
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    if a.cpu_check:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=prior
    c,reg,old,inputs,tables,previous=validate(a.project,a.stage)
    calibration,specs,_,evidence=inputs
    samples={}
    for r in c['requests']:
        for method in c['methods']:
            data={**r,'num_steps':point(method)['requested_steps']}
            sample=InferenceArguments(**data)
            assert all(sample.model_dump(mode='json')[k]==v for k,v in data.items())
            samples[(r['name'],method)]=sample
    plan=matrix([r['name'] for r in c['requests']])
    setupdata=json.loads((a.project/'configs/f1_setup.json').read_text())
    setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    native=MinimalV1LVGDiT.forward
    assert native.__module__+'.'+native.__qualname__==NATIVE_FORWARD
    native_path=Path(inspect.getfile(native)).resolve()
    native_identity=dict(qualified_name=NATIVE_FORWARD,path=str(native_path),sha256=sha(native_path))
    if a.cpu_check:
        from types import SimpleNamespace
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        for n in (18,26,35):
            sample=samples[(c['requests'][0]['name'],'NATIVE'+str(n))]
            try:
                execute(dummy,sample,'NATIVE'+str(n),table_parameters=tables,previous_parameters=previous,
                    settings=old['historical_wc_settings'],specs=specs[STRATEGY],runtime=a.project/'runtime',wc=wc,rf=rf,
                    calibration=calibration,inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=old['expected_real_shape'])
            except ValueError as e:assert str(e)=='Ordinary guardrails required'
            else:raise AssertionError('Unguarded Native path accepted')
        clock=json.loads((a.stage/c['references']['native_scheduler_CPU']['ref']).read_text())
        grid=[]
        for row in clock['rows']:
            s=FlowUniPCMultistepScheduler(num_train_timesteps=1000,shift=1,use_dynamic_shifting=False)
            s.set_timesteps(row['requested_steps'],device='cpu',shift=5.,use_kerras_sigma=True)
            assert s.timesteps.tolist()==row['timesteps'] and s.sigmas.tolist()==row['sigmas']
            grid.append(dict(requested_steps=row['requested_steps'],actual_updates=len(s.timesteps),all_sigmas_and_timesteps_equal=True))
        mutations=dict(scope_counts={**COUNTS,'scientific_paths':43},methods=c['methods'][:-1],
            training=True,P_ACR=True,T1=True,head_elision=True,new_final_test_inputs=True,
            billed_limit_GPUh=12.,neighbor_gap_retained=False,direct_corrected_neighbor_included=True)
        for key,value in mutations.items():
            bad=copy.deepcopy(c);bad[key]=value
            try:validate_contract(bad)
            except ValueError:pass
            else:raise AssertionError('Changed complete card accepted: '+key)
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',dict(status=PRODUCTION_CPU_STATUS,exit_code=0,
            source_revision=reg['source_revision'],registration_sha256=sha(a.stage/'registration.json'),
            config_sha256=sha(a.stage/CONFIG),scope_counts=COUNTS,matrix=plan,
            actual_sample_argument_variants=len(samples),native_forward_identity=native_identity,
            actual_scheduler_CPU_checks=grid,mutations_refused=list(mutations),input_evidence=evidence,
            sampling_CPU_ref=c['references']['sampling_CPU_raw'],CUDA_initialized=False,
            GPU_submissions=0,model_weights_loaded=0,ledger_written=False))
        print(PRODUCTION_CPU_STATUS);return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['status']==PRODUCTION_CPU_STATUS and proof['source_revision']==reg['source_revision']==a.source_revision
    assert proof['registration_sha256']==sha(a.stage/'registration.json') and proof['config_sha256']==sha(a.stage/CONFIG)
    assert proof['native_forward_identity']==native_identity
    assert os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    lease=(a.project/'.sync/gpu-locks'/(a.gpu_uuid+'.lock')).resolve()
    assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==lease
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    output=a.project/'outputs'/RUN
    assert output.is_dir() and not (output/'runner.json').exists()
    state=dict(status='N05_CORE66_INITIALIZING_ONE_RESIDENT_MODEL',pid=os.getpid(),source_revision=a.source_revision,
        config_sha256=sha(a.stage/CONFIG),scope_counts=COUNTS,matrix=plan,runs=[],started_unix=time.time(),
        native_forward_identity=native_identity,new_input_confirmation=False,neighbor_comparison_completed=False)
    save=lambda:write(output/'runner.json',state)
    save();init_environment();init_output_dir(output,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        begin=time.perf_counter();inference=im.Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-begin
        model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
        contract=json.loads((a.stage/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
        mode=establish_shared_eval(net,contract['module_types']);verify_shared_eval(net,mode)
        assert type(net).forward is MinimalV1LVGDiT.forward and torch.__version__=='2.7.1+cu128'
        assert torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert all(b.self_attn.backend=='minimal_a2a' and type(b.self_attn.attn_op).__name__=='MinimalA2AAttnOp' for b in net.blocks)
        settings=old['historical_wc_settings']
        wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
        versions=[(p,p._version) for p in net.parameters()]
        state['status']='N05_CORE66_ALL_PATHS_RUNNING';save()
        for planned in plan:
            row={**planned,'status':'RUNNING','started_unix':time.time()};state['runs'].append(row);save()
            sample=samples[(planned['scene'],planned['method'])]
            initial.restore();assert initial.fingerprint()==origin;verify_shared_eval(net,mode)
            directory=output/planned['id']
            result=execute(inference,sample,planned['method'],table_parameters=tables,previous_parameters=previous,
                runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,calibration=calibration,specs=specs[STRATEGY],
                inference_module=im,output=directory,expected_shape=old['expected_real_shape'],audit=diagnostic_warm(planned))
            guides=result.pop('guided',None)
            if guides is not None:
                assert diagnostic_warm(planned) and len(guides)==36
                path=directory/'warm-guided.pt';assert not path.exists();torch.save({'guided':guides},path)
                result.update(warm_guided_outputs=36,warm_guided_tree_sha256=tree_digest(guides),
                    warm_guided_artifact=dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size))
            final=result.pop('final_latent',None)
            if final is not None:
                path=directory/'final-latent.pt';assert not path.exists();torch.save({'final_latent':final},path)
                result.update(final_latent_sha256=tree_digest(final),final_artifact=dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size))
            row.update(result,ended_unix=time.time());audit_row(row,planned);save()
            assert row['status'] in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED')
            assert all(p._version==v for p,v in versions)
        initial.restore();assert initial.fingerprint()==origin and len(state['runs'])==66
        state['status']='N05_CORE66_GPU_COMPLETE_CPU_AUDIT_PENDING';save()
    except BaseException as e:
        state.update(status='N05_CORE66_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise
    finally:cleanup_environment();state['ended_unix']=time.time();save()

if __name__=='__main__':main()
