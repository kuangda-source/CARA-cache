#!/usr/bin/env python3
"""Exactly five missing Native35 references; full-video scoring follows release."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback


def build_arguments(draft, config, destination, argument_module):
    params = dict(draft['model_setup_from_original_W1'])
    params.update(worldcache_enabled=False, output_dir=str(destination))
    setup = argument_module.SetupArguments(**params)
    if json.loads(setup.model_dump_json()) != params:
        raise ValueError('Only output directory and cache disable may change original setup')
    rows = [draft['rows'][i] for i in config['sample_indices']]
    samples = [argument_module.InferenceArguments(**r['request']) for r in rows]
    if ([s.name for s in samples] != config['sample_names']
            or [json.loads(s.model_dump_json()) for s in samples] != [r['request'] for r in rows]):
        raise ValueError('Actual original five typed requests differ')
    return setup, samples, rows


def validate(project, stage, runtime, output):
    sys.path.insert(0, str(stage/'src'))
    from wcomr.w1_native_reference_execution import validate_stage
    config = json.loads((stage/'native-prod-config.json').read_text())
    if output.resolve() != (project/'outputs'/config['run_id']/'diagnostic').resolve():
        raise ValueError('Independent five-reference output identity differs')
    result = validate_stage(project, stage, runtime, config, selected=config['GPU_execution_selected'])
    spec = importlib.util.spec_from_file_location('native_assets', stage/'scripts/run_wc_s0_profile.py')
    assets = importlib.util.module_from_spec(spec); spec.loader.exec_module(assets)
    assets.validate(project, stage, runtime)  # Source/weights only; never its GPU entrypoint.
    return config, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','runtime','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--gpu-uuid'); parser.add_argument('--source-revision')
    parser.add_argument('--draft-check',action='store_true')
    parser.add_argument('--validate-only',action='store_true')
    args = parser.parse_args(); sys.path.insert(0,str(args.stage/'src'))
    from wcomr.w1_native_reference_execution import validate_config
    config = json.loads((args.stage/'native-prod-config.json').read_text())
    if args.draft_check:
        print(json.dumps(validate_config(config))); return
    config, validation = validate(args.project,args.stage,args.runtime,args.output)
    if args.validate_only:
        print(json.dumps(validation)); return
    validate_config(config,selected=True)
    fd = int(os.environ['W1_REFERENCE_LOCK_FD']); parent = int(os.environ['W1_REFERENCE_SUPERVISOR_PID'])
    held, original = os.fstat(fd), (args.project/'.sync/f1.lock').stat()
    if ((held.st_dev,held.st_ino) != (original.st_dev,original.st_ino)
            or parent<=0 or not Path('/proc/'+str(parent)).exists()
            or args.gpu_uuid != config['gpu_uuid'] or os.environ.get('CUDA_VISIBLE_DEVICES') != args.gpu_uuid
            or Path.cwd().resolve() != args.runtime.resolve()
            or type(args.source_revision) is not str or len(args.source_revision)!=40
            or any(c not in '0123456789abcdef' for c in args.source_revision)):
        raise ValueError('Independent selected UUID, inherited shared lock and source required')
    sys.path[:0]=[str(args.stage/'src'),str(args.runtime),str(args.runtime/'packages/cosmos-oss'),
                  str(args.runtime/'packages/cosmos-cuda')]
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ.update(HF_HUB_CACHE=str(args.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    state={'run_card':config['card'],'scope':config,'source_revision':args.source_revision,
           'pid':os.getpid(),'supervisor_pid':parent,'started_unix':time.time(),'gpu_uuid':args.gpu_uuid,
           'status':'INITIALIZING','cases':[],'planned_references':5,'original_denominator':[8,7,1],
           'original_rejected_sample_replaced':False,'independent_confirmation':False,'GPU_scoring':False,
           'CUDA_initialized':False,'clean_speed_measurement':False,'complete_video':False,'toy_fixture':False}
    def save():
        path=args.output/'receipt.tmp';path.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')
        path.replace(args.output/'receipt.json')
    save(); cleanup=None
    try:
        import torch
        from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
        init_environment();cleanup=cleanup_environment;init_output_dir(args.output,profile=False)
        import cosmos_predict2.config as arguments
        import cosmos_predict2.inference as inference_module
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.decoder_policy import backend_flags
        from wcomr.w1_native_reference_sampling import run_native_batch
        if torch.__version__!='2.7.1+cu128' or torch.cuda.get_device_capability()!=(8,6):
            raise ValueError('Actual Torch/sm86 differs')
        draft=json.loads((args.stage/'w1-reference-draft.json').read_text())
        replay=json.loads((args.stage/'reports/w1_replay_r1_runner.json').read_text())
        flags=replay['flags'];state['backend_flags']=flags;torch.backends.cudnn.enabled=flags['cudnn_enabled']
        torch.backends.cudnn.benchmark=flags['cudnn_benchmark'];torch.backends.cudnn.deterministic=flags['cudnn_deterministic']
        torch.backends.cudnn.allow_tf32=flags['cudnn_allow_tf32'];torch.backends.cuda.matmul.allow_tf32=flags['matmul_allow_tf32']
        torch.use_deterministic_algorithms(flags['deterministic_algorithms'])
        setup,samples,rows=build_arguments(draft,config,args.output,arguments)
        state['setup']=json.loads(setup.model_dump_json())
        state['registration']=install_core_inference_registration(setup.model,setup.experiment)
        started=time.perf_counter();inference=inference_module.Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-started;state['CUDA_initialized']=torch.cuda.is_initialized()
        net=inference.pipe.model.net;net.eval()
        state['network_class']=type(net).__module__+'.'+type(net).__name__
        if len(net.blocks)!=28 or inference.pipe.model.config.use_torch_compile or backend_flags()!=flags:
            raise ValueError('Original eager28 eval/backend differs')
        for block in net.blocks:
            a=block.self_attn
            if (a.backend,a.n_heads,a.head_dim,type(a.attn_op).__name__)!=('minimal_a2a',16,128,'MinimalA2AAttnOp'):
                raise ValueError('Original dense attention binding differs')
        save()
        run_native_batch(inference,samples,rows,state=state,save=save,output=args.output/'artifacts',
            inference_module=inference_module,sampling_policy=draft['sampling_protocol'],expected_flags=flags,
            synchronize=torch.cuda.synchronize)
    except BaseException as error:
        state.update(status='TECH_BLOCKED_FIVE_REFERENCE_DENOMINATOR_PRESERVED',
                     error_type=type(error).__name__,error=str(error));traceback.print_exc();raise
    finally:
        if cleanup is not None:
            try:cleanup()
            except Exception as error:state.update(cleanup_error=str(error),status='TECH_BLOCKED_NATIVE_CLEANUP')
        state['ended_unix']=time.time();state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()


if __name__=='__main__':main()
