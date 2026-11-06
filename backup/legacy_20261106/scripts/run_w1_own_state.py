"""Three original scalar trajectories with score-only same-state teachers."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback


def build_arguments(old,config,destination,arguments):
    params=dict(old['setup']);params['output_dir']=str(destination)
    setup=arguments.SetupArguments(**params)
    requests=[old['cases'][i]['sample'] for i in config['sample_indices']]
    samples=[arguments.InferenceArguments(**r) for r in requests]
    if (json.loads(setup.model_dump_json())!=params
            or [json.loads(s.model_dump_json()) for s in samples]!=requests
            or [s.name for s in samples]!=config['sample_names']):
        raise ValueError('Only output directory may change original typed setup/requests')
    return setup,samples


def validate(project,stage,runtime,output):
    sys.path.insert(0,str(stage/'src'))
    from wcomr.own_state_execution import validate_stage,read
    c=read(stage/'own-state-config.json')
    if output.resolve()!=(project/'outputs'/c['run_id']/'diagnostic').resolve():raise ValueError('Output identity differs')
    result=validate_stage(project,stage,runtime,c,selected=c['GPU_execution_selected'])
    spec=importlib.util.spec_from_file_location('own_state_asset_binding',stage/'scripts/run_wc_s0_profile.py')
    assets=importlib.util.module_from_spec(spec);spec.loader.exec_module(assets)
    assets.validate(project,stage,runtime)  # CPU source/file audit only.
    return c,result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['project','stage','runtime','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--gpu-uuid');p.add_argument('--source-revision')
    p.add_argument('--validate-only',action='store_true');p.add_argument('--draft-check',action='store_true')
    a=p.parse_args();sys.path.insert(0,str(a.stage/'src'))
    from wcomr.own_state_execution import validate_config,read,sha
    c=read(a.stage/'own-state-config.json')
    if a.draft_check:print(json.dumps(validate_config(c)));return
    c,validation=validate(a.project,a.stage,a.runtime,a.output)
    if a.validate_only:print(json.dumps(validation));return
    validate_config(c,selected=True)
    fd=int(os.environ['W1_OWN_STATE_LOCK_FD']);parent=int(os.environ['W1_OWN_STATE_SUPERVISOR_PID'])
    held=os.fstat(fd);lock=(a.project/'.sync/f1.lock').stat()
    if ((held.st_dev,held.st_ino)!=(lock.st_dev,lock.st_ino) or not Path('/proc/'+str(parent)).exists()
            or a.gpu_uuid!=c['gpu_uuid'] or os.environ.get('CUDA_VISIBLE_DEVICES')!=a.gpu_uuid
            or Path.cwd().resolve()!=a.runtime.resolve() or len(a.source_revision or '')!=40):
        raise ValueError('Inherited project lock, supervisor, UUID, runtime and source required')
    sys.path[:0]=[str(a.stage/'src'),str(a.runtime),str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
    os.environ.update(HF_HUB_CACHE=str(a.project/'hfhub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    a.output.mkdir(parents=True,exist_ok=False)
    state={'run_card':c['card'],'scope':c,'source_revision':a.source_revision,'pid':os.getpid(),
        'supervisor_pid':parent,'gpu_uuid':a.gpu_uuid,'started_unix':time.time(),'status':'INITIALIZING',
        'cases':[],'planned_scenes':3,'planned_observations':12,'independent_confirmation':False,
        'clean_speed_measurement':False,'teacher_written_to_deployment':False,'CUDA_initialized':False}
    def save():
        path=a.output/'receipt.tmp';path.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');path.replace(a.output/'receipt.json')
    cleanup=None;save()
    try:
        import torch
        from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
        init_environment();cleanup=cleanup_environment;init_output_dir(a.output,profile=False)
        import cosmos_predict2.config as arguments
        import cosmos_predict2.inference as inference_module
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from wcomr.runtime_config import install_core_inference_registration
        from wcomr.decoder_policy import backend_flags
        from wcomr.own_state_sampling import run_batch
        old=read(a.stage/'reports/w1_replay_r1_runner.json');flags=old['flags']
        for attr,key in [('enabled','cudnn_enabled'),('benchmark','cudnn_benchmark'),
            ('deterministic','cudnn_deterministic'),('allow_tf32','cudnn_allow_tf32')]:setattr(torch.backends.cudnn,attr,flags[key])
        torch.backends.cuda.matmul.allow_tf32=flags['matmul_allow_tf32'];torch.use_deterministic_algorithms(flags['deterministic_algorithms'])
        if (torch.__version__!='2.7.1+cu128' or torch.cuda.get_device_capability()!=(8,6)
                or sha(wc.__file__)!=old['cache_source_sha256']):raise ValueError('Torch/GPU/pinned cache source differs')
        setup,samples=build_arguments(old,c,a.output,arguments)
        state['setup']=json.loads(setup.model_dump_json());state['backend_flags']=flags
        state['registration']=install_core_inference_registration(setup.model,setup.experiment)
        started=time.perf_counter();inference=inference_module.Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.perf_counter()-started;state['CUDA_initialized']=torch.cuda.is_initialized()
        net=inference.pipe.model.net;net.eval()
        if len(net.blocks)!=28 or net.probe_depth!=2 or backend_flags()!=flags:raise ValueError('Original eager28/probe2/eval/backend differs')
        for block in net.blocks:
            attn=block.self_attn
            if (attn.backend,attn.n_heads,attn.head_dim,type(attn.attn_op).__name__)!=('minimal_a2a',16,128,'MinimalA2AAttnOp'):
                raise ValueError('Original dense attention differs')
        def peak(mode):
            if mode=='reset':torch.cuda.reset_peak_memory_stats();return
            return {'allocated_bytes':torch.cuda.max_memory_allocated(),'reserved_bytes':torch.cuda.max_memory_reserved()}
        save()
        run_batch(inference,samples,old,c,state=state,save=save,output=a.output/'artifacts',
            inference_module=inference_module,original=wc.worldcache_mini_train_dit_forward,
            synchronize=torch.cuda.synchronize,peak=peak)
    except BaseException as error:
        state.update(status='TECH_BLOCKED_THREE_SCENE_SCOPE_PRESERVED',error_type=type(error).__name__,error=str(error))
        traceback.print_exc();raise
    finally:
        if cleanup:
            try:cleanup()
            except Exception as error:state.update(cleanup_error=str(error),status='TECH_BLOCKED_CLEANUP')
        state.update(ended_unix=time.time());state['process_wall_seconds']=state['ended_unix']-state['started_unix'];save()


if __name__=='__main__':main()
