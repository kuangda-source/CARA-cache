#!/usr/bin/env python3
"""Complete64 guarded real video run, with its own CPU and execution contract."""
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
    for name in ('project','stage'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--cpu-check',action='store_true')
    parser.add_argument('--source-revision');parser.add_argument('--gpu-uuid')
    args=parser.parse_args()
    os.environ.update(HF_HUB_CACHE=str(args.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    if args.cpu_check:
        os.environ['CUDA_VISIBLE_DEVICES']=''
        import torch
        def forbidden(*a,**kw):raise RuntimeError('Full64 production CPU forbids CUDA/downloads/model execution')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from wcomr.current_birth_real_production_r1 import (
        validate,validate_contract,validate_selected,binding,REQUESTS,RUN,COUNTS)
    c,inputs=validate(args.project,args.stage)
    calibration,specs,references,evidence=inputs
    if args.cpu_check:
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,name):raise RuntimeError('Full64 CPU forbids Triton execution: '+name)
        triton.runtime.driver.active=ImportOnlyDriver()
        from cosmos_predict2.config import InferenceArguments
        import cosmos_predict2.inference as inference_module
        from cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit import MinimalV1LVGDiT
        from wcomr import source_aware_current_birth_sampling_r2 as sampler
        from wcomr import source_aware_current_birth_sampling_r1 as original
        from wcomr.source_aware_working_epoch_sampling_r1 import valid_P_interval
        from huggingface_hub import constants
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common.core import GUARDRAIL1_CHECKPOINT_DIR
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.blocklist.blocklist import Blocklist
        assert Path(constants.HF_HUB_CACHE).resolve()==(args.project/'hfhub').resolve()
        assert Path(GUARDRAIL1_CHECKPOINT_DIR).resolve()==(args.project/'hfhub/models--nvidia--Cosmos-Guardrail1/snapshots/d6d4bfa899a71454a700907664f3e88f503950cf').resolve()
        assert Blocklist().blocklist_words
        assert Path(inspect.getsourcefile(MinimalV1LVGDiT.forward)).resolve()==(args.project/'runtime/cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py').resolve()
        for name in ('run_batch','verify_batch','audit_vectors','CurrentBirthSamplingOwner','CurrentBirthDeployment'):
            assert getattr(sampler,name) is getattr(original,name)
        assert sampler.valid_P_interval is valid_P_interval
        samples=InferenceArguments.from_files([args.stage/REQUESTS]);assert len(samples)==4
        assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['preregistration']['requests']))
        from types import SimpleNamespace
        empty=SimpleNamespace(pipe=SimpleNamespace(offload_diffusion_model=False),rank0=True,
            text_guardrail_runner=None,video_guardrail_runner=None)
        refused=[]
        for strategy in sampler.STRATEGIES:
            try:
                sampler.run_batch(empty,samples,None,{},state={},save=forbidden,output=args.stage/'never-created',
                    inference_module=inference_module,contexts=[('invalid',)]*4,mode_setup={},runtime=args.project/'runtime',
                    rf_module=None,config={'sample_names':[s.name for s in samples],'run_id':RUN},
                    calibration=calibration,policy_specs=specs[strategy])
            except ValueError as error:
                assert str(error)=='Complete guarded four-request guided-W1 calibration batch required'
            else:raise AssertionError('Guardrail-less full64 production entered model execution')
        mutations={'card':'OLD_CARD','run_id':'old_run','scope_counts':{'complete_paths':32},
            'strategies':[sampler.STRATEGIES[0]],'methods':['SOURCE_RA','CPD'],'repetitions':['first','second'],
            'branch_order':['negative_prompt','conditional'],'guided_weights':[7,-6],
            'state_steps':[12,30,35],'current_P_birth_rule':'OLD_BIRTH_PLUS_DRIFT','fixed_P_steps':[12,30],
            'P_mode':'RANDOM_075','P_layers':[4,10],'P_ratio':.75,'P_block_size':64,
            'shared_A_phase_boundary':26,'shared_A_strength':[1.,1.],'maximum_consecutive_P':3,
            'borrowed_D_drift_ratio':0.,'P_future_drift_empirically_calibrated':True,
            'RA_calibration_fingerprint':'TOY','RA_threshold':.1,
            'reference_policy':'OTHER_SEED','teacher_calls':1,'training':True,
            'boundary_or_alpha_sweep':True,'clean_latency_claim':True,'independent_confirmation_claim':True}
        for key,value in mutations.items():
            bad=copy.deepcopy(c);bad['preregistration'][key]=value
            try:validate_contract(bad,args.stage)
            except ValueError:refused.append(key)
            else:raise AssertionError('Full64 production accepted altered registered scope: '+key)
        for key,value in [('seed',4),('guidance',6),('num_steps',24),('name','human_199_seed3')]:
            bad=copy.deepcopy(c);bad['preregistration']['requests'][0][key]=value
            try:validate_contract(bad,args.stage)
            except ValueError:refused.append('request_'+key)
            else:raise AssertionError('Full64 production accepted altered request: '+key)
        if c['GPU_execution_selected']:validate_selected(c,args.project,args.stage)
        assert Path(inference_module.__file__).resolve()==(args.project/'runtime/cosmos_predict2/inference.py').resolve()
        assert not torch.cuda.is_initialized()
        print(json.dumps({'status':'CURRENT_BIRTH_FULL64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',
            'config_binding_sha256':binding(c),'payload_sha256':c['payload_sha256'],
            'registered_scope':COUNTS,'production_contract_mutation_refusals':refused,
            'actual_guardrail_Blocklist_four_CAL_and_original_forward_origin_checked':True,
            'compatibility_wrapper_execution_callables_identical':True,'guardrail_less_entry_refused_both_strategies':True,
            'actual_input_evidence':evidence,'complete_method_parameter_sets':16,
            'CUDA_initialized':False,'GPU_submissions':0}));return
    validate_selected(c,args.project,args.stage)
    if (os.environ.get('CUDA_VISIBLE_DEVICES')!=args.gpu_uuid or args.gpu_uuid!=c['gpu_uuid']
        or os.environ.get('WC_SUPERVISOR_PID')!=str(os.getppid()) or not os.environ.get('WC_LOCK_FD','').isdigit()):
        raise ValueError('Live selected complete64 supervisor and shared lock required')
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as inference_module
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.source_aware_current_birth_sampling_r2 import run_batch,verify_batch,STRATEGIES
    from wcomr.mid_coverage import tree_digest
    from wcomr.current_birth_real_inputs_r1 import sha
    import torch
    output=args.project/'outputs'/RUN/'diagnostic';output.mkdir(parents=True,exist_ok=False)
    state={'status':'INITIALIZING','pid':os.getpid(),'source_revision':args.source_revision,'run_id':RUN,
        'started_unix':time.time(),'config':c,'planned_scope':COUNTS,
        'model_context':'Cosmos-Predict2.5-2B:'+sha(args.project/'configs/f1_setup.json'),
        'input_evidence':evidence,'matched_Native_metadata':references,
        'batches':{s:{'status':'PENDING_COMPLETE_SCOPE_NOT_REPLACED'} for s in STRATEGIES},'completed_strategies':[]}
    def save():
        tmp=output/'receipt.tmp';tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(output/'receipt.json')
    save();init_environment();init_output_dir(output,profile=False)
    try:
        params=json.loads((args.project/'configs/f1_setup.json').read_text());params.update(keep_going=False,worldcache_enabled=True,output_dir=str(output))
        setup=SetupArguments(**params);install_core_inference_registration(setup.model,setup.experiment)
        samples=InferenceArguments.from_files([args.stage/REQUESTS]);started=time.perf_counter()
        inference=inference_module.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-started
        net=inference.pipe.model.net;contract=json.loads((args.stage/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
        modes=establish_shared_eval(net,contract['module_types']);verify_shared_eval(net,modes)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
        for block in net.blocks:assert block.self_attn.backend=='minimal_a2a' and type(block.self_attn.attn_op).__name__=='MinimalA2AAttnOp'
        settings=c['historical_wc_settings'];assert all(getattr(net,k)==v for k,v in settings.items())
        contexts=[(RUN+':'+sample.name,state['model_context'],tree_digest(sample.model_dump(mode='json'))) for sample in samples]
        local={'sample_names':[s.name for s in samples],'run_id':RUN,'logical_copy_cap_bytes':c['logical_copy_cap_bytes'],
            'workspace_reserve_bytes':c['workspace_reserve_bytes'],'paired_prefix_reserve_bytes':c['paired_prefix_reserve_bytes'],
            'expected_components':c['expected_real_components'],'expected_shape':c['expected_real_shape']}
        for strategy in STRATEGIES:
            directory=output/strategy;directory.mkdir(exist_ok=False)
            state['status']='COMPLETE64_STRATEGY_RUNNING';state['current_strategy']=strategy;save()
            run_batch(inference,samples,wc,settings,state=state['batches'][strategy],save=save,output=directory,
                inference_module=inference_module,contexts=contexts,mode_setup=modes,runtime=args.project/'runtime',
                config=local,rf_module=rf,calibration=calibration,policy_specs=specs[strategy])
            state['batches'][strategy]['current_birth_whole_verification']=verify_batch(state['batches'][strategy])
            state['completed_strategies'].append(strategy);save()
        state['status']='CURRENT_BIRTH_REAL_FULL64_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT';save()
    except BaseException as error:
        state.update(status='COMPLETE64_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
    finally:
        cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
