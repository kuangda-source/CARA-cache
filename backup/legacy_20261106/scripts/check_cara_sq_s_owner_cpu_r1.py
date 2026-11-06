"""GPU-hidden S owner/physical roundtrip component in the registered runtime."""
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
    if args.output.exists():raise FileExistsError('Preserve original S owner CPU evidence')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('S owner component must run with GPU devices hidden')
    started,cpu=time.monotonic(),time.process_time()
    import torch
    def forbidden(*args,**kwargs):raise RuntimeError('S CPU component cannot initialize CUDA or download')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    torch.set_num_threads(2);os.nice(10)
    # Reuse the accepted PG CPU import adapter. Only import-time capability
    # assertions are adapted; the actual sampler runs after all three restore.
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
    from check_sq_s_owner_roundtrip_cpu_r1 import run
    scope=json.loads((ROOT/args.scope).read_text())
    fixture=run(runtime,ROOT/'S-owner-CPU-artifacts')
    selected=fixture['checks']
    if (len(selected)!=2 or {row['flow'] for row in selected}!={False,True}
            or any(row['status']!='PASS' or 'parents' not in row for row in selected)
            or sum(row['complete_CPU_paths'] for row in selected)!=scope['complete_CPU_paths']
            or sum(len(row['events']) for row in selected)!=scope['expected_checked_boundaries']):
        raise ValueError('Complete frozen S owner CPU cohort missing')
    if torch.cuda.is_initialized():raise RuntimeError('S owner CPU component initialized CUDA')
    result=dict(status='SQ_S_OWNER_CPU_PASS_STANDINS_NOT_COMPLETE_COLLECTOR',profile=args.profile,
        scope=scope,rows=selected,CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        fixture_status=fixture['status'],upstream_sha256=fixture['upstream_sha256'],
        CPU_import_adapter='ACCEPTED_PG_IMPORT_ONLY_FLASH_PROBES_AND_CURRENT_DEVICE',
        CPU_import_probes_restored_before_sampling=True,model_weight_loads_forbidden=True,
        CUDA_initialized=False,actual_Cosmos_weights=False,real_generated_video=False,
        complete_S_collector_accepted=False,S_labels_collected=0,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(result['status'])


if __name__=='__main__':main()
