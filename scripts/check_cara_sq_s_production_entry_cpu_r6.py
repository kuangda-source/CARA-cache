"""Linux native imports, real-cache parsers and full S CPU composition."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import socket
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests'), str(ROOT/'scripts')]


def main():
    parser = argparse.ArgumentParser()
    for name in ('assets', 'output'): parser.add_argument('--'+name, type=Path, required=True)
    for name in ('profile', 'scope', 'manifest-sha256'): parser.add_argument('--'+name, required=True)
    args = parser.parse_args(); args.output = args.output.resolve()
    if args.output.exists(): raise FileExistsError('Preserve original native S CPU card')
    if platform.system() != 'Linux' or not Path('/proc/self').exists():
        raise ValueError('Native S CPU entry requires Linux; local fixtures cannot clear it')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('NVIDIA_VISIBLE_DEVICES') != 'void':
        raise ValueError('Native S CPU entry requires hidden GPUs')
    scope = json.loads((ROOT/args.scope).read_text())
    if args.profile not in scope['hosts'] or args.manifest_sha256 != scope['retained_manifest_sha256']:
        raise ValueError('Frozen native S CPU scope/host/retained membership differs')
    started, cpu = time.monotonic(), time.process_time()
    import torch
    if torch.__version__ != '2.7.1+cu128': raise ValueError('Original S container Torch runtime required')
    tensor_load = torch.load
    def forbidden(*a, **kw): raise RuntimeError('Native S CPU forbids CUDA, weights and network')
    torch.cuda._lazy_init = forbidden; torch.load = forbidden; torch.hub.download_url_to_file = forbidden
    socket.create_connection = forbidden; socket.socket.connect = forbidden; socket.socket.connect_ex = forbidden
    import huggingface_hub
    cached_file, cached_snapshot = huggingface_hub.hf_hub_download, huggingface_hub.snapshot_download
    cache_lookups = []
    def local_file(*a, **kw):
        path = cached_file(*a, **dict(kw, local_files_only=True))
        stat = Path(path).stat()
        cache_lookups.append(dict(args=list(a), kwargs=kw, path=str(path), bytes=stat.st_size,
            stamp=[stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]))
        return path
    def local_snapshot(*a, **kw): return cached_snapshot(*a, **dict(kw, local_files_only=True))
    huggingface_hub.hf_hub_download = local_file; huggingface_hub.snapshot_download = local_snapshot
    torch.set_num_threads(2); os.nice(10)
    os.environ['PYTHONPATH'] = os.pathsep.join([str(ROOT/'src'), str(ROOT/'tests'),
        str(ROOT/'scripts'), os.environ.get('PYTHONPATH', '')])
    log = io.StringIO()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in scope['unit_modules'])
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    if not tests.wasSuccessful() or tests.skipped or tests.testsRun != scope['unit_controls']:
        raise ValueError(log.getvalue())
    print('S_NATIVE_ENTRY_UNITS_PASS '+str(tests.testsRun), flush=True)
    runtime = ROOT/'cache/runtime'
    sys.path[:0] = [str(runtime), str(runtime/'packages/cosmos-oss'), str(runtime/'packages/cosmos-cuda')]
    import triton
    class Driver:
        def get_benchmarker(self): return forbidden
        def __getattr__(self, name): raise RuntimeError('Native S CPU refuses Triton execution: '+name)
    triton.runtime.driver.active = Driver()
    import transformers.utils as transformer_utils
    from transformers.utils import import_utils
    probes = (transformer_utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available, torch.cuda.current_device)
    transformer_utils.is_flash_attn_2_available = import_utils.is_flash_attn_2_available = lambda: True
    torch.cuda.current_device = lambda: 0
    try:
        from cosmos_predict2 import config, inference as actual_inference
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:
        transformer_utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available, torch.cuda.current_device = probes
    artifacts = args.output.parent/'CPU-entry-artifacts'; artifacts.mkdir(parents=True, exist_ok=False)
    loads = []
    def tiny_loader(path, **kw):
        path = Path(path)
        if (path.is_symlink() or not path.resolve().is_relative_to(artifacts.resolve())
                or path.parent.name != 'streaming' or path.suffix != '.pt'
                or not path.name.startswith(('anchor-', 'state-')) or path.stat().st_size > 8*2**20
                or kw != dict(map_location='cpu', weights_only=True)):
            raise ValueError('Only newly written bounded tiny CPU tensors may be loaded')
        loads.append(str(path.relative_to(artifacts))); return tensor_load(path, **kw)
    from check_sq_s_production_entry_cpu_r5 import run
    result = run(runtime, artifacts, args.profile, config, tiny_loader, native_modules=(wc, rf))
    rows = result['checks']
    if (len(rows) != 2 or {row['flow'] for row in rows} != {False, True}
            or not all(row['full_native_WC_RF_module_namespaces'] for row in rows)
            or len(loads) != 80 or len(set(loads)) != 64 or len(cache_lookups) != 1):
        raise ValueError('Complete native imports, two flows, real cache lookup and exact reload cohort required')
    if cache_lookups[0]['bytes'] != scope['diffusion_checkpoint_bytes']:
        raise ValueError('Native parser resolved a metadata sentinel or foreign checkpoint size')
    from check_sq_s_supervisor_cpu_r6 import run as supervise
    controls = [supervise(rows[index % 2], scenario) for index, scenario in enumerate(scope['supervisor_scenarios'])]
    if not all(row['passed'] for row in controls) or torch.cuda.is_initialized():
        raise ValueError('Linux supervisor controls or uninitialized CUDA boundary failed')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    from wcomr.sq_s_spec_r2 import EXECUTION_CRITICAL
    receipt = dict(status='S_NATIVE_IMPORTS_CLI_MATRIX_AND_LINUX_LIFECYCLE_CPU_PASS', profile=args.profile,
        scope=scope, unit_controls=dict(tests=tests.testsRun, skipped=0, failures=0, errors=0, log=log.getvalue()),
        rows=rows, supervisor_controls=controls, checkpoint_cache_lookups=cache_lookups,
        checkpoint_lookup_is_metadata_sentinel=False, checkpoint_bytes_hashed_this_card=False,
        actual_full_inference_module_import=True, actual_full_WC_RF_module_imports=True,
        actual_inference_module_path=str(actual_inference.__file__), actual_native_parser=True,
        CPU_import_probes_restored=True, model_loads_are_declared_tiny_CPU_standins=True,
        weight_loads_forbidden=True, downloads_and_socket_outbound_blocked=True,
        tiny_tensor_load_calls=len(loads), unique_tiny_tensor_files_loaded=len(set(loads)),
        critical_source_sha256={name: sha(ROOT/name) for name in EXECUTION_CRITICAL},
        upstream_sha256=result['upstream_sha256'], pinned_config_source_sha256=sha(runtime/'cosmos_predict2/config.py'),
        actual_platform=dict(system=platform.system(), machine=platform.machine()), torch_version=torch.__version__,
        CPU_wall_seconds=time.monotonic()-started, CPU_seconds=time.process_time()-cpu,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_weights_loaded=False, real_generated_video=False, real_S_labels=0, CUDA_initialized=False,
        actual_GPU_entry_accepted=False, full_S_entry_CPU_accepted=False,
        original_container_terminal_acceptance_required=True, GPU_submissions=0, new_GPUh=0, real_central_ledger_writes=0)
    with args.output.open('x') as stream: json.dump(receipt, stream, indent=2, allow_nan=False); stream.write('\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__': main()
