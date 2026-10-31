"""Collect one separately admitted endpoint allocation; no dispatch, scores or freeze."""
import argparse
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--source-revision',required=True);parser.add_argument('--gpu-uuid',required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.project/'runtime'),
                  str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from run_cara_budget_calibration_r1 import validate_runner_handoff
    from wcomr.cara_s_endpoint_runner_binding_r1 import validate,RUNNER,MODE,RA,SETUP,GEOMETRY
    from wcomr.cara_s_endpoint_runner_r1 import collect_loaded
    from wcomr.cara_budget_search_journal_r1 import create_record,read_record as read
    from wcomr.policy_price_terminal_r1 import require
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.wc73_exclusive_r1 import runner_context_gate
    card,bound,proposal,launch,profile,context=validate(args.project,args.stage)
    output=args.project/'outputs'/launch['run_id'];storage=storage_for(args.stage);storage.check()
    require(storage.output==output and storage.config['image_bytes']==profile['storage']['output_image_bytes']
            and storage.config['journal_bytes']==profile['storage']['independent_journal_bytes']
            and all(storage.config[k]>=profile['storage'][k] for k in
                    ('minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes')),
            'Original private endpoint output required')
    require(launch['source_revision']==args.source_revision and launch['gpu_uuid']==args.gpu_uuid==os.environ['CUDA_VISIBLE_DEVICES'],
            'Original endpoint runner identity differs')
    expected=[sys.executable,str(args.stage/RUNNER),'--project',str(args.project),'--stage',str(args.stage),
              '--source-revision',args.source_revision,'--gpu-uuid',args.gpu_uuid]
    identity=validate_runner_handoff(args.stage,launch,context['launch_sha256'],expected)
    create_record(output/'endpoint-model-runner-intent.json',dict(identity=identity,context=context,no_replay=True))
    require(os.environ['WC_SUPERVISOR_PID']==str(os.getppid()),'Original endpoint supervisor required')
    require(Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==(args.project/'.sync/gpu-locks'/(args.gpu_uuid+'.lock')).resolve(),
            'Inherited original endpoint device lease required')
    cuda_context=runner_context_gate(args.project,args.stage,args.gpu_uuid)
    import torch
    torch.set_num_threads(2)
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as inference_module
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from wcomr.runtime_config import install_core_inference_registration
    setup=SetupArguments(**{**read(args.stage/SETUP),'keep_going':True,'worldcache_enabled':True,'output_dir':str(output)})
    require(not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model,
            'Original guarded endpoint model setup required')
    samples={r['name']:InferenceArguments(**{k:v for k,v in r.items() if k!='partition'}) for r in card['inputs']}
    state=dict(status='MODEL_LOADING',started_unix=time.time(),scope_sha256=card['scope_sha256'],
        source_revision=launch['source_revision'],identity=identity,CPU_fixture_only=False,scientific_accepted=False)
    atomic_json(output/'endpoint-model-runner.json',state)
    init_environment()
    try:
        init_output_dir(output,profile=False);install_core_inference_registration(setup.model,setup.experiment)
        started=time.monotonic();inference=inference_module.Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.monotonic()-started
        require(torch.__version__=='2.7.1+cu128' and len(inference.pipe.model.net.blocks)==28
                and list(torch.cuda.get_device_capability())==profile['hosts']['two_card']['capability'],
                'Pinned endpoint runtime/model/device differs')
        common=dict(runtime=args.project/'runtime',wc=wc,rf=rf,inference_module=inference_module,
                    expected_shape=read(args.stage/GEOMETRY)['expected_real_shape'])
        collection,evidence=collect_loaded(inference,samples,card,bound,common,read(args.stage/RA),'two_card',output,
                                           context,storage,read(args.stage/MODE)['module_types'])
        state.update(status='COMPLETE_ENDPOINT_COLLECTION_PENDING_RELEASE',loaded_model_checks=evidence,
                     complete_paths=len(collection['rows']))
    except BaseException as error:
        state.update(status='ENDPOINT_MODEL_RUNNER_FAILED',error_type=type(error).__name__,error=str(error));raise
    finally:
        try:cleanup_environment()
        except BaseException as error:
            state.update(status='ENDPOINT_MODEL_CLEANUP_FAILED',cleanup_error_type=type(error).__name__,cleanup_error=str(error));raise
        finally:
            state['ended_unix']=time.time();atomic_json(output/'endpoint-model-runner.json',state)
    require(cuda_context is not None,'Original endpoint CUDA context disappeared')


if __name__=='__main__':main()
