#!/usr/bin/env python3
"""One isolated local registry CPU run; no SSH, model weights or GPU calls."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'artifacts', 'output', 'exit', 'registration'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and not args.exit.exists() and not args.artifacts.exists()
    registration = json.loads(args.registration.read_text())
    assert registration['expected_CPU_paths'] == 952
    binding = registration['payload_sha256']
    assert binding and all(sha(ROOT / n) == h for n, h in binding.items())
    runtime_binding = {str(p.relative_to(args.runtime)): sha(p) for p in args.runtime.rglob('*.py')}
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      HF_HUB_DISABLE_TELEMETRY='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0, str(ROOT / 'src'))
    import torch
    torch.set_num_threads(2)

    def forbidden(*args, **kwargs):
        raise RuntimeError('Shared local CPU forbids CUDA, downloads and external model weights')

    assert not torch.cuda.is_initialized()
    original_load = torch.load
    torch.cuda._lazy_init = forbidden
    torch.load = forbidden
    torch.hub.download_url_to_file = forbidden
    start = time.time()
    code = 1
    status = 'FROZEN_SHARED_FULL952_LOCAL_CPU_TECHNICAL_FAILURE'
    print(json.dumps(dict(status='FROZEN_SHARED_CPU_STARTED', pid=os.getpid(),
                          source_revision=registration['source_revision'], started_unix=start)), flush=True)
    try:
        path = ROOT / 'tests/check_frozen_shared_execution_sampling_cpu_r1.py'
        spec = importlib.util.spec_from_file_location('shared_registry952', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def own_loader(path, **kwargs):
            path = Path(path).resolve()
            assert path.is_relative_to(args.artifacts.resolve())
            assert kwargs == {'weights_only': True, 'map_location': 'cpu'}
            return original_load(path, **kwargs)

        result = module.run(args.runtime, own_loader, args.artifacts)
        assert result['actual_CPU_paths'] == 952 and result['ordinary_pairs'] == 32816
        assert not torch.cuda.is_initialized()
        assert all(sha(ROOT / n) == h for n, h in binding.items())
        assert runtime_binding == {str(p.relative_to(args.runtime)): sha(p) for p in args.runtime.rglob('*.py')}
        result.update(source_revision=registration['source_revision'], source_sha256=binding,
                      runtime_source_sha256=runtime_binding, CPU_wall_seconds=time.time() - start,
                      CUDA_initialized=False, GPU_submissions=0, SSH_queries=0, ledger_written=False)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        code, status = 0, result['status']
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps(dict(
            status=status, error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc(),
            source_revision=registration['source_revision'], expected_CPU_paths=952,
            expected_pairs=32816, full_scope_not_shrunk=True,
            source_sha256=binding, runtime_source_sha256=runtime_binding,
            GPU_submissions=0, SSH_queries=0, ledger_written=False), indent=2) + '\n')
        raise
    finally:
        args.exit.write_text(json.dumps(dict(status=status, exit_code=code, pid=os.getpid(),
            started_unix=start, ended_unix=time.time(), source_revision=registration['source_revision'],
            result_ref=str(args.output), result_sha256=sha(args.output) if args.output.exists() else None,
            expected_CPU_paths=952, source_sha256=binding,
            GPU_submissions=0, SSH_queries=0, ledger_written=False), indent=2) + '\n')
    print(json.dumps(dict(status=status, actual_CPU_paths=952, CPU_wall_seconds=result['CPU_wall_seconds'])), flush=True)


if __name__ == '__main__':
    main()
