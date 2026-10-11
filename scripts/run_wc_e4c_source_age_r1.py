#!/usr/bin/env python3
"""One registered arm and one actual model lifetime; four children are supervised."""
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
    p.add_argument('--cpu-check',action='store_true');p.add_argument('--arm')
    p.add_argument('--source-revision');p.add_argument('--gpu-uuid');args=p.parse_args()
    os.environ.update(HF_HUB_CACHE=str(args.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    if args.cpu_check:os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    def forbidden(*a,**k):raise RuntimeError('E4C production CPU forbids CUDA/downloads/model execution')
    if args.cpu_check:
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,n):raise RuntimeError('E4C production CPU forbids Triton execution: '+n)
        triton.runtime.driver.active=ImportOnlyDriver()
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from wcomr.e4c_source_age_production_r1 import (RUN,CONFIG,STRATEGY,validate,validate_contract,
        validate_selected,binding,sha,write,protected_capacity_failure)
    from wcomr.e4c_matched_source_age_sampling_r1 import compile_batch,verify_batch
    from wcomr.e1_memory_diagnostic_sampling_r1 import memory
    c,old,inputs=validate(args.project,args.stage);calibration,specs,references,evidence=inputs
    scope=json.loads((args.stage/c['scope_ref']).read_text())
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as inference_module
    samples=InferenceArguments.from_files([args.stage/'e4c-requests.jsonl'])
    if len(samples)!=2 or not all(all(s.model_dump(mode='json')[k]==v for k,v in r.items())
            for s,r in zip(samples,c['requests'])):raise ValueError('Actual E4C requests differ')
    if args.cpu_check:
        from cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit import MinimalV1LVGDiT
        from huggingface_hub import constants
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.blocklist.blocklist import Blocklist
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common.core import GUARDRAIL1_CHECKPOINT_DIR
        assert Path(constants.HF_HUB_CACHE).resolve()==(args.project/'hfhub').resolve()
        assert Path(GUARDRAIL1_CHECKPOINT_DIR).resolve()==(args.project/'hfhub/models--nvidia--Cosmos-Guardrail1/snapshots/d6d4bfa899a71454a700907664f3e88f503950cf').resolve()
        assert Blocklist().blocklist_words
        assert Path(inspect.getsourcefile(MinimalV1LVGDiT.forward)).resolve()==(args.project/'runtime/cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py').resolve()
        from types import SimpleNamespace
        empty=SimpleNamespace(pipe=SimpleNamespace(offload_diffusion_model=False),rank0=True,
            text_guardrail_runner=None,video_guardrail_runner=None)
        run,proof=compile_batch(scope,calibration=calibration,policy_specs=specs[STRATEGY])
        try:
            run(empty,samples,None,{},state={},save=forbidden,output=args.stage/'never-created',
                inference_module=inference_module,contexts=[(RUN+':'+s.name,'CPU_VALID_MODEL','CPU_VALID_CONDITION') for s in samples],
                mode_setup={},runtime=args.project/'runtime',rf_module=None,config={'sample_names':[s.name for s in samples],'run_id':RUN})
        except ValueError as error:assert str(error)=='Complete guarded E4c four-parent diagnostic batch required'
        else:raise AssertionError('Guardrail-less E4c entry reached model')
        mutations={'card':'OLD_FULL64','automatic_single_job_GPUh':4,'forecast_complete_GPUh':8.1,
            'training':True,'human_review':True,'empty_cache_or_gate_bypass':True,'continue_after_failure':'CONTINUE'}
        refused=[]
        for key,v in mutations.items():
            bad=copy.deepcopy(c);bad[key]=v
            try:validate_contract(bad,args.stage)
            except (ValueError,KeyError):refused.append(key)
            else:raise AssertionError('E4c admitted altered registered scope: '+key)
        assert not torch.cuda.is_initialized()
        print(json.dumps({'status':'E4C_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU',
            'config_binding_sha256':binding(c),'payload_sha256':c['payload_sha256'],'scope_counts':c['scope_counts'],
            'actual_original_input_evidence':evidence,'registered_derivation':proof,'contract_mutation_refusals':refused,
            'guardrail_less_entry_refused':True,'CUDA_initialized':False,'GPU_submissions':0}));return
    validate_selected(c,args.stage)
    if args.arm is not None:raise ValueError('E4c is one complete model job, without arm selection')
    if (os.environ.get('CUDA_VISIBLE_DEVICES')!=args.gpu_uuid or args.gpu_uuid!=c['gpu_uuid']
            or os.environ.get('WC_SUPERVISOR_PID')!=str(os.getppid()) or not os.environ.get('WC_LOCK_FD','').isdigit()):
        raise ValueError('Original E4C supervisor and shared lock required')
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.mid_coverage import tree_digest
    output=args.project/'outputs'/RUN/'model';output.mkdir(exist_ok=False)
    state={'status':'E4C_ARM_INITIALIZING','pid':os.getpid(),'source_revision':args.source_revision,'run_id':RUN,
        'scope':scope,'planned_paths':4,'config_sha256':sha(args.stage/CONFIG),'started_unix':time.time(),
        'model_context':'Cosmos-Predict2.5-2B:'+sha(args.project/'configs/f1_setup.json'),
        'input_evidence':evidence,'matched_Native_metadata':references,'batch':{}}
    save=lambda:write(output/'receipt.json',state)
    observer=(output/'memory-observer.jsonl').open('x')
    def sink(row):observer.write(json.dumps({'unix':time.time(),**row},allow_nan=False)+'\n');observer.flush()
    save();init_environment();init_output_dir(output,profile=False)
    try:
        params=json.loads((args.project/'configs/f1_setup.json').read_text())
        params.update(keep_going=False,worldcache_enabled=True,output_dir=str(output))
        setup=SetupArguments(**params);install_core_inference_registration(setup.model,setup.experiment)
        names=scope['sample_names'];chosen=samples
        started=time.perf_counter();inference=inference_module.Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-started
        net=inference.pipe.model.net;contract=json.loads((args.stage/c['model_mode_contract_ref']).read_text())
        modes=establish_shared_eval(net,contract['module_types']);verify_shared_eval(net,modes)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
        for block in net.blocks:assert block.self_attn.backend=='minimal_a2a' and type(block.self_attn.attn_op).__name__=='MinimalA2AAttnOp'
        settings=old['historical_wc_settings'];assert all(getattr(net,k)==v for k,v in settings.items())
        contexts=[(RUN+':'+s.name,state['model_context'],tree_digest(s.model_dump(mode='json'))) for s in chosen]
        local={'sample_names':names,'run_id':RUN,**c['checkpoint_reserves'],
            'expected_components':old['expected_real_components'],'expected_shape':old['expected_real_shape']}
        run,proof=compile_batch(scope,calibration=calibration,policy_specs=specs[STRATEGY])
        state.update(status='E4C_ARM_COMPLETE_SCOPE_RUNNING',derivation=proof,after_load_memory=memory());save()
        run(inference,chosen,wc,settings,state=state['batch'],save=save,output=output,
            inference_module=inference_module,contexts=contexts,mode_setup=modes,runtime=args.project/'runtime',
            config=local,rf_module=rf)
        state['whole_arm_verification']=verify_batch(state['batch'],scope)
        state['status']='E4C_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT';save()
    except BaseException as error:
        protected=protected_capacity_failure(type(error).__name__,str(error))
        state.update(status='E4C_ARM_PROTECTED_CAPACITY_STOP' if protected else 'E4C_ARM_TECH_FAILED_SCOPE_RETAINED',
            error_type=type(error).__name__,error=str(error),protected_capacity_failure=protected);save();raise
    finally:
        cleanup_environment();observer.close();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
