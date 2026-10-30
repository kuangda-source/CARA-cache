"""CPU composition of the unchanged S CLI, model entry and complete matrix."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import socket
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests'), str(ROOT/'scripts')]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', choices=('two_card', 'four_card'), required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if args.output.exists(): raise FileExistsError('Retain original CPU CLI composition attempt')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('NVIDIA_VISIBLE_DEVICES') != 'void':
        raise ValueError('CPU composition requires hidden GPUs')
    start, cpu = time.monotonic(), time.process_time()
    import torch
    tensor_load = torch.load
    def forbidden(*a, **kw): raise RuntimeError('CPU entry forbids CUDA, weights and network')
    torch.cuda._lazy_init = forbidden; torch.load = forbidden
    torch.hub.download_url_to_file = forbidden
    socket.create_connection = forbidden
    socket.socket.connect = forbidden; socket.socket.connect_ex = forbidden
    import huggingface_hub
    huggingface_hub.hf_hub_download = forbidden; huggingface_hub.snapshot_download = forbidden
    torch.set_num_threads(2); os.nice(10)
    artifacts = args.output.parent/'CPU-entry-artifacts'
    artifacts.mkdir(parents=True, exist_ok=False)
    # A metadata sentinel exercises the original parser's checkpoint lookup.
    # It is not a real checkpoint, and is never passed to a weight loader.
    checkpoint = artifacts/'CPU_CHECKPOINT_METADATA_ONLY.json'
    checkpoint.write_text('{"CPU_fixture": true, "actual_weights": false}\n')
    runtime = ROOT/'cache/runtime'
    sys.path[:0] = [str(runtime), str(runtime/'packages/cosmos-oss'), str(runtime/'packages/cosmos-cuda')]
    import cosmos_predict2.config as config
    import cosmos_predict2._src.imaginaire.utils.checkpoint_db as checkpoint_db
    from wcomr.runtime_config import MODEL, EXPERIMENT
    selected = config.MODEL_CHECKPOINTS[config.MODEL_KEYS[MODEL]]
    expected = dict(repo_id=selected.hf.repository, repo_type='model',
        revision=selected.hf.revision, filename=selected.hf.filename)
    lookups = []
    def checkpoint_metadata(**kw):
        if kw != expected: raise ValueError('Original selected checkpoint identity differs')
        lookups.append(dict(kw)); return str(checkpoint)
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
    with patch.object(checkpoint_db, 'hf_hub_download', side_effect=checkpoint_metadata):
        result = run(runtime, artifacts, args.profile, config, tiny_loader)
    rows = result['checks']
    # The unchanged audit loads each of 8 raw states and its four anchor
    # references: 40 calls over 32 unique tensors per flow. The other 108
    # audited files are JSON rows, and some anchor references share a file.
    if (len(rows) != 2 or {r['flow'] for r in rows} != {False, True}
            or len(loads) != 80 or len(set(loads)) != 64 or len(lookups) != 1):
        raise ValueError(f'Two full flows/80 loads/64 unique tensors/one checkpoint lookup required: '
            f'flows={len(rows)}, tensor_reloads={len(loads)}, checkpoint_lookups={len(lookups)}')
    if torch.cuda.is_initialized(): raise ValueError('CUDA initialized during CPU composition')
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    files = ['scripts/run_cara_sq_s_r2.py', 'src/wcomr/sq_s_model_entry_r1.py',
        'src/wcomr/sq_s_runner_r1.py', 'src/wcomr/sq_s_data_terminal_r2.py',
        'scripts/check_cara_sq_s_production_entry_cpu_r5.py', 'tests/check_sq_s_production_entry_cpu_r5.py',
        'plans/cara_next_stage_20261028/sq/S_MODEL_ENTRY_CPU_RESOURCE_CONTRACT_R5.json',
        'tests/check_full_sampling.py', 'tests/check_partial_mlp_guided_sampling_cpu_r1.py']
    receipt = dict(status='S_ACTUAL_CLI_TINY_CPU_COMPOSITION_PASS_NOT_NATIVE_ALLOCATION_OR_GPU',
        profile=args.profile, rows=rows, actual_platform=dict(system=platform.system(), machine=platform.machine()),
        Python=sys.version, packages={n: importlib.metadata.version(n) for n in
            ('torch', 'numpy', 'einops', 'pydantic', 'tyro', 'huggingface-hub', 'loguru', 'diffusers', 'PyYAML')},
        source_sha256={name: sha(ROOT/name) for name in files}, upstream_sha256=result['upstream_sha256'],
        pinned_config_source_sha256=sha(runtime/'cosmos_predict2/config.py'),
        original_model=MODEL, original_experiment=EXPERIMENT, checkpoint_metadata_lookup=lookups,
        checkpoint_lookup_is_CPU_standin=True, tiny_tensor_load_calls=len(loads),
        unique_tiny_tensor_files_loaded=len(set(loads)),
        declared_CPU_substitutions=['source/authority/lease/context admission', 'storage monitor',
            'checkpoint file lookup metadata sentinel', 'environment and registration',
            'WC/RF module namespaces from unchanged AST bodies and explicit CPU globals',
            'inference weight loader, tiny weights/attention/conditioning/geometry/decoder/writer',
            'CUDA telemetry', 'explicit model entry CPU_fixture=True', 'explicit data checker CPU_fixture=True'],
        actual_production_cli_has_no_CPU_fixture_switch=True,
        production_CLI_model_matrix_and_data_sources_modified=False,
        native_Linux_allocation_acceptance=False, complete_S_entry_CPU_accepted=False,
        actual_weights=False, actual_S_labels=0, GPU_ready=False, CUDA_initialized=False,
        GPU_submissions=0, new_GPUh=0, real_central_ledger_writes=0, remote_compute_server_queries=0,
        CPU_wall_seconds=time.monotonic()-start, CPU_seconds=time.process_time()-cpu,
        peak_RSS_native_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    with args.output.open('x') as stream: json.dump(receipt, stream, indent=2, allow_nan=False); stream.write('\n')
    print(receipt['status'], flush=True)


if __name__ == '__main__': main()
