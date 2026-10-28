"""One authorized saved-state Q1 CUDA cut, with exact original-output gates."""
import argparse
import gc
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--gpu-uuid',required=True)
    args=p.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    from wcomr.sq_q1_execution_r1 import validate,read,require
    from wcomr.sq_q1_spec_r1 import RUN,ASSETS,WEIGHT,CHECKPOINT_SHA,MANIFEST_SHA,PROFILE
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.sq_q1_stage_r1 import verify_lease_fd
    from wcomr.wc73_exclusive_r1 import runner_context_gate
    scope,registration,authority=validate(args.project,args.stage)
    storage=storage_for(args.stage);storage.check();output=storage.output
    require(output==args.project/'outputs'/RUN,'Wrong Q1 output storage')
    require(registration['source_revision']==args.source_revision
            and authority['gpu_uuid']==args.gpu_uuid==os.environ['CUDA_VISIBLE_DEVICES'],
            'Q1 runner source/UUID differs')
    require(os.environ['WC_SUPERVISOR_PID']==str(os.getppid()),'Wrong original Q1 supervisor')
    verify_lease_fd(args.project,args.gpu_uuid,os.environ['WC_LOCK_FD'])
    context=runner_context_gate(args.project,args.stage,args.gpu_uuid)
    import torch
    from wcomr.sq_q1_assets_r1 import B1Reader,file_sha,real_geometry
    from wcomr.sq_q1_readout_r1 import cosmos_condition_schema
    from wcomr.sq_q1_collection_r1 import collect_saved_q1
    from wcomr.sq_readout_subgraph_r1 import build_kernel,original_backend_policy
    profile=read(args.stage/PROFILE)
    require(torch.__version__=='2.7.1+cu128' and torch.cuda.device_count()==1
            and list(torch.cuda.get_device_capability())==profile['hosts'][authority['host']]['capability'],
            'Pinned Q1 torch/sole-device capability differs')
    torch.set_num_threads(2)
    torch.cuda.set_per_process_memory_fraction(profile['CUDA_allocator_fraction_max'])
    def forbidden_download(*args,**kwargs):
        raise RuntimeError('Q1 downloads are forbidden')
    torch.hub.download_url_to_file=forbidden_download
    state=dict(status='Q1_SOURCE_AND_ASSET_CHECKS',run_id=RUN,launch_id=authority['launch_id'],
        source_revision=registration['source_revision'],scope_sha256=authority['scope_sha256'],started_unix=time.time())
    def save_health(value):
        storage.check()
        atomic_json(output/'Q1-health.json',dict(value,run_id=RUN,launch_id=authority['launch_id']))
    atomic_json(output/'Q1-runner.json',state)
    reader=B1Reader(args.project/ASSETS)
    reader.verify_files(lambda done,total:save_health(dict(status='VERIFY_ORIGINAL_B1',verified_files=done,total_files=total)))
    checkpoint=args.project/WEIGHT
    require(file_sha(checkpoint)==CHECKPOINT_SHA,'Original checkpoint SHA differs')
    schema=cosmos_condition_schema()
    weights=torch.load(checkpoint,map_location='cpu',weights_only=True,mmap=True)
    kernel,source_proof=build_kernel(args.project/'runtime',weights,device='cuda')
    del weights;gc.collect()
    versions=[(p,p._version) for p in kernel.net.parameters()]
    def load(record):
        value=reader.load(record);real_geometry(value);return value
    torch.cuda.reset_peak_memory_stats()
    with original_backend_policy(args.project/'runtime') as backend:
        result=collect_saved_q1(kernel,reader.records,load,schema,device='cuda',
            max_copy_bytes=profile['private_input_logical_cap_GiB']*2**30,
            save_health=save_health,synchronize=torch.cuda.synchronize)
        require(all(p._version==version for p,version in versions),'Q1 changed original head weights')
        result.update(CPU_fixture=False,actual_CUDA=bool(context.is_cuda),
            run_id=RUN,launch_id=authority['launch_id'],host=authority['host'],gpu_uuid=args.gpu_uuid,
            source_revision=registration['source_revision'],scope_sha256=authority['scope_sha256'],
            input_evidence=dict(checkpoint_sha256=CHECKPOINT_SHA,manifest_sha256=MANIFEST_SHA,
                original_B1_files_verified=len(reader.verified),condition_schema='ACTUAL_RUNTIME_MODULE'),
            source_proof=source_proof,backend=backend,
            workspace_memory=dict(peak_allocated=torch.cuda.max_memory_allocated(),
                peak_reserved=torch.cuda.max_memory_reserved(),deployment_memory_measured=False),
            GPU_released=False,central_cost_settled=False,ended_unix=time.time())
        atomic_json(output/'Q1-collection.json',result)
    state.update(status=result['status'],ended_unix=time.time())
    atomic_json(output/'Q1-runner.json',state)
    require(context is not None,'Original Q1 context disappeared before receipt writes')


if __name__=='__main__':main()
