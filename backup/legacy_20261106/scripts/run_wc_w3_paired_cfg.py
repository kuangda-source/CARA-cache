#!/usr/bin/env python3
"""H-T38: one existing seed2, one WC parent, eight suffixes, no new Native."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def validate(project,stage):
    sys.path.insert(0,str(stage/'src'))
    from wcomr.rv0_paired_cfg_production import validate as checked
    return checked(project,stage)


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu-check',action='store_true');p.add_argument('--source-revision');p.add_argument('--gpu-uuid')
    args=p.parse_args()
    os.environ['HF_HUB_CACHE']=str(args.project/'hfhub')
    c,base=validate(args.project,args.stage)
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime'),str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    if args.cpu_check:
        os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        import torch
        def forbidden(*a,**k):raise RuntimeError('CPU production check forbids CUDA/downloads')
        torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,name):raise RuntimeError('CPU check forbids Triton driver access: '+name)
        triton.runtime.driver.active=ImportOnlyDriver()
        from cosmos_predict2.config import InferenceArguments
        import cosmos_predict2.inference as inference_module
        from wcomr.rv0_paired_cfg_production import run_portfolio,validate_contract,binding,validate_selected
        from wcomr.rv0_paired_cfg_causal import run_paired_cfg_batch
        from huggingface_hub import constants as hf_constants
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common.core import GUARDRAIL1_CHECKPOINT_DIR
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.blocklist.blocklist import Blocklist
        expected_cache=args.project/'hfhub'
        expected_guard=expected_cache/'models--nvidia--Cosmos-Guardrail1/snapshots/d6d4bfa899a71454a700907664f3e88f503950cf'
        assert Path(hf_constants.HF_HUB_CACHE).resolve()==expected_cache.resolve()
        assert Path(GUARDRAIL1_CHECKPOINT_DIR).resolve()==expected_guard.resolve() and (expected_guard/'blocklist/custom').is_dir()
        blocklist=Blocklist();assert blocklist.blocklist_words
        parsed=InferenceArguments.from_files([args.stage/'paired-request.jsonl']);assert len(parsed)==1
        assert all(parsed[0].model_dump(mode='json')[k]==v for k,v in c['preregistration']['same_existing_request'].items())
        from types import SimpleNamespace
        empty=SimpleNamespace(pipe=SimpleNamespace(offload_diffusion_model=False),rank0=True,text_guardrail_runner=None,video_guardrail_runner=None)
        try:
            run_paired_cfg_batch(empty,parsed,None,{},state={},save=forbidden,output=args.stage/'never-created',
                inference_module=inference_module,contexts=[('early',)],mode_setup={},runtime=args.project/'runtime',
                config={'sample_names':[parsed[0].name],'target_calls':[46],'paired_full_calls':[45,46],'maximum_age_solver_steps':32})
        except ValueError as error:assert str(error)=='Independent small single-process guarded C/D scope differs'
        else:raise AssertionError('Real delayed paired imports must stop before model/generation')
        import ast,copy
        pending=['rv0_paired_cfg_production','rv0_paired_cfg_causal','rv0_paired_cfg_evaluation'];visited=set()
        while pending:
            name=pending.pop()
            if name in visited:continue
            visited.add(name);source=args.stage/'src/wcomr'/Path(name.replace('.','/')+'.py')
            assert source.is_file(),'Missing transitive paired source: '+name
            for node in ast.walk(ast.parse(source.read_text())):
                if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:pending.append(node.module)
        refused=[]
        mutations=[('seed',3),('snapshot_step',23),('snapshot_after_call',46),('single_full_calls',[45]),('paired_full_calls',[46]),
            ('main_comparisons',['PAIRED_vs_SINGLE']),('scope_counts',{'WC_parents':1}),('remaining_policy','PARENT_MASK')]
        for key,value in mutations:
            bad=copy.deepcopy(c);bad['preregistration'][key]=value
            try:validate_contract(bad,args.stage)
            except ValueError:refused.append(key)
            else:raise AssertionError('Production contract accepted '+key)
        for mod in [inference_module]:
            assert Path(mod.__file__).resolve()==(args.project/'runtime/cosmos_predict2/inference.py').resolve()
        if c['GPU_execution_selected']:validate_selected(c,args.project,args.stage)
        assert not torch.cuda.is_initialized()
        print(json.dumps({'status':'PAIRED_CFG_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU','CUDA_initialized':False,'GPU_submissions':0,
            'config_binding_sha256':binding(c),'payload_sha256':c['payload_sha256'],'parsed_request':parsed[0].model_dump(mode='json'),
            'project_HF_cache_and_actual_CPU_Blocklist_verified':True,'real_paired_delayed_imports_checked':True,
            'transitive_local_source_count':len(visited),'production_contract_mutation_refusals':refused}));return
    from wcomr.rv0_paired_cfg_production import validate_selected
    validate_selected(c,args.project,args.stage)
    if (os.environ.get('CUDA_VISIBLE_DEVICES')!=args.gpu_uuid or c['gpu_uuid']!=args.gpu_uuid
            or os.environ.get('WC_SUPERVISOR_PID')!=str(os.getppid()) or not os.environ.get('WC_LOCK_FD','').isdigit()):
        raise ValueError('Direct live supervisor, shared lock and selected UUID required')
    os.fstat(int(os.environ['WC_LOCK_FD']))
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as inference_module
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.rv0_paired_cfg_production import run_portfolio,read_prior
    import torch
    execution_run=c.get('execution_run_id',c['preregistration']['run_id'])
    output=args.project/'outputs'/execution_run/'diagnostic';output.mkdir(parents=True,exist_ok=False)
    state={'status':'INITIALIZING','pid':os.getpid(),'source_revision':args.source_revision,'config':c,
        'run_id':execution_run,'scientific_run_id':c['preregistration']['run_id'],
        'started_unix':time.time(),'model_context':'Cosmos-Predict2.5-2B:'+sha(args.project/'configs/f1_setup.json'),'cases':[]}
    def save():
        tmp=output/'receipt.tmp';tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(output/'receipt.json')
    save();init_environment();init_output_dir(output,profile=False)
    try:
        params=json.loads((args.project/'configs/f1_setup.json').read_text())
        params.update(keep_going=False,worldcache_enabled=True,output_dir=str(output))
        setup=SetupArguments(**params);install_core_inference_registration(setup.model,setup.experiment)
        samples=InferenceArguments.from_files([args.stage/'paired-request.jsonl'])
        start=time.perf_counter();inference=inference_module.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.perf_counter()-start
        net=inference.pipe.model.net;mode=json.loads((base/'manifests/wc_h0_eval_mode_contract_20261003.json').read_text())
        modes=establish_shared_eval(net,mode['module_types']);verify_shared_eval(net,modes)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
        for block in net.blocks:assert block.self_attn.backend=='minimal_a2a' and type(block.self_attn.attn_op).__name__=='MinimalA2AAttnOp'
        old=json.loads((base/'onset-config.json').read_text());settings=old['historical_wc_settings']
        assert all(getattr(net,k)==v for k,v in settings.items())
        sampling=c['sampling_protocol']
        run_portfolio(inference,samples,wc,settings,state=state,save=save,output=output,inference_module=inference_module,
            mode_setup=modes,runtime=args.project/'runtime',scope=c['preregistration'],sampling_policy=sampling,prior_row=read_prior(args.stage)[1])
    finally:
        cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
