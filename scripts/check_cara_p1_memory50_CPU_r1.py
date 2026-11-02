"""CPU-only validation of the proposed prelaunch50GiB resource gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.sched_setaffinity(0, {26, 27})
    resource.setrlimit(resource.RLIMIT_AS, (4*2**30, 4*2**30))
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    os.environ.update(CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void',
                      OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path[:0] = [str(root/'tests'), str(root/'src'), str(root/'scripts')]
    started = time.time()
    from wcomr.cara_source_lifecycle_p1_service_r1 import HeldFITService
    from wcomr.cara_source_lifecycle_fit_broker_r1 import Host
    from wcomr.cara_source_lifecycle_p1_dispatch_r1 import ready_inputs
    import test_cara_source_lifecycle_p1_profile_quote_r1 as profile
    import test_cara_source_lifecycle_p1_dispatch_r1 as dispatch
    imported_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(profile.P1ProfileQuoteTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(dispatch.P1DispatchTests),
        dispatch.P1Memory50BoundaryTests('test_current50_admits_and49_refuses_without_changing_caps'),
    ])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    names = ['src/wcomr/cara_source_lifecycle_p1_runner_binding_r1.py',
             'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_CONTAINER_PROFILE_R1.json',
             'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json',
             'tests/test_cara_source_lifecycle_p1_dispatch_r1.py',
             'src/wcomr/cara_source_lifecycle_fit_broker_r1.py',
             'src/wcomr/cara_source_lifecycle_p1_service_r1.py']
    value = dict(schema='CARA_P1_MEMORY50_LINUX_CPU_DELTA_R1',
        status='CPU_DELTA_ACCEPTED' if result.wasSuccessful() else 'CPU_DELTA_FAILED',
        pid=os.getpid(),started_unix=started,ended_unix=time.time(),
        tests_run=result.testsRun,errors=len(result.errors),failures=len(result.failures),
        import_peak_RSS_bytes=imported_peak,
        whole_control_test_peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        peak_is_not_a_production_video_peak=True,
        CPU_affinity=sorted(os.sched_getaffinity(0)),RLIMIT_AS_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],
        CUDA_visible=os.environ['CUDA_VISIBLE_DEVICES'],NVIDIA_visible=os.environ['NVIDIA_VISIBLE_DEVICES'],
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names},
        production_40_8_container_limits_changed=False,original12GiB_query_gate_changed=False,
        real_GPU_or_Docker_dispatch=False,real_metrics_computed=0,ledger_written=False,
        original_GPU_stage_or_authority_modified=False)
    with args.output.open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(value))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
