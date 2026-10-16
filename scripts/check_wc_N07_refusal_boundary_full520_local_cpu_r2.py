#!/usr/bin/env python3
"""Local rejection regression; no SSH, CUDA, weights, GPU launch or ledger write."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def hashes(paths):
    # Isolated, bounded standard-library reads avoid historical metadata-helper stalls.
    code = 'import hashlib,json,sys\nfrom pathlib import Path\nprint(json.dumps({n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in json.load(sys.stdin)}))\n'
    result = subprocess.run([sys.executable, '-S', '-c', code], input=json.dumps([str(n) for n in paths]),
        text=True, capture_output=True, timeout=30, check=True)
    return json.loads(result.stdout)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'artifacts', 'output', 'exit'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    if any(x.exists() for x in (args.artifacts, args.output, args.exit)):
        raise FileExistsError('Use a fresh local proof; preserve every earlier attempt')
    config = read(ROOT / 'configs/wc_paper_N07_frozen_shared_production_r1_20261016.json')
    ref = config['references']['shared_CPU_raw']; original = read(ROOT / ref['ref'])
    if hashlib.sha256((ROOT / ref['ref']).read_bytes()).hexdigest() != ref['sha256']:
        raise ValueError('Original numerical proof changed')
    old = original['source_sha256']
    added = ('src/wcomr/frozen_guardrail_boundary_r2.py',
        'tests/test_frozen_guardrail_boundary_r2.py', 'tests/check_frozen_guardrail_boundary_sampling_cpu_r2.py',
        'scripts/check_wc_N07_refusal_boundary_full520_local_cpu_r2.py')
    names = set(old) | set(added)
    before = hashes([ROOT / n for n in names])
    if any(before[str(ROOT / n)] != digest for n, digest in old.items()):
        raise ValueError('A numerical dependency differs from the accepted952 proof')
    runtime_before = hashes([args.runtime / n for n in original['runtime_source_sha256']])
    if any(runtime_before[str(args.runtime / n)] != h for n, h in original['runtime_source_sha256'].items()):
        raise ValueError('The pinned sampler/runtime changed')
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        HF_HUB_DISABLE_TELEMETRY='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    sys.path.insert(0, str(ROOT / 'src'))
    import torch
    torch.set_num_threads(2)
    def forbidden(*a, **kw): raise RuntimeError('CPU proof forbids CUDA, model weights and downloads')
    assert not torch.cuda.is_initialized()
    original_load = torch.load; torch.load = forbidden
    torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden
    start = time.time(); code = 1; value = None
    status = 'N07_REFUSAL_BOUNDARY_FULL520_LOCAL_CPU_TECHNICAL_FAILURE'
    try:
        path = ROOT / 'tests/check_frozen_guardrail_boundary_sampling_cpu_r2.py'
        spec = importlib.util.spec_from_file_location('rejection_boundary_full520', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        def own_loader(path, **kw):
            path = Path(path).resolve()
            assert path.is_relative_to(args.artifacts.resolve())
            assert kw == dict(weights_only=True, map_location='cpu')
            return original_load(path, **kw)
        value = module.run(args.runtime.resolve(), own_loader, args.artifacts.resolve())
        assert not torch.cuda.is_initialized() and value['actual_CPU_paths'] == 520
        assert before == hashes([ROOT / n for n in names])
        assert runtime_before == hashes([args.runtime / n for n in original['runtime_source_sha256']])
        value.update(source_sha256={n:before[str(ROOT / n)] for n in sorted(names)},
            unchanged_original_numerical_sources=len(old), original_numeric_proof_ref=ref,
            runtime_source_sha256=original['runtime_source_sha256'],
            CPU_wall_seconds=time.time() - start, CUDA_initialized=False, GPU_submissions=0,
            SSH_queries=0, ledger_written=False, production_CPU_accepted=False)
        args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
        code, status = 0, value['status']
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps(dict(status=status,
            error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc(),
            source_sha256={n:before[str(ROOT / n)] for n in sorted(names)},
            expected_complete_sampling_CPU_paths=160, expected_zero_step_refusal_CPU_paths=360,
            expected_pairs=5760, GPU_submissions=0, ledger_written=False), indent=2) + '\n')
        raise
    finally:
        args.exit.write_text(json.dumps(dict(status=status, exit_code=code, pid=os.getpid(),
            started_unix=start, ended_unix=time.time(), output_ref=str(args.output),
            output_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest() if args.output.exists() else None,
            expected_CPU_paths=520, GPU_submissions=0, SSH_queries=0, ledger_written=False), indent=2) + '\n')
    print(json.dumps(dict(status=status, actual_CPU_paths=value['actual_CPU_paths'],
        ordinary_pairs=value['ordinary_pairs'], CPU_wall_seconds=value['CPU_wall_seconds'])))


if __name__ == '__main__': main()
