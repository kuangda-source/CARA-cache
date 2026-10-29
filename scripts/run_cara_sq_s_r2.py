"""One separately admitted full S model load and complete original matrix."""
import argparse
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import time


def run(args):
    from wcomr.sq_s_execution_r2 import validate,require
    from wcomr.sq_s_spec_r2 import RUN
    from wcomr.sq_s_stage_r2 import verify_lease_fd
    from wcomr.sq_control_storage_r1 import storage_for
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.wc73_exclusive_r1 import runner_context_gate
    bundle,registration,authority=validate(args.project,args.stage)
    storage=storage_for(args.stage);storage.check();output=storage.output
    require(output==args.project/'outputs'/RUN and registration['source_revision']==args.source_revision
        and authority['gpu_uuid']==args.gpu_uuid==os.environ['CUDA_VISIBLE_DEVICES']
        and os.environ['WC_SUPERVISOR_PID']==str(os.getppid()),'Original S runner/source/parent differs')
    require(not (output/'S-runner.json').exists() and not (output/'S-collection.json').exists(),
        'Original S model attempt exists; recover without retry')
    verify_lease_fd(args.project,args.gpu_uuid,os.environ['WC_LOCK_FD'])
    context=runner_context_gate(args.project,args.stage,args.gpu_uuid)
    import torch
    from cosmos_predict2 import config, inference
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    import cosmos_oss.init as initialize
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.policy_generator_r1.interval_grammar import Profile
    from wcomr.sq_s_model_entry_r1 import execute
    from wcomr.sq_s_data_terminal_r2 import check_result
    profile=bundle['execution_profile'];upper=bundle['upper']
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(profile['CUDA_allocator_fraction_max'])
    def forbidden_download(*args,**kwargs):raise RuntimeError('S model downloads are forbidden')
    torch.hub.download_url_to_file=forbidden_download
    identity={key:authority[key] for key in ('run_id','host','gpu_uuid','launch_id','source_revision','scope_sha256')}
    atomic_json(output/'S-runner.json',dict(identity,status='S_ORIGINAL_MODEL_ENTRY_STARTING',started_unix=time.time()))
    profile_values=dict(upper['profile'])
    for key in ('protected_dense','alpha_candidates'):profile_values[key]=tuple(profile_values[key])
    bundle.update(profile=Profile(**profile_values),store_limits=dict(
        maximum_total_bytes=profile['streaming_tensor_artifact_cap_GiB']*2**30,
        maximum_file_bytes=profile['output_file_GiB_max']*2**30,
        minimum_free_bytes=profile['minimum_output_free_MiB']*2**20))
    admitted=dict(authority,scope_sha256=upper['scope_sha256'])
    api=SimpleNamespace(config=config,inference=inference,wc=wc,rf=rf,initialize=initialize,
        install_registration=install_core_inference_registration)
    def save_health(value):
        storage.check();atomic_json(output/'S-health.json',dict(value,**identity))
    def save_result(value):
        value.update(identity,actual_CUDA=bool(context.is_cuda),
            workspace_memory=dict(peak_allocated=torch.cuda.max_memory_allocated(),
                peak_reserved=torch.cuda.max_memory_reserved(),deployment_memory_measured=False))
        check_result(value,upper,bundle['physical'],identity_sha256=bundle['identity']['identity_sha256'],
            resource_contract_sha256=bundle['resource_contract']['contract_sha256'],
            expected_shape=bundle['identity']['expected_real_shape'],new_output_root=str(output/'paths'))
        atomic_json(output/'S-collection.json',value)
    torch.cuda.reset_peak_memory_stats()
    result=execute(bundle=bundle,runtime=args.project/'runtime',output=output,storage=storage,
        context=admitted,runtime_api=api,save_health=save_health,
        save_matrix=lambda value:atomic_json(output/'S-matrix.json',value),save_result=save_result)
    atomic_json(output/'S-runner.json',dict(identity,status=result['status'],ended_unix=time.time(),
        actual_scientific_labels_accepted=False,GPU_released=False,central_cost_settled=False))
    require(context is not None,'Original S context disappeared before final receipts')
    return result


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('source-revision','gpu-uuid'):p.add_argument('--'+key,required=True)
    args=p.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    run(args)


if __name__=='__main__':main()
