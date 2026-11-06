#!/usr/bin/env python3
"""One resident model; all twenty warmups and full40 science paths."""
import argparse,copy,json,os,sys,time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--cpu-check',action='store_true');parser.add_argument('--source-revision');parser.add_argument('--gpu-uuid')
    a=parser.parse_args()
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
    import torch
    if a.cpu_check:
        os.environ['CUDA_VISIBLE_DEVICES']=''
        def forbidden(*a,**kw):raise RuntimeError('N2 production CPU prohibits CUDA/weights/downloads')
        torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,n):raise RuntimeError('N2 CPU denies Triton execution: '+n)
        triton.runtime.driver.active=ImportOnlyDriver()
        import transformers.utils as hu
        from transformers.utils import import_utils as iu
        previous=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
        hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from wcomr.simple26d_r1 import CONFIG,MODE_REF,sha,write,validate,validate_contract,RUN,STRATEGY,COUNTS,PRODUCTION_CPU_STATUS
    from wcomr.simple26d_r1 import execute
    from wcomr.simple26d_r1 import matrix
    diagnostic_warm=lambda row:row['section']=='WARMUP'
    from wcomr.simple26d_r1 import audit_row
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    if a.cpu_check:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=previous
    c,reg,old,inputs,tables,previous_parameters=validate(a.project,a.stage)
    calibration,specs,refs,evidence=inputs;samples=[InferenceArguments(**r) for r in c['requests']]
    assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['requests']))
    plan=matrix([s.name for s in samples])
    setupdata=json.loads((a.project/'configs/f1_setup.json').read_text())
    setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    if a.cpu_check:
        from types import SimpleNamespace
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:
            execute(dummy,samples[0],'FIXED_A',table_parameters=tables,previous_parameters=previous_parameters,
                runtime=a.project/'runtime',wc=wc,rf=rf,settings={},calibration=calibration,specs=specs[STRATEGY],
                inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=old['expected_real_shape'])
        except ValueError as e:assert str(e)=='Ordinary guardrails required'
        else:raise AssertionError('Unguarded path accepted')
        mutations={'scope_counts':{**COUNTS,'scientific_paths':23},'methods':c['methods'][:-1],
            'A_method':'W1_ONE_PHASE','P_enabled':True,'online_teachers':True,'training':True,
            'autonomy_exclusive_upper_GPUh':8,'cumulative_cap_GPUh':77.,'billed_limit_GPUh':12.,
            'timing_claim':'CLEAN_LATENCY','plans':{**c['plans'],'UNIFORM_A':['D']*36}}
        for k,v in mutations.items():
            bad=copy.deepcopy(c);bad[k]=v
            try:validate_contract(bad)
            except ValueError:pass
            else:raise AssertionError('Changed whole scope accepted: '+k)
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',dict(status=PRODUCTION_CPU_STATUS,exit_code=0,
            GPU_submissions=0,CUDA_initialized=False,ledger_written=False,config_sha256=sha(a.stage/CONFIG),
            registration_sha256=sha(a.stage/'registration.json'),sampling_CPU_sha256=sha(a.stage/'simple26d-sampling-CPU-result.json'),
            scope_counts=COUNTS,source_revision=reg['source_revision'],mutations_refused=list(mutations),input_evidence=evidence,matrix=plan))
        print(PRODUCTION_CPU_STATUS);return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['status']==PRODUCTION_CPU_STATUS and proof['config_sha256']==sha(a.stage/CONFIG) and proof['registration_sha256']==sha(a.stage/'registration.json')
    assert os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    lease_path=(a.project/'.sync/gpu-locks'/(a.gpu_uuid+'.lock')).resolve()
    assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==lease_path
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    output=a.project/'outputs'/RUN;assert output.is_dir() and not (output/'runner.json').exists()
    state={'status':'SIMPLE26D_INITIALIZING_SINGLE_RESIDENT_MODEL','pid':os.getpid(),
        'source_revision':a.source_revision,'config_sha256':sha(a.stage/CONFIG),'scope_counts':COUNTS,
        'matrix':plan,'table_fingerprints':{g:p['fingerprint'] for g,p in tables.items()},'runs':[],'started_unix':time.time()}
    save=lambda:write(output/'runner.json',state)
    save();init_environment();init_output_dir(output,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        begin=time.perf_counter();inference=im.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-begin
        model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
        mode=establish_shared_eval(net,json.loads((a.stage/MODE_REF).read_text())['module_types']);verify_shared_eval(net,mode)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert all(b.self_attn.backend=='minimal_a2a' and type(b.self_attn.attn_op).__name__=='MinimalA2AAttnOp' for b in net.blocks)
        settings=old['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint();versions=[(p,p._version) for p in net.parameters()]
        state['status']='SIMPLE26D_ALL36_FULL_PATHS_RUNNING';save()
        for planned in plan:
            row={**planned,'status':'RUNNING','started_unix':time.time()};state['runs'].append(row);save()
            sample=next(s for s in samples if s.name==planned['scene'])
            initial.restore();assert initial.fingerprint()==fp;verify_shared_eval(net,mode)
            key=(planned['section'],sample.name,planned['round']);directory=output/planned['id']
            result=execute(inference,sample,planned['method'],table_parameters=tables,previous_parameters=previous_parameters,
                runtime=a.project/'runtime',wc=wc,rf=rf,
                settings=settings,calibration=calibration,specs=specs[STRATEGY],inference_module=im,
                output=directory,expected_shape=old['expected_real_shape'],audit=diagnostic_warm(planned))
            guides=result.pop('guided',None)
            if guides is not None:
                assert diagnostic_warm(planned) and len(guides)==36
                raw=directory/'warm-guided.pt';assert not raw.exists()
                torch.save({'guided':guides},raw)
                result['warm_guided_outputs']=len(guides)
                result['warm_guided_artifact']={'path':str(raw),'sha256':sha(raw),'bytes':raw.stat().st_size}
                result['warm_guided_tree_sha256']=tree_digest(guides)
            final=result.pop('final_latent',None)
            if final is not None:
                path=directory/'final-latent.pt';assert not path.exists();torch.save({'final_latent':final},path)
                result['final_latent_sha256']=tree_digest(final)
                result['final_artifact']={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
            row.update(result,ended_unix=time.time());save()
            assert row['status'] in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED')
            if row['status']!='TEXT_REJECTED':assert row['solver_steps']==row['guided_pairs']==36
            audit_row(row,planned)
            assert all(p._version==v for p,v in versions)
        initial.restore();assert initial.fingerprint()==fp
        assert len(state['runs'])==36
        state['status']='SIMPLE26D_ALL36_FULL24_SCIENCE_GPU_COMPLETE_CPU_AUDIT_PENDING';save()
    except BaseException as error:
        state.update(status='SIMPLE26D_TECHNICAL_STOP_FULL24_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
    finally:cleanup_environment();state['ended_unix']=time.time();save()

if __name__=='__main__':main()
