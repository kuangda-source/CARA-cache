"""Bounded metadata-chain controls; no sampler, metric model, or GPU execution."""
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
    parser=argparse.ArgumentParser()
    for key in ('runtime','stage','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--host',required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    signal.alarm(30)
    start=time.time()
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert registration['host']==args.host
    assert all(sha(args.stage/name)==value for name,value in registration['payload_sha256'].items())
    assert all(sha(args.runtime/name)==value for name,value in registration['runtime_source_sha256'].items())
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    sys.path[:0]=[str(args.stage/name) for name in ('src','scripts','tests')]
    import test_cara_fast_post_r2
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_fast_post_r2))
    assert result.wasSuccessful() and not result.skipped
    assert not any(name=='torch' or name.startswith('cosmos_predict2') for name in sys.modules)
    signal.alarm(10)
    proof=dict(status='FAST_A32_POST_METADATA_CHAIN_CPU_COMPLETE_NOT_GPU',host=args.host,
        tests_run=result.testsRun,tests_skipped=0,started_unix=start,ended_unix=time.time(),
        registration_sha256=sha(args.stage/'registration.json'),payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],
        simulated_GPU_Docker_and_process_observations=True,temporary_CPU_ledgers_only=True,
        real_metric_execution=False,real_model_execution=False,old_model_videos_read=0,
        sampler_matrix_repeated=False,GPU_submissions=0,ledger_written=False,
        resource_bound=dict(cpus=1,memory_GiB=4,work_seconds=30,exit_seconds=10))
    with args.output.open('x') as handle:
        json.dump(proof,handle,indent=2)
        handle.write('\n')
    print(json.dumps(dict(status=proof['status'],host=args.host,tests_run=result.testsRun)),flush=True)


if __name__=='__main__':
    main()
