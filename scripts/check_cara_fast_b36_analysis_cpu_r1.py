"""GPU-hidden aggregation tests using schematic metadata, never B36 results."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import unittest


def main():
    parser = argparse.ArgumentParser()
    for name in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    signal.alarm(180)
    started = time.time()
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration = json.loads((args.stage/'registration.json').read_text())
    assert registration['host'] == args.host and os.sched_getaffinity(0) == {27}
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    assert all(sha(args.stage/name) == expected for name, expected in registration['payload_sha256'].items())
    assert all(sha(args.runtime/name) == expected for name, expected in registration['runtime_source_sha256'].items())
    sys.path[:0] = [str(args.stage/name) for name in ('src', 'scripts', 'tests')]
    from test_cara_fast_b36_analysis_r1 import AnalysisTests
    tests = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AnalysisTests))
    assert tests.wasSuccessful() and not tests.skipped and tests.testsRun == 6
    assert 'torch' not in sys.modules
    signal.alarm(30)
    proof = dict(status='FAST_B36_ANALYSIS_CPU_COMPLETE_NOT_SCIENCE', host=args.host,
        started_unix=started, ended_unix=time.time(), tests_run=tests.testsRun, tests_skipped=0,
        registration_sha256=sha(args.stage/'registration.json'), payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],
        prompt_equal_formal_plus_six_clean_repeats_verified=True,
        separate_dual_clocks_and_A_only_FIT_sensitivity_verified=True,
        all32_curves_PSNR_and_undefined_gradient_states_preserved=True,
        immutable_A32_freeze_changed=False, WC_RA_UNMATCHED_preserved=True,
        partial_mixed_unaccepted_live_and_UNKNOWN_refused=True,
        production_fixture_and_output_overwrite_refused=True,
        registered_scoring_positions=32, reused_A_metric_pairs=6, new_metric_computations=0,
        CPU_metadata_fixture_only=True, actual_B36_results_accessed=False,
        metric_model_executed=False, torch_imported=False, model_weights_loaded=False,
        GPU_submissions=0, ledger_written=False, temporary_CPU_ledger_mutations_only=True,
        actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
        resource_bound=dict(cpus=1, memory_GiB=4, swap=False, cpuset=[27], work_seconds=180, exit_seconds=30),
        GPU_authorized=False, GPU_dispatch_ready=False)
    with args.output.open('x') as handle:
        json.dump(proof, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=proof['status'], host=args.host, tests_run=tests.testsRun)), flush=True)


if __name__ == '__main__':
    main()
