#!/usr/bin/env python3
"""MF-00 complete4 source-bound interface and guarded full pipeline."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time


def validate(project,stage):
    sys.path.insert(0,str(stage/'src'))
    from wcomr.cfg_mf00_interface_production import validate as check
    return check(project,stage)


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu-check',action='store_true');p.add_argument('--source-revision');p.add_argument('--gpu-uuid')
    args=p.parse_args();os.environ['HF_HUB_CACHE']=str(args.project/'hfhub')
    c,_=validate(args.project,args.stage)
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime'),str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    if args.cpu_check:
        os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        import torch
        def forbidden(*a,**kw):raise RuntimeError('Teacher production CPU forbids CUDA/downloads')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,name):raise RuntimeError('CPU forbids Triton execution: '+name)
        triton.runtime.driver.active=ImportOnlyDriver()
        from cosmos_predict2.config import InferenceArguments
        import cosmos_predict2.inference as inference_module
        from wcomr.cfg_mf00_interface_sampling import run_batch
        from wcomr.cfg_mf00_interface_production import binding,validate_contract,validate_selected
        from huggingface_hub import constants
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common.core import GUARDRAIL1_CHECKPOINT_DIR
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.blocklist.blocklist import Blocklist
        from wcomr.rv0_video_reader import probe_video
        assert Path(constants.HF_HUB_CACHE).resolve()==(args.project/'hfhub').resolve()
        assert Path(GUARDRAIL1_CHECKPOINT_DIR).resolve()==(args.project/'hfhub/models--nvidia--Cosmos-Guardrail1/snapshots/d6d4bfa899a71454a700907664f3e88f503950cf').resolve()
        assert Blocklist().blocklist_words
        samples=InferenceArguments.from_files([args.stage/'native-policy-requests.jsonl']);assert len(samples)==2
        assert all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,c['preregistration']['requests']))
        from types import SimpleNamespace
        empty=SimpleNamespace(pipe=SimpleNamespace(offload_diffusion_model=False),rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:
            run_batch(empty,samples,None,{},state={},save=forbidden,output=args.stage/'never-created',
                inference_module=inference_module,contexts=[('invalid',),('invalid',)],mode_setup={},runtime=args.project/'runtime',rf_module=None,
                config={'sample_names':[s.name for s in samples],'run_id':c['execution_run_id']})
        except ValueError as error:assert str(error)=='Complete guarded two-request native-policy batch required'
        else:raise AssertionError('Guardrail-less teacher production entered model execution')
        mutations={'card':'OLD_CARD','run_id':'old_run','requests':c['preregistration']['requests'][:1],
            'orders':['ORIGINAL'],'observers':['OFF','ON'],'repetitions':['first','second'],
            'state_steps':[13,21,33,36],'scope_counts':{'complete_paths':8},'measurement_space':'RAW_NET',
            'selector':'FORCE_JOINT_DD','new_policy_or_clean_latency_claim':True}
        refused=[]
        for key,value in mutations.items():
            bad=copy.deepcopy(c);bad['preregistration'][key]=value
            try:validate_contract(bad,args.stage)
            except ValueError:refused.append(key)
            else:raise AssertionError('Production accepted altered registered scope: '+key)
        for key,value in [('seed',4),('guidance',6),('num_steps',24),('name','human_199_seed3')]:
            bad=copy.deepcopy(c);bad['preregistration']['requests'][0][key]=value
            try:validate_contract(bad,args.stage)
            except ValueError:refused.append(key)
            else:raise AssertionError('Production accepted altered request: '+key)
        if c['GPU_execution_selected']:validate_selected(c,args.project,args.stage)
        assert Path(inference_module.__file__).resolve()==(args.project/'runtime/cosmos_predict2/inference.py').resolve()
        assert not torch.cuda.is_initialized()
        print(json.dumps({'status':'REAL_MF00_INTERFACE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU','config_binding_sha256':binding(c),'payload_sha256':c['payload_sha256'],
            'registered_scope':c['preregistration']['scope_counts'],'requests':[s.model_dump(mode='json') for s in samples],'production_contract_mutation_refusals':refused,
            'actual_guardrail_cache_Blocklist_and_derived_seed3_request':True,'actual_delayed_teacher_imports_checked':True,'CUDA_initialized':False,'GPU_submissions':0}));return
    from wcomr.cfg_mf00_interface_production import validate_selected,sha
    validate_selected(c,args.project,args.stage)
    if (os.environ.get('CUDA_VISIBLE_DEVICES')!=args.gpu_uuid or args.gpu_uuid!=c['gpu_uuid']
            or os.environ.get('WC_SUPERVISOR_PID')!=str(os.getppid()) or not os.environ.get('WC_LOCK_FD','').isdigit()):
        raise ValueError('Live selected teacher supervisor/shared lock required')
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as inference_module
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.cfg_mf00_interface_sampling import run_batch
    from wcomr.mid_coverage import tree_digest
    import torch
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    output=args.project/'outputs'/c['execution_run_id']/'diagnostic';output.mkdir(parents=True,exist_ok=False)
    state={'status':'INITIALIZING','pid':os.getpid(),'source_revision':args.source_revision,'run_id':c['execution_run_id'],'started_unix':time.time(),
        'config':c,'model_context':'Cosmos-Predict2.5-2B:'+sha(args.project/'configs/f1_setup.json'),'batch':{}}
    def save():
        tmp=output/'receipt.tmp';tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(output/'receipt.json')
    save();init_environment();init_output_dir(output,profile=False)
    try:
        params=json.loads((args.project/'configs/f1_setup.json').read_text());params.update(keep_going=False,worldcache_enabled=True,output_dir=str(output))
        setup=SetupArguments(**params);install_core_inference_registration(setup.model,setup.experiment)
        samples=InferenceArguments.from_files([args.stage/'native-policy-requests.jsonl'])
        started=time.perf_counter();inference=inference_module.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-started
        net=inference.pipe.model.net;contract=json.loads((args.stage/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
        modes=establish_shared_eval(net,contract['module_types']);verify_shared_eval(net,modes)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
        for block in net.blocks:assert block.self_attn.backend=='minimal_a2a' and type(block.self_attn.attn_op).__name__=='MinimalA2AAttnOp'
        settings=c['historical_wc_settings'];assert all(getattr(net,k)==v for k,v in settings.items())
        contexts=[(c['execution_run_id']+':'+sample.name,state['model_context'],tree_digest(sample.model_dump(mode='json'))) for sample in samples]
        local={'sample_names':[sample.name for sample in samples],'run_id':c['execution_run_id'],'logical_copy_cap_bytes':c['logical_copy_cap_bytes'],'workspace_reserve_bytes':c['workspace_reserve_bytes'],'paired_prefix_reserve_bytes':c['paired_prefix_reserve_bytes'],
               'expected_components':c['expected_real_components'],'expected_shape':c['expected_real_shape']}
        run_batch(inference,samples,wc,settings,state=state['batch'],save=save,output=output,inference_module=inference_module,
            contexts=contexts,mode_setup=modes,runtime=args.project/'runtime',config=local,rf_module=rf)
        state['ancillary_old_BASE_video_bridge']=None
        state['exposed_identity_implementation_comparison_not_CONF']=True
        state['historical_video_is_not_new_identity_control']=True
        state['historical_full_state_acceptance']=False
        state['status']='REAL_MF00_INTERFACE_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT';save()
    except BaseException as error:
        state.update(status='TEACHER_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
    finally:
        cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
