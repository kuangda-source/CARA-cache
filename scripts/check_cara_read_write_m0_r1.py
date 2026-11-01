"""Run local CPU component controls; never transport or dispatch an experiment."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new receipt; preserve the original CPU attempt')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['CARA_READ_WRITE_RUNTIME'] = str(args.runtime.resolve())
    sys.path.insert(0, str(ROOT / 'src'))
    import torch
    from wcomr.cara_read_write_state_r1 import UNIPC_SHA256
    if torch.cuda.is_initialized():
        raise ValueError('CPU-only component check required')
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    upstream = 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py'
    if sha(args.runtime / upstream) != UNIPC_SHA256:
        raise ValueError('Original registered UniPC source differs')
    started = time.time()
    path = ROOT / 'tests/test_cara_read_write_m0_r1.py'
    spec = importlib.util.spec_from_file_location('cara_read_write_m0_controls', path)
    tests = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = tests
    spec.loader.exec_module(tests)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    passed = result.wasSuccessful() and result.testsRun == 20 and not result.skipped
    sources = [
        'src/wcomr/cara_read_write_state_r1.py',
        'src/wcomr/cara_read_write_proposals_r1.py',
        'tests/test_cara_read_write_m0_r1.py',
        'scripts/check_cara_read_write_m0_r1.py',
        'src/wcomr/policy_generator_r1/interval_grammar.py',
        'src/wcomr/cara_fast_spec_r1.py',
        'plans/cara_next_stage_20261101/e1/E1_COMPLETE_ENDPOINT_DECISION_R1.json',
        'plans/cara_next_stage_20261101/read_write/EXPERIMENT_PROTOCOL_R1.json',
        'plans/cara_next_stage_20261101/read_write/SOURCE_FRAMEWORK_20261101.md',
    ]
    receipt = dict(schema='CARA_READ_WRITE_M0_CPU_COMPONENT_R1',
        status='CPU_COMPONENT_PASS_FULL_MODEL_VJP_PENDING' if passed else 'CPU_COMPONENT_FAILED',
        passed=passed, started_unix=started, ended_unix=time.time(), execution_host='local_macOS_CPU',
        source_parent_HEAD=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        skipped=len(result.skipped), metrics=tests.METRICS,
        original_runtime_source_sha256={upstream: UNIPC_SHA256},
        source_sha256={p: sha(ROOT / p) for p in sources},
        completed_components=['original UniPC explicit memory + all36 exact forward parity',
            'original UniPC history VJP + directional finite differences',
            'synthetic cache recurrence + original UniPC read/write derivative control',
            'four-corner partition and signed interaction algebra',
            'at most two exact-K legal radius1/radius2 hard proposals'],
        remaining=['actual Cosmos complete cache-state adapter and forward parity',
            'actual frozen-backbone input VJP, warp/non-smooth handling, VAE/LPIPS backward',
            'two-card production CPU and complete M1 entry/quote/admission',
            'real GPU read/write mechanism, hard-swap usefulness and held-out method evidence'],
        model_weights_loaded=False, actual_Cosmos_cache_differentiated=False,
        full_model_adjoint_accepted=False, scientific_method_established=False,
        CUDA_initialized=torch.cuda.is_initialized(), GPU_submissions=0, ledger_written=False,
        new_GPU_authority=False, original_experiments_replayed=False, original_freezes_changed=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=receipt['status'], tests_run=result.testsRun, output=str(args.output))))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
