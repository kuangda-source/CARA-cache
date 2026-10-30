"""Linux-only controls for S's admission-only RAM/namespace correction."""
import argparse
import importlib.abc
import io
import json
import os
from pathlib import Path
import platform
import resource
import signal
import sys
import time
import unittest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    args = parser.parse_args()
    sys.path[:0] = [str(args.stage / name) for name in ('src', 'scripts', 'tests')]
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.sq_s_execution_r2 import validate_source, require
    from wcomr.sq_s_stage_r2 import create
    require(platform.system() == 'Linux' and Path('/proc/self').exists(), 'Actual Linux controls required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and os.environ.get('NVIDIA_VISIBLE_DEVICES') == 'void',
        'GPU-hidden CPU controls required')
    require(os.sched_getaffinity(0) == {4, 5}, 'Original two preparation CPU cores required')
    resource.setrlimit(resource.RLIMIT_AS, (2 * 2**30, 2 * 2**30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 2**20, 64 * 2**20))
    signal.alarm(300)
    os.nice(10)
    class NoTorch(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name == 'torch' or name.startswith('torch.'):
                raise RuntimeError('Admission-only CPU controls forbid Torch/model loading')
    sys.meta_path.insert(0, NoTorch())
    project = args.stage.parent.parent
    bundle, registration = validate_source(project, args.stage)
    started, cpu = time.monotonic(), time.process_time()
    names = ('test_sq_s_host_memory_policy_r1', 'test_sq_s_execution_r2', 'test_sq_s_host_entry_r2')
    log = io.StringIO()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    passed = tests.wasSuccessful() and tests.testsRun == 30 and not tests.skipped and 'torch' not in sys.modules
    result = dict(status='S_RAM50_AFFECTED_LINUX_CPU_PASS' if passed else 'S_RAM50_AFFECTED_LINUX_CPU_FAIL',
        passed=passed, host=registration['host'], stage=str(args.stage), source_revision=registration['source_revision'],
        registration_sha256=sha(args.stage / 'registration.json'), tests=tests.testsRun,
        skipped=len(tests.skipped), failures=len(tests.failures), errors=len(tests.errors), log=log.getvalue(),
        actual_platform=dict(system=platform.system(), machine=platform.machine(), python=sys.version),
        current_profile=bundle['execution_profile'],
        payload_actual_sha256={name: sha(args.stage / name) for name in registration['payload_sha256']},
        runtime_actual_sha256={name: sha(project / 'runtime' / name) for name in registration['runtime_source_sha256']},
        worker_wall_seconds=time.monotonic() - started, worker_CPU_seconds=time.process_time() - cpu,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, GPU_hidden=True, torch_imported=False,
        numerical_pipeline_reexecuted=False, full_S_entry_CPU_accepted=False, GPU_submissions=0, ledger_writes=0)
    create(args.stage / 'RAM50-CPU-result.json', result)
    print(json.dumps({key: result[key] for key in ('status', 'tests', 'skipped', 'worker_wall_seconds')}), flush=True)
    if not passed:
        raise RuntimeError('Affected admission controls failed; retain original result')


if __name__ == '__main__':
    main()
