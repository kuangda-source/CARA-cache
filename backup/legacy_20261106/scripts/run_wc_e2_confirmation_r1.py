#!/usr/bin/env python3
"""Complete E2 confirmation, timing and parity card; no submission on import."""
import argparse
import copy
import inspect
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    parser.add_argument('--cpu-check',action='store_true')
    parser.add_argument('--source-revision');parser.add_argument('--gpu-uuid')
    args=parser.parse_args()
    os.environ.update(HF_HUB_CACHE=str(args.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    if args.cpu_check:
        os.environ['CUDA_VISIBLE_DEVICES']=''
        import torch
        def forbidden(*a,**k):raise RuntimeError('E2 actual production CPU forbids CUDA, downloads and weights')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.load=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,n):raise RuntimeError('E2 CPU forbids Triton execution: '+n)
        triton.runtime.driver.active=ImportOnlyDriver()
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from wcomr.e2_confirmation_production_r1 import validate,validate_contract,validate_selected,binding,REQUESTS,RUN
    c,inputs,rows,calibration,threshold=validate(args.project,args.stage)
    from cosmos_predict2.config import InferenceArguments
    import cosmos_predict2.inference as inference_module
    from cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit import MinimalV1LVGDiT
    from wcomr.e2_confirmation_timing_sampling_r1 import execute_path,run_matrix,verify_matrix
    samples=InferenceArguments.from_files([args.stage/REQUESTS])
    if len(samples)!=10 or not all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,rows)):
        raise ValueError('Actual ten parsed E2 production requests differ')
    if args.cpu_check:
        from huggingface_hub import constants
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common.core import GUARDRAIL1_CHECKPOINT_DIR
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.blocklist.blocklist import Blocklist
        assert Path(constants.HF_HUB_CACHE).resolve()==(args.project/'hfhub').resolve()
        assert Path(GUARDRAIL1_CHECKPOINT_DIR).resolve()==(args.project/'hfhub/models--nvidia--Cosmos-Guardrail1/snapshots/d6d4bfa899a71454a700907664f3e88f503950cf').resolve()
        assert Blocklist().blocklist_words
        assert Path(inspect.getsourcefile(MinimalV1LVGDiT.forward)).resolve()==(args.project/'runtime/cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py').resolve()
        from types import SimpleNamespace
        empty=SimpleNamespace(pipe=SimpleNamespace(offload_diffusion_model=False),rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        for method in ('NATIVE','WC','RA','W1_ONE_PHASE','BETA1_ONE_PHASE'):
            try:
                execute_path(empty,samples[0],None,{},row={'method':method,'status':'NOT_STARTED'},save=forbidden,
                    output=args.stage/'never-created',inference_module=inference_module,context=('E2','CPU','condition'),
                    mode_setup={},runtime=args.project/'runtime',config=c,rf_module=None,calibration=calibration,
                    threshold=threshold['threshold'],sampling_policy=c['sampling_protocol'],mode='AUDIT')
            except ValueError as error:assert str(error)=='Fresh frozen E2 method, mode, request and guarded pipeline required'
            else:raise AssertionError('Guardrail-less E2 entry executed model work')
        mutations={'card':'OLD_CARD','scope_counts':{'complete_actual_GPU_paths':72},'RA_threshold':.1,
            'guided_weights':[7,-6],'A_phase_boundary':26,'A_phase_strength':[1,1],
            'original_A_extra_heads_elided':True,'teacher_calls':1,'training':True,'automatic_single_job_GPUh':4,
            'expected_real_shape':[1,16,24,54,95],'forecast_complete_GPUh':1.,'confirmation_accepted':True}
        refused=[]
        for key,value in mutations.items():
            bad=copy.deepcopy(c);bad[key]=value
            try:validate_contract(bad,args.stage)
            except ValueError:refused.append(key)
            else:raise AssertionError('Altered E2 production scope accepted: '+key)
        if c['GPU_execution_selected']:validate_selected(c,args.project,args.stage)
        assert Path(inference_module.__file__).resolve()==(args.project/'runtime/cosmos_predict2/inference.py').resolve()
        assert not torch.cuda.is_initialized()
        print(json.dumps({'status':'E2_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU','config_binding_sha256':binding(c),
            'payload_sha256':c['payload_sha256'],'scope_counts':c['scope_counts'],
            'actual_ten_requests_parsed':True,'actual_guardrail_resource_and_Native_origin_checked':True,
            'five_guardrail_less_methods_refused':True,'contract_mutation_refusals':refused,
            'actual_real_prior_fingerprint':calibration.fingerprint,'actual_threshold':threshold,
            'CUDA_initialized':False,'GPU_submissions':0}));return
    validate_selected(c,args.project,args.stage)
    if (os.environ.get('CUDA_VISIBLE_DEVICES')!=args.gpu_uuid or args.gpu_uuid!=c['gpu_uuid']
            or os.environ.get('WC_SUPERVISOR_PID')!=str(os.getppid()) or not os.environ.get('WC_LOCK_FD','').isdigit()):
        raise ValueError('E2 live selected supervisor, GPU and shared lock required')
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from cosmos_predict2.config import SetupArguments
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.cfg_ra_calibration_production import sha
    import torch
    output=args.project/'outputs'/RUN/'diagnostic';output.mkdir(parents=True,exist_ok=False)
    state={'status':'E2_INITIALIZING','pid':os.getpid(),'source_revision':args.source_revision,'run_id':RUN,
        'started_unix':time.time(),'config':c,'model_context':'Cosmos-Predict2.5-2B:'+sha(args.project/'configs/f1_setup.json'),
        'matrix':{},'planned_scope':c['scope_counts']}
    def save():
        temp=output/'receipt.tmp';temp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');temp.replace(output/'receipt.json')
    save();init_environment();init_output_dir(output,profile=False)
    try:
        params=json.loads((args.project/'configs/f1_setup.json').read_text());params.update(keep_going=False,worldcache_enabled=True,output_dir=str(output))
        setup=SetupArguments(**params);install_core_inference_registration(setup.model,setup.experiment)
        start=time.perf_counter();inference=inference_module.Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-start
        net=inference.pipe.model.net;contract=json.loads((args.stage/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
        modes=establish_shared_eval(net,contract['module_types']);verify_shared_eval(net,modes)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
        assert all(block.self_attn.backend=='minimal_a2a' and type(block.self_attn.attn_op).__name__=='MinimalA2AAttnOp' for block in net.blocks)
        settings=c['historical_wc_settings'];assert all(getattr(net,k)==v for k,v in settings.items())
        local={'run_id':RUN,'model_context':state['model_context'],'expected_shape':c['expected_real_shape']}
        state['status']='E2_COMPLETE76_RUNNING';save()
        run_matrix(inference,{s.name:s for s in samples},wc,settings,state=state['matrix'],save=save,output=output,
            inference_module=inference_module,mode_setup=modes,runtime=args.project/'runtime',config=local,
            rf_module=rf,calibration=calibration,threshold=threshold['threshold'],sampling_policy=c['sampling_protocol'],inputs=inputs)
        state['whole_matrix_verification']=verify_matrix(state['matrix'],inputs)
        state['status']='E2_GPU_COMPLETE_REQUIRES_RAW_AUDIT_AND_93FRAME_CPU_SCORE';save()
    except BaseException as error:
        state.update(status='E2_GPU_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
    finally:
        cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
