"""GPU-hidden complete S collection topology, using declared CPU stand-ins."""
import argparse
import io
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
import tempfile
import unittest

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
    original_load=torch.load
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
    scope=json.loads((ROOT/args.scope).read_text())
    storage_mode=scope['schema']=='SQ_S_COLLECTION_STREAMING_CPU_R2'
    tiny_loads=[]
    unit=None;unit_loads=[]
    artifacts=ROOT/'S-collection-CPU-artifacts'
    if storage_mode:
        from check_sq_s_collection_storage_cpu_r2 import run
        import test_sq_s_storage_r1 as unit_checks
        def unit_loader(path,**kwargs):
            path=Path(path)
            if (path.is_symlink() or not path.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
                    or path.parent.name!='complete' or path.stat().st_size>2**20
                    or not path.name.startswith(('anchor-','state-')) or path.suffix!='.pt'
                    or kwargs!={'map_location':'cpu','weights_only':True}):
                raise ValueError('CPU storage unit audit refuses non-fixture tensors')
            unit_loads.append(path.name);return original_load(path,**kwargs)
        stream=io.StringIO();old_loader=unit_checks.tensor_loader;unit_checks.tensor_loader=unit_loader
        try:checked=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(unit_checks))
        finally:unit_checks.tensor_loader=old_loader
        if not checked.wasSuccessful() or checked.testsRun!=scope['storage_unit_tests'] or checked.skipped:
            raise ValueError('Complete CPU storage failure controls required: '+stream.getvalue())
        unit=dict(tests=checked.testsRun,skipped=len(checked.skipped),log=stream.getvalue(),tiny_tensor_reloads=len(unit_loads))
        def tiny_loader(path,**kwargs):
            path=Path(path)
            if (path.is_symlink() or not path.resolve().is_relative_to(artifacts.resolve())
                    or path.parent.name!='streaming' or path.stat().st_size>8*2**20
                    or not path.name.startswith(('anchor-','state-')) or path.suffix!='.pt'
                    or kwargs!={'map_location':'cpu','weights_only':True}):
                raise ValueError('CPU storage audit refuses any model/checkpoint or external tensor path')
            tiny_loads.append(path.name)
            return original_load(path,**kwargs)
        fixture=run(runtime,artifacts,tiny_loader)
    else:
        from check_sq_s_collection_cpu_r1 import run
        fixture=run(runtime,artifacts)
    rows=fixture['checks']
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
        if storage_mode:
            stored=row['storage'];audit=stored['reload_audit']
            if (not row['CPU_streaming_storage_accepted'] or stored['measured_rows']!=108
                    or stored['raw_states']!=8 or stored['unique_anchor_files']!=24
                    or not 0<stored['actual_stored_bytes']<=16*2**20
                    or audit['files_SHA_and_bytes_reloaded']!=140
                    or not audit['actual_C_reference_and_noise_grid_retained']):
                raise ValueError('Complete bounded CPU streaming/reload composition required')
    if sum(r['complete_CPU_paths'] for r in rows)!=scope['complete_CPU_paths'] or torch.cuda.is_initialized():
        raise ValueError('S CPU full cohort or hidden-GPU boundary failed')
    if storage_mode and (len(tiny_loads)!=80 or len(unit_loads)!=6):raise ValueError('Exact source-bound tiny-file reload cohort required')
    result=dict(status=('SQ_S_COLLECTION_STREAMING_CPU_PASS_NOT_REAL_MODEL_ACCEPTANCE' if storage_mode
                        else 'SQ_S_COLLECTION_CPU_TOPOLOGY_PASS_NOT_REAL_MODEL_OR_STORAGE_ACCEPTANCE'),
        profile=args.profile,scope=scope,rows=rows,fixture_status=fixture['status'],
        upstream_sha256=fixture['upstream_sha256'],CPU_wall_seconds=time.monotonic()-started,
        CPU_seconds=time.process_time()-cpu,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        CPU_import_adapter='ACCEPTED_PG_IMPORT_ONLY_FLASH_PROBES_AND_CURRENT_DEVICE',
        CPU_import_probes_restored_before_sampling=True,model_weight_loads_forbidden=True,
        CUDA_initialized=False,actual_Cosmos_weights=False,real_generated_video=False,
        CPU_streaming_storage_accepted=storage_mode,tiny_tensor_files_loaded=len(tiny_loads),
        storage_unit_controls=unit,
        streaming_raw_storage_accepted=False,complete_S_card_accepted=False,S_labels_collected=0,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(result['status'])


if __name__=='__main__':main()
