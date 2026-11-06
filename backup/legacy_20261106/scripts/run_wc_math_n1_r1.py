#!/usr/bin/env python3
"""One resident model; complete four natural parents and twelve same-state comparisons."""
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
    from wcomr.math_n1_production_r1 import CONFIG,UUID,MODE_REF,sha,write,validate,validate_contract,RUN,STRATEGY,COUNTS
    from wcomr import clean_speed20_r1 as clean
    from wcomr.math_n1_natural_diag_r1 import natural_diagnostic_install
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.mid_coverage import tree_digest
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    if a.cpu_check:
        hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=prev
    c,reg,old,inputs,index=validate(a.project,a.stage);calibration,specs,refs,evidence=inputs
    original_guided=json.loads((a.stage/c['original_guided_bindings_ref']).read_text())['bindings']
    samples=[InferenceArguments(**r) for r in c['requests']]
    assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['requests']))
    setupdata=json.loads((a.project/'configs/f1_setup.json').read_text())
    setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    if a.cpu_check:
        from types import SimpleNamespace
        dummy=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:clean.execute(dummy,samples[0],'KEEP_A_P',runtime=a.project/'runtime',wc=wc,rf=rf,settings={},calibration=calibration,specs=specs[STRATEGY],inference_module=im,output=a.stage/'NEVER_CREATED',expected_shape=old['expected_real_shape'])
        except ValueError as e:assert str(e)=='Ordinary guardrails required'
        else:raise AssertionError('Guardrail-less path accepted')
        mutations={'scope_counts':{**COUNTS,'points':11},'states':c['states'][:-1],
            'gamma_diagnostic':[0.,1.],'A_method':'W1_ONE_PHASE','head_elision':True,
            'forced_P_or_C_suffixes':True,'deployed_variant':'P_REFERENCE_UNIT',
            'automatic_single_job_GPUh':4,'cumulative_cap_GPUh':77.89524658965853,
            'forecast_complete_GPUh':9.,'training':True}
        for k,v in mutations.items():
            bad=copy.deepcopy(c);bad[k]=v
            try:validate_contract(bad)
            except ValueError:pass
            else:raise AssertionError('Changed N1 scope accepted: '+k)
        assert not torch.cuda.is_initialized() and not (a.stage/'NEVER_CREATED').exists()
        write(a.stage/'production-CPU-result.json',{'status':'MATH_N1_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',
            'exit_code':0,'GPU_submissions':0,'CUDA_initialized':False,'ledger_written':False,
            'config_sha256':sha(a.stage/CONFIG),'registration_sha256':sha(a.stage/'registration.json'),
            'sampling_CPU_sha256':sha(a.stage/'sampling-CPU-result.json'),'scope_counts':COUNTS,
            'source_revision':reg['source_revision'],'mutations_refused':list(mutations),'input_evidence':evidence})
        print('MATH_N1_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU');return
    proof=json.loads((a.stage/'production-CPU-result.json').read_text())
    assert proof['status']=='MATH_N1_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['config_sha256']==sha(a.stage/CONFIG) and proof['registration_sha256']==sha(a.stage/'registration.json')
    assert os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid==UUID and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    output=a.project/'outputs'/RUN;assert output.is_dir() and not (output/'runner.json').exists()
    state={'status':'INITIALIZING_N1_SINGLE_RESIDENT_MODEL','pid':os.getpid(),
        'source_revision':a.source_revision,'config_sha256':sha(a.stage/CONFIG),'scope_counts':COUNTS,
        'runs':[],'started_unix':time.time()}
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
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint();versions=[(p,p._version) for p in net.parameters()]
        state['status']='N1_FULL4_NATURAL_PARENTS12_POINTS_RUNNING';save()
        for i,sample in enumerate(samples):
            row={'scene':sample.name,'status':'RUNNING','started_unix':time.time()};state['runs'].append(row);save()
            initial.restore();assert initial.fingerprint()==fp;verify_shared_eval(net,mode)
            directory=output/str(i);holder={};points=[s for s in c['states'] if s['scene']==sample.name]
            def writer(step,payload):
                directory.mkdir(exist_ok=True);path=directory/('point-'+str(step)+'.pt');assert not path.exists()
                torch.save(payload,path)
                return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'tensor_sha256':tree_digest(payload)}
            with natural_diagnostic_install(clean,scheduler,points,c['checkpoint_reserves'],writer,holder):
                result=clean.execute(inf,sample,'KEEP_A_P',runtime=a.project/'runtime',wc=wc,rf=rf,
                    settings=settings,calibration=calibration,specs=specs[STRATEGY],inference_module=im,
                    output=directory/'parent',expected_shape=old['expected_real_shape'],audit=True)
            owner=holder['owner'];records=owner.records
            final=result.pop('final_latent',None);guided=result.pop('guided',None)
            assert final is not None and guided is not None and len(guided)==36
            path=directory/'parent-vectors.pt';torch.save({'final_latent':final,'guided':guided},path)
            bind=index['original_parent_bindings'][sample.name]
            row.update(result,executed_strategy=STRATEGY,diagnostic_points=records,
                actual_pair_computations=owner.actual_pair_computations,
                final_latent_sha256=tree_digest(final),old_final_equal=tree_digest(final)==bind['final_latent_sha256'],
                old_actions_equal=result['actions']==bind['actions'],
                old_all36_guided_equal=[tree_digest(g) for g in guided]==original_guided[sample.name]['guided_sha256'],
                parent_vectors={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size},
                ended_unix=time.time());save()
            assert row['status']=='COMPLETE' and len(records)==3 and owner.actual_pair_computations==45
            assert row['old_final_equal'] and row['old_actions_equal'] and row['old_all36_guided_equal'],'Diagnostic changed original parent; retain full scope'
            assert all(p._version==v for p,v in versions)
        initial.restore();assert initial.fingerprint()==fp
        assert sum(r['actual_pair_computations'] for r in state['runs'])==180
        state['status']='N1_COMPLETE4_PARENTS12_POINTS180_PAIRS_RAW_AUDIT_PENDING';save()
    except BaseException as e:
        state.update(status='N1_TECHNICAL_STOP_FULL12_SCOPE_RETAINED',error_type=type(e).__name__,error=str(e));save();raise
    finally:
        cleanup_environment();state['ended_unix']=time.time();save()
if __name__=='__main__':main()
