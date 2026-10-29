"""Run both complete S matrices through the new runner, with GPUs hidden."""
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
    if args.output.exists():raise FileExistsError('Retain original S runner CPU evidence')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('S runner CPU must hide GPUs')
    started,cpu=time.monotonic(),time.process_time();initial_children=resource.getrusage(resource.RUSAGE_CHILDREN)
    import torch
    original_load=torch.load
    def forbidden(*a,**kw):raise RuntimeError('S runner CPU forbids CUDA, model weights and downloads')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    import huggingface_hub
    huggingface_hub.hf_hub_download=forbidden;huggingface_hub.snapshot_download=forbidden
    torch.set_num_threads(2);os.nice(10)
    scope=json.loads((ROOT/args.scope).read_text());expected=scope['hosts'][args.profile]
    log=io.StringIO();tests=unittest.TextTestRunner(stream=log,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName('test_sq_s_runner_r1'))
    if not tests.wasSuccessful() or tests.testsRun!=scope['unit_controls'] or tests.skipped:
        raise ValueError(log.getvalue())
    print(json.dumps(dict(status='S_RUNNER_UNITS_PASS',tests=tests.testsRun,GPU_submissions=0)),flush=True)
    runtime=ROOT/'cache/runtime'
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('S runner CPU refuses Triton execution: '+name)
    triton.runtime.driver.active=Driver()
    import transformers.utils as transformer_utils
    from transformers.utils import import_utils
    saved=(transformer_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    transformer_utils.is_flash_attn_2_available=import_utils.is_flash_attn_2_available=lambda:True
    torch.cuda.current_device=lambda:0
    try:
        import cosmos_predict2._src.predict2.inference.worldcache_utils
        import cosmos_predict2._src.predict2.models.video2world_model_rectified_flow
    finally:
        transformer_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=saved
    retained=json.loads((ROOT/scope['retained_CPU_fixture_ref']).read_text())
    artifacts=ROOT/'S-runner-CPU-artifacts';loads=[]
    def tiny_loader(path,**kwargs):
        path=Path(path)
        stream=path.parent.name=='streaming' and path.name.startswith(('anchor-','state-')) and path.suffix=='.pt'
        weights=path.parent.name=='CPU-fixture-assets' and path.name=='weights.pt'
        if (path.is_symlink() or not path.resolve().is_relative_to(artifacts.resolve())
                or not (stream or weights) or path.stat().st_size>8*2**20
                or kwargs!={'map_location':'cpu','weights_only':True}):
            raise ValueError('Only original tiny output/checkpoint may be loaded')
        loads.append(path.name);return original_load(path,**kwargs)
    from check_sq_s_runner_cpu_r1 import run
    fixture=run(runtime,artifacts,tiny_loader,args.profile,retained);rows=fixture['checks']
    if len(rows)!=2 or {r['flow'] for r in rows}!={False,True} or len(loads)!=expected['tiny_tensor_reloads']:
        raise ValueError('Both complete matrices and exact tiny-load cohort required')
    for row in rows:
        entry=row['runner_entry']
        if (row['status']!='PASS' or row['physical_counts']!=expected['counts_per_flow']
                or row['complete_new_CPU_paths']!=expected['counts_per_flow']['new_paths']
                or len(row['OFF_ON_controls'])!=4 or row['logical_paths']!=10
                or row['observed_head_forward_calls']!=expected['counts_per_flow']['branch_readouts']
                or row['observed_deep_block_calls']!=expected['counts_per_flow']['deep_block_calls']
                or row['reload_audit']['files_SHA_and_bytes_reloaded']!=140
                or len(entry['resource_checks'])!=108 or not entry['complete_state_reset_and_model_precision_unchanged']
                or entry['classification']['CPU_fixture'] is not True
                or entry['health']['status']!='S_COMPLETE_MATRIX_AWAITING_MODEL_CLEANUP_AND_ALLOCATION_TERMINAL'
                or not entry['health']['original_state_restored']):
            raise ValueError('S full physical/guard/storage denominator changed')
    if torch.cuda.is_initialized():raise ValueError('CUDA must remain uninitialized')
    children=resource.getrusage(resource.RUSAGE_CHILDREN)
    result=dict(status='S_RUNNER_FULL_MATRIX_CPU_PASS_NOT_COMPLETE_GPU_CARD',profile=args.profile,
        scope=scope,rows=rows,upstream_sha256=fixture['upstream_sha256'],
        unit_controls=dict(tests=tests.testsRun,skipped=0,log=log.getvalue()),
        original_meta_and_default_decode_components_reused=scope['accepted_unchanged_components'],
        new_meta_architecture_or_synthetic_decode_runs=0,tiny_tensor_files_loaded=len(loads),
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        reaped_child_CPU_seconds=children.ru_utime+children.ru_stime-initial_children.ru_utime-initial_children.ru_stime,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        CPU_import_probes_restored=True,model_weight_loads_forbidden=True,Hugging_Face_downloads_blocked=True,
        actual_Cosmos_weights=False,real_generated_video=False,CUDA_initialized=False,S_real_labels=0,
        actual_S_GPU_entry_accepted=False,whole_S_quote_frozen=False,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result['status'])


if __name__=='__main__':main()
