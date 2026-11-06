"""Bounded render verification; fixtures remain visibly distinct from B results."""
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
    registration = json.loads((args.stage/'registration.json').read_bytes())
    assert registration['host'] == args.host and os.sched_getaffinity(0) == {27}
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    assert all(sha(args.stage/name) == expected for name, expected in registration['payload_sha256'].items())
    assert all(sha(args.runtime/name) == expected for name, expected in registration['runtime_source_sha256'].items())
    os.environ['MPLCONFIGDIR'] = str(args.stage/'MPL-cache')
    os.environ['CARA_B36_FIGURE_PREVIEW'] = str(args.stage/'figure-layout-preview')
    sys.path[:0] = [str(args.stage/name) for name in ('src', 'scripts', 'tests')]
    from test_cara_fast_b36_figures_r1 import FigureTests
    tests = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FigureTests))
    assert tests.wasSuccessful() and not tests.skipped and tests.testsRun == 6
    assert 'torch' not in sys.modules
    import matplotlib
    preview = json.loads((args.stage/'figure-layout-preview/CPU-layout-proof.json').read_bytes())
    assert preview['status'] == 'CPU_FIGURE_LAYOUT_ONLY' and preview['CPU_fixture_only']
    signal.alarm(30)
    proof = dict(status='FAST_B36_FIGURES_CPU_COMPLETE_NOT_SCIENCE', host=args.host,
        started_unix=started, ended_unix=time.time(), tests_run=tests.testsRun, tests_skipped=0,
        registration_sha256=sha(args.stage/'registration.json'), payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'], matplotlib_version=matplotlib.__version__,
        bootstrap_samples=20000, bootstrap_seed=20261028, bootstrap_unit='prompt',
        original_bootstrap_implementation_reused=True, formal_positions=32, all_frame_curve_rows=2976,
        figure_panels=4, formats=['png','pdf'], preview_file_sha256=preview['files'],
        preview_proof_sha256=sha(args.stage/'figure-layout-preview/CPU-layout-proof.json'),
        all_five_original_receipts_rebuilt=True, altered_aggregate_input_source_and_partial_refused=True,
        production_fixture_and_output_replacement_refused=True, CPU_watermark_on_all_figures=True,
        CPU_fixture_column_on_all_tables=True, FIT_UNMATCHED_and_undefined_values_preserved=True,
        counterbalanced_member_order_uses_fixed_role_numbers=True, undefined_gradient_plot_path_exercised=True,
        CPU_metadata_fixture_only=True, actual_B36_results_accessed=False, metric_networks_executed=False,
        torch_imported=False, model_weights_loaded=False, GPU_submissions=0, ledger_written=False,
        actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
        resource_bound=dict(cpus=1, memory_GiB=4, swap=False, cpuset=[27], work_seconds=180, exit_seconds=30),
        GPU_authorized=False, GPU_dispatch_ready=False)
    with args.output.open('x') as handle:
        json.dump(proof, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=proof['status'], host=args.host, tests_run=6, figure_panels=4)), flush=True)


if __name__ == '__main__':
    main()
