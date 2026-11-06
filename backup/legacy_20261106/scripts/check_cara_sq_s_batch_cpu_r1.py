"""Run only the new S whole-matrix CPU composition, preserving old stages."""
import argparse
import io
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'scripts')]


def main():
    p=argparse.ArgumentParser()
    for name in ('assets','output'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('profile','scope','manifest-sha256'):p.add_argument('--'+name,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve S whole CPU evidence')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('Whole S CPU must hide all GPUs')
    started,cpu=time.monotonic(),time.process_time()
    import torch
    original_load=torch.load
    def forbidden(*args,**kwargs):raise RuntimeError('CPU S batch cannot initialize CUDA, load weights or download')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    torch.set_num_threads(2);os.nice(10)
    runtime=ROOT/'cache/runtime'
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('CPU S refuses Triton execution: '+name)
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
    import test_sq_s_batch_r1 as units
    stream=io.StringIO()
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(units))
    scope=json.loads((ROOT/args.scope).read_text())
    if not tests.wasSuccessful() or tests.testsRun!=scope['unit_controls'] or tests.skipped:
        raise ValueError('S whole-matrix controls failed: '+stream.getvalue())
    artifacts=ROOT/'S-batch-CPU-artifacts';loads=[]
    def tiny_loader(path,**kwargs):
        path=Path(path)
        if (path.is_symlink() or not path.resolve().is_relative_to(artifacts.resolve())
                or path.parent.name!='streaming' or path.stat().st_size>8*2**20
                or not path.name.startswith(('anchor-','state-')) or path.suffix!='.pt'
                or kwargs!={'map_location':'cpu','weights_only':True}):
            raise ValueError('Only this stage\'s tiny S output may be reloaded')
        loads.append(path.name)
        return original_load(path,**kwargs)
    from check_sq_s_batch_cpu_r1 import run
    fixture=run(runtime,artifacts,tiny_loader);rows=fixture['checks']
    if len(rows)!=2 or {r['flow'] for r in rows}!={False,True} or len(loads)!=80 or torch.cuda.is_initialized():
        raise ValueError('Both complete S upper matrices and exact80 tiny reloads required')
    for row in rows:
        if (row['status']!='PASS' or row['complete_CPU_paths']!=10 or row['warm_CPU_paths']!=2
                or len(row['OFF_ON_controls'])!=4 or row['S_labels_collected']!=0
                or row['observed_head_forward_calls']!=936 or row['observed_deep_block_calls']!=552
                or row['reload_audit']['files_SHA_and_bytes_reloaded']!=140
                or not row['exact_full36_guided_final_latent_decoded93_RGB']):
            raise ValueError('Whole S CPU scope changed')
    result=dict(status='S_WHOLE_UPPER_MATRIX_CPU_PASS_NOT_GPU_OR_SCIENTIFIC_ACCEPTANCE',
        profile=args.profile,scope=scope,rows=rows,upstream_sha256=fixture['upstream_sha256'],
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        unit_controls=dict(tests=tests.testsRun,skipped=len(tests.skipped),log=stream.getvalue()),
        tiny_tensor_files_loaded=len(loads),actual_Cosmos_weights=False,real_generated_video=False,
        model_weight_loads_forbidden=True,CUDA_initialized=False,S_labels_collected=0,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])


if __name__=='__main__':main()
