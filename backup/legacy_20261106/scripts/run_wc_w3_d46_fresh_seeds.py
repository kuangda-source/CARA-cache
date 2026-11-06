#!/usr/bin/env python3
"""Complete registered two-seed card; CPU preparation cannot authorize GPU."""
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
    config=json.loads((stage/'seed-config.json').read_text());sys.path.insert(0,str(stage/'src'))
    from wcomr.rv0_d46_seed_scope import validate_scope,read_original
    validate_scope(config['preregistration'],read_original(project))
    for name,h in config['payload_sha256'].items():
        if sha(stage/name)!=h:raise ValueError('New registered source changed: '+name)
    base=project/config['base_stage']
    for name,h in config['base_payload_sha256'].items():
        if sha(base/name)!=h:raise ValueError('Frozen base source changed: '+name)
    for name,h in config['project_input_sha256'].items():
        if sha(project/name)!=h:raise ValueError('Original model/sample protocol changed: '+name)
    if json.loads((stage/'seed-requests.jsonl').read_text().splitlines()[0])!=config['preregistration']['requests'][0]:
        raise ValueError('First seed parser source changed')
    if [json.loads(x) for x in (stage/'seed-requests.jsonl').read_text().splitlines()]!=config['preregistration']['requests']:
        raise ValueError('Complete two seed requests changed')
    assets=module(base/'scripts/run_wc_s0_profile.py','d46_shared_asset_validator');assets.validate(project,base,project/'runtime')
    execution_run=config.get('execution_run_id',config['preregistration']['run_id'])
    if execution_run != config['preregistration']['run_id']:
        recovery=config.get('technical_recovery')
        if execution_run not in ('wc-w3-d46-fresh-seeds-r2','wc-w3-d46-fresh-seeds-r3') or not recovery:
            raise ValueError('Unknown independent technical execution identity')
        receipt=stage/recovery['manifest_ref']
        if sha(receipt)!=recovery['manifest_sha256']:
            raise ValueError('Technical recovery provenance changed')
        restored=json.loads(receipt.read_text())
        if (restored['scientific_card']!=config['preregistration']['card']
                or restored['execution_run_id']!=execution_run
                or restored['complete_scope']!=config['preregistration']['scope_counts']
                or not restored['prior_failure_all_wall_retained']):
            raise ValueError('Technical recovery changed approved scientific scope')
        prior=project/restored['prior_failure_supervisor_ref']
        if sha(prior)!=restored['prior_failure_supervisor_sha256'] or json.loads(prior.read_text())['exit_code']!=1:
            raise ValueError('Original initialization failure provenance changed')
    return config,base


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
        # Transformer Engine asks for a Triton benchmarker while importing.
        # Match the existing CPU origin check: imports only, no kernel execution.
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,name):raise RuntimeError('CPU check forbids Triton driver access: '+name)
        triton.runtime.driver.active=ImportOnlyDriver()
        from cosmos_predict2.config import InferenceArguments
        from wcomr.rv0_d46_seed_portfolio import run_portfolio
        from wcomr.rv0_d46_seed_causal import run_d46_seed_batch
        from wcomr.w1_native_reference_sampling import run_native_request,official_native_forward
        from huggingface_hub import constants as hf_constants
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common.core import GUARDRAIL1_CHECKPOINT_DIR
        from cosmos_predict2._src.imaginaire.auxiliary.guardrail.blocklist.blocklist import Blocklist
        expected_cache=args.project/'hfhub'
        expected_guard=expected_cache/'models--nvidia--Cosmos-Guardrail1/snapshots/d6d4bfa899a71454a700907664f3e88f503950cf'
        assert Path(hf_constants.HF_HUB_CACHE).resolve()==expected_cache.resolve()
        assert Path(GUARDRAIL1_CHECKPOINT_DIR).resolve()==expected_guard.resolve()
        assert (expected_guard/'blocklist/custom').is_dir()
        blocklist=Blocklist()
        assert blocklist.blocklist_words
        parsed=InferenceArguments.from_files([args.stage/'seed-requests.jsonl'])
        assert len(parsed)==2
        for sample,request in zip(parsed,c['preregistration']['requests']):
            actual=sample.model_dump(mode='json')
            assert all(actual[k]==v for k,v in request.items())
        # Exercise the real Native function's delayed imports before its first
        # production precondition; no model construction or generation occurs.
        from types import SimpleNamespace
        from wcomr.decoder_policy import backend_flags
        empty=SimpleNamespace(pipe=SimpleNamespace(model=SimpleNamespace(net=SimpleNamespace())))
        try:
            run_native_request(empty,parsed[0],state={'status':'CPU_DELAYED_IMPORT_CHECK'},save=forbidden,
                output=args.stage/'never-created-native-cpu-output',inference_module=None,
                sampling_policy=c['sampling_protocol'],expected_flags=backend_flags(),synchronize=forbidden)
        except ValueError as error:
            assert str(error)=='Fresh complete35 Native reference/eval/backend identity differs'
        else:raise AssertionError('CPU Native entry should stop before generation')
        import ast
        pending=['rv0_d46_seed_causal','rv0_d46_seed_portfolio','rv0_d46_seed_evaluation','w1_native_reference_sampling']
        visited=set()
        while pending:
            name=pending.pop()
            if name in visited:continue
            visited.add(name);source=args.stage/'src/wcomr'/Path(name.replace('.','/')+'.py')
            assert source.is_file(), 'Missing transitive staged source: '+name
            for node in ast.walk(ast.parse(source.read_text())):
                if isinstance(node,ast.ImportFrom) and node.level==1 and node.module:
                    pending.append(node.module)
        assert not torch.cuda.is_initialized()
        print(json.dumps({'status':'D46_FRESH_SEEDS_ACTUAL_PRODUCTION_SOURCE_ASSETS_PARSER_IMPORT_CPU_PASS_NOT_GPU',
            'CUDA_initialized':False,'GPU_submissions':0,'parsed_seed_names':[s.name for s in parsed],
            'native_callable':run_native_request.__name__,'causal_callable':run_d46_seed_batch.__name__,
            'portfolio_callable':run_portfolio.__name__,'source_files':len(c['payload_sha256']),
            'project_HF_cache_and_actual_CPU_Blocklist_verified':True,
            'real_Native_delayed_imports_checked':True,'transitive_local_source_count':len(visited),
            'execution_run_id':c.get('execution_run_id',c['preregistration']['run_id'])}));return
    authority=c.get('execution_scope_authority')
    if not authority or c.get('GPU_execution_selected') is not True:
        raise ValueError('This complete >2GPUh card needs a new direct execution exception')
    approval=args.stage/authority['approval_ref']
    if sha(approval)!=authority['approval_sha256'] or json.loads(approval.read_text())['approved_card']!=c['preregistration']['card']:
        raise ValueError('New concrete whole-card exception identity differs')
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
    from wcomr.rv0_d46_seed_portfolio import run_portfolio
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
        samples=InferenceArguments.from_files([args.stage/'seed-requests.jsonl'])
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
            mode_setup=modes,runtime=args.project/'runtime',scope=c['preregistration'],sampling_policy=sampling)
    finally:
        cleanup_environment();state['ended_unix']=time.time();save()


if __name__=='__main__':main()
