"""GPU-hidden complete S collection topology, using declared CPU stand-ins."""
import argparse
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'scripts')]


def main():
    p=argparse.ArgumentParser()
    for name in ('assets','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('profile','scope','manifest-sha256'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S collection CPU evidence')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('S collection fixture must hide GPU devices')
    started,cpu=time.monotonic(),time.process_time()
    import torch
    def forbidden(*args,**kwargs):raise RuntimeError('S CPU fixture cannot initialize CUDA, load weights or download')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    torch.set_num_threads(2);os.nice(10)
    runtime=ROOT/'cache/runtime'
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('S CPU refuses Triton execution: '+name)
    triton.runtime.driver.active=Driver()
    import transformers.utils as transformers_utils
    from transformers.utils import import_utils
    saved=(transformers_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    transformers_utils.is_flash_attn_2_available=import_utils.is_flash_attn_2_available=lambda:True
    torch.cuda.current_device=lambda:0
    try:
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:
        transformers_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=saved
    from check_sq_s_collection_cpu_r1 import run
    scope=json.loads((ROOT/args.scope).read_text())
    fixture=run(runtime,ROOT/'S-collection-CPU-artifacts');rows=fixture['checks']
    if len(rows)!=2 or {r['flow'] for r in rows}!={False,True} or any(r['status']!='PASS' for r in rows):
        raise ValueError('Both flow settings of the complete S CPU topology required')
    for row in rows:
        for actual,expected in (('complete_CPU_paths','CPU_paths_per_flow'),
                ('CPU_fixture_moment_rows','CPU_fixture_moment_rows_per_flow'),
                ('extra_Dense_teacher_pairs','extra_Dense_teacher_pairs_per_flow'),
                ('extra_C_readout_pairs','extra_C_readout_pairs_per_flow')):
            if row[actual]!=scope[expected]:raise ValueError('S CPU topology denominator differs: '+actual)
        if (len(row['raw_CPU_states'])!=scope['raw_CPU_states_per_flow'] or len(row['OFF_ON_controls'])!=4
                or row['Dense_hidden_replay_heads']!=0 or row['S_labels_collected']!=0):
            raise ValueError('S CPU raw/control scope changed')
    if sum(r['complete_CPU_paths'] for r in rows)!=scope['complete_CPU_paths'] or torch.cuda.is_initialized():
        raise ValueError('S CPU full cohort or hidden-GPU boundary failed')
    result=dict(status='SQ_S_COLLECTION_CPU_TOPOLOGY_PASS_NOT_REAL_MODEL_OR_STORAGE_ACCEPTANCE',
        profile=args.profile,scope=scope,rows=rows,fixture_status=fixture['status'],
        upstream_sha256=fixture['upstream_sha256'],CPU_wall_seconds=time.monotonic()-started,
        CPU_seconds=time.process_time()-cpu,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        CPU_import_adapter='ACCEPTED_PG_IMPORT_ONLY_FLASH_PROBES_AND_CURRENT_DEVICE',
        CPU_import_probes_restored_before_sampling=True,model_weight_loads_forbidden=True,
        CUDA_initialized=False,actual_Cosmos_weights=False,real_generated_video=False,
        streaming_raw_storage_accepted=False,complete_S_card_accepted=False,S_labels_collected=0,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(result['status'])


if __name__=='__main__':main()
