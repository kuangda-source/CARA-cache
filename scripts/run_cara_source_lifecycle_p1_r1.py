"""Full P1 on the admitted original Cosmos runner; host CPU queue owns FIT scoring."""
import argparse
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--source-revision',required=True)
    parser.add_argument('--gpu-uuid',required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from run_cara_budget_calibration_r1 import validate_runner_handoff
    from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import validate,RUNNER,MODE,SETUP,GEOMETRY,WEIGHTS
    from wcomr.cara_source_lifecycle_fit_broker_r1 import Client
    from wcomr.cara_source_lifecycle_p1_clock_r1 import OriginalAllocationClock
    from wcomr.cara_budget_search_journal_r1 import create_record,read_record as read
    from wcomr.gpu_budget_pool_v2 import atomic_json,sha
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.wc73_exclusive_r1 import runner_context_gate

    card,launch,profile,context,spec,quote=validate(args.project,args.stage)
    output=args.project/'outputs'/launch['run_id']
    storage=storage_for(args.stage)
    storage.check()
    if (storage.output!=output or storage.config['image_bytes']!=profile['storage']['output_image_bytes']
            or storage.config['journal_bytes']!=profile['storage']['independent_journal_bytes']
            or any(storage.config[k]<profile['storage'][k] for k in
                ('minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes'))
            or launch['source_revision']!=args.source_revision
            or launch['gpu_uuid']!=args.gpu_uuid or os.environ['CUDA_VISIBLE_DEVICES']!=args.gpu_uuid):
        raise ValueError('Original P1 source/device and private whole-card storage required')
    command=[sys.executable,str(args.stage/RUNNER),'--project',str(args.project),'--stage',str(args.stage),
             '--source-revision',args.source_revision,'--gpu-uuid',args.gpu_uuid]
    identity=validate_runner_handoff(args.stage,launch,context['launch_sha256'],command)
    create_record(output/'P1-model-runner-intent.json',dict(identity=identity,context=context,no_replay=True))
    if (os.environ['WC_SUPERVISOR_PID']!=str(os.getppid())
            or Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()
               !=(args.project/'.sync/gpu-locks'/(args.gpu_uuid+'.lock')).resolve()):
        raise ValueError('Original P1 supervisor and inherited device lease required')
    clock=OriginalAllocationClock(read(args.stage/'guardian.json'),context)
    score=Client(spec)
    runner_context_gate(args.project,args.stage,args.gpu_uuid)
    import torch
    from wcomr.cara_source_lifecycle_p1_runner_r1 import collect_loaded
    torch.set_num_threads(2)
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as inference_module
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from wcomr.runtime_config import install_core_inference_registration
    setup=SetupArguments(**{**read(args.stage/SETUP),'keep_going':True,'worldcache_enabled':True,'output_dir':str(output)})
    if setup.disable_guardrails or setup.use_torch_compile or setup.offload_diffusion_model:
        raise ValueError('Original guarded P1 model setup required')
    samples={r['name']:InferenceArguments(**{k:v for k,v in r.items() if k!='partition'}) for r in card['inputs']}
    state=dict(status='P1_MODEL_LOADING',started_unix=time.time(),scope_sha256=card['scope_sha256'],
        source_revision=launch['source_revision'],identity=identity,CPU_fixture_only=False,scientific_accepted=False)
    target=output/'P1-model-runner.json'
    atomic_json(target,state)
    try:
        init_environment();init_output_dir(output,profile=False)
        install_core_inference_registration(setup.model,setup.experiment)
        started=time.monotonic()
        inference=inference_module.Inference(setup)
        torch.cuda.synchronize()
        state['load_seconds']=time.monotonic()-started
        if (torch.__version__!='2.7.1+cu128' or len(inference.pipe.model.net.blocks)!=28
                or list(torch.cuda.get_device_capability())!=profile['hosts']['two_card']['capability']):
            raise ValueError('Pinned P1 runtime/model/device differs')
        common=dict(runtime=args.project/'runtime',wc=wc,rf=rf,inference_module=inference_module,
                    expected_shape=read(args.stage/GEOMETRY)['expected_real_shape'])
        result,evidence=collect_loaded(inference=inference,samples=samples,card=card,common=common,context=context,
            output=output/'algorithm',storage=storage,mode_types=read(args.stage/MODE)['module_types'],
            snapshot_limits=profile['snapshot_limits'],weights=read(args.stage/WEIGHTS)['weights'],score=score,
            elapsed_seconds=clock,query_bounds=quote['fair_search_query_bounds'],create=True,allow_new=True)
        if (result.get('failure') is not None
                or result['status']!='P1_ALGORITHM_COMPLETE_PENDING_ORIGINAL_RELEASE_SETTLEMENT_AND_SCIENCE'
                or len(result['semantic_positions'])!=146):
            raise RuntimeError('Original whole P1 algorithm failed; retain complete denominator and no retry')
        state.update(status='P1_FULL146_ALGORITHM_COMPLETE_PENDING_RELEASE',loaded_model_checks=evidence,
            semantic_positions=146,complete_semantic_positions=result['complete_semantic_positions'],
            algorithm_summary_sha256=sha(output/'algorithm/algorithm-summary.json'))
    except BaseException as error:
        state.update(status='P1_MODEL_RUNNER_FAILED',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        try:cleanup_environment()
        except BaseException as error:
            state.update(status='P1_MODEL_CLEANUP_FAILED',cleanup_error_type=type(error).__name__,cleanup_error=str(error))
            raise
        finally:
            state['ended_unix']=time.time();atomic_json(target,state)


if __name__=='__main__':main()
