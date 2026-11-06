"""Local CPU integration only; save original success or failure without retry."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve the original receipt; use a new output')
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
    import torch
    if torch.cuda.is_initialized():
        raise ValueError('Local CPU-only integration required')
    path = ROOT / 'tests/check_cara_read_write_suffix_cpu_r1.py'
    spec = importlib.util.spec_from_file_location('cara_read_write_suffix_CPU', path)
    checker = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = checker
    spec.loader.exec_module(checker)
    receipt = dict(schema='CARA_READ_WRITE_M1_SUFFIX_CPU_COMPONENT_R1',
        started_unix=time.time(), status='STARTED', actual_Cosmos_weights=False,
        actual_model_VJP=False, scientific_scores_read=False, GPU_submissions=0,
        ledger_written=False, production_whole_card_accepted=False)
    sources = ['src/wcomr/cara_read_write_suffix_r1.py',
        'tests/check_cara_read_write_suffix_cpu_r1.py',
        'scripts/check_cara_read_write_suffix_cpu_r1.py',
        'src/wcomr/cpu_owned_state_snapshot.py',
        'src/wcomr/policy_generator_r1/production_sampling.py',
        'tests/check_full_sampling.py', 'tests/check_partial_mlp_guided_sampling_cpu_r1.py']
    receipt['source_sha256'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}
    try:
        result = checker.run(args.runtime.resolve(), ROOT / '.sync/read-write-suffix-CPU')
        assert len(result['checks']) == 2 and {r['flow'] for r in result['checks']} == {False, True}
        assert all(r['complete_corners'] == 4 and r['parent_resume_equals_original'] for r in result['checks'])
        receipt.update(status='PINNED_WC_RF_UNIPC_FOUR_CORNER_CPU_COMPONENT_PASS',
            passed=True, result=result, complete_tiny_suffixes=8,
            CUDA_initialized=torch.cuda.is_initialized(),
            limits='Actual pinned WC/RF/UniPC and hard suffix loop; tiny CPU weights/attention/embedding/head/conditions. No real Cosmos cache sensitivity, video, quality, CUDA memory or complete production entry acceptance.')
    except BaseException as error:
        receipt.update(status='CPU_COMPONENT_FAILED', passed=False,
            error_type=type(error).__name__, error=str(error))
        raise
    finally:
        receipt['ended_unix'] = time.time()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    print(json.dumps(dict(status=receipt['status'], suffixes=8, output=str(args.output))))


if __name__ == '__main__':
    main()
