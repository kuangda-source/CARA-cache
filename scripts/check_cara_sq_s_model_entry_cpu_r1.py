"""CPU-only loader boundaries and the actual pinned Cosmos argument parsers."""
import argparse
import hashlib
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
    if args.output.exists():raise FileExistsError('Retain original S loader CPU attempt')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('The S loader CPU proof must hide all GPUs')
    started,cpu=time.monotonic(),time.process_time()
    import torch
    def forbidden(*a,**kw):raise RuntimeError('S model-entry CPU forbids CUDA, weights and downloads')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    import huggingface_hub
    # The original SetupArguments parser resolves its checkpoint through this
    # API even when the file is already cached. Permit that readonly lookup;
    # cache misses must fail without attempting a download.
    cached_file=huggingface_hub.hf_hub_download
    cached_snapshot=huggingface_hub.snapshot_download
    def local_file(*a,**kw):return cached_file(*a,**dict(kw,local_files_only=True))
    def local_snapshot(*a,**kw):return cached_snapshot(*a,**dict(kw,local_files_only=True))
    huggingface_hub.hf_hub_download=local_file;huggingface_hub.snapshot_download=local_snapshot
    torch.set_num_threads(2);os.nice(10)
    scope=json.loads((ROOT/args.scope).read_text())
    log=io.StringIO();tests=unittest.TextTestRunner(stream=log,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName('test_sq_s_model_entry_r1'))
    if not tests.wasSuccessful() or tests.skipped or tests.testsRun!=scope['unit_controls']:
        raise ValueError(log.getvalue())
    print('S_MODEL_ENTRY_15_CPU_CONTROLS_PASS',flush=True)
    runtime=ROOT/'cache/runtime'
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import cosmos_predict2.config as actual_config
    from test_sq_s_model_entry_r1 import ModelEntryTests
    test=ModelEntryTests()
    def actual_parser(bundle,storage,api,inference):
        from wcomr.runtime_config import MODEL,EXPERIMENT
        api.config=actual_config;original=api.install_registration
        def checked(model,experiment):
            if (model,experiment)!=(MODEL,EXPERIMENT):raise ValueError('Original model/experiment parser differs')
            return original(model,experiment)
        api.install_registration=checked
    result,(_,_,api,_,events,health,_,outputs)=test.run_entry(before=actual_parser)
    if (api.config is not actual_config or events.count('load')!=1 or events.count('cleanup')!=1
            or result['model_entry']['model_loads']!=1 or outputs!=[result]
            or not result['model_entry']['environment_cleanup_accepted']):
        raise ValueError('Actual pinned setup/input parsers and complete one-load cleanup sequence required')
    if torch.cuda.is_initialized():raise ValueError('CUDA must remain uninitialized')
    config_path=runtime/'cosmos_predict2/config.py'
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    if sha(config_path)!=scope['pinned_config_source_sha256']:raise ValueError('Pinned actual Cosmos config source differs')
    r=dict(status='S_MODEL_ENTRY_PARSERS_AND_LOADER_BOUNDARIES_CPU_PASS_NOT_GPU_CARD',
        profile=args.profile,scope=scope,unit_controls=dict(tests=tests.testsRun,skipped=0,errors=0,failures=0,log=log.getvalue()),
        actual_pinned_Cosmos_config_parser=True,pinned_config_source_sha256=sha(config_path),
        checkpoint_resolution_readonly_existing_cache_only=True,
        original_two_FIT_input_objects_lossless=True,original_setup_fields_lossless=True,
        original_model_and_experiment_parser_binding=True,
        native_parser_probe=dict(events=events,model_load_standins=1,environment_cleanup_standins=1,
            actual_environment_loader_and_matrix_replaced=True,
            runtime_registration_and_worldcache_install_replaced=True,result=result),
        original_matrix_component_reused_unchanged=scope['unchanged_matrix_acceptance'],
        actual_Cosmos_weights=False,actual_model_forward_calls=0,complete_GPU_model_entry_accepted=False,
        actual_S_labels=0,CUDA_initialized=False,whole_S_quote_frozen=False,
        CPU_wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        parent_peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(),machine=platform.machine()),torch_version=torch.__version__,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
    print(r['status'],flush=True)


if __name__=='__main__':main()
