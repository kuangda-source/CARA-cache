"""Bounded full media checks with synthetic lifecycle/score metadata."""
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
    for name in ('runtime','stage','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True);args=parser.parse_args()
    assert args.host=='two_card' and os.sched_getaffinity(0)=={26} and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    signal.alarm(900);started=time.time()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert registration['host']==args.host
    assert all(sha(args.stage/p)==h for p,h in registration['payload_sha256'].items())
    assert all(sha(args.runtime/p)==h for p,h in registration['runtime_source_sha256'].items())
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'tests')]
    import test_cara_s_endpoint_artifacts_r1
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_s_endpoint_artifacts_r1))
    assert result.wasSuccessful() and not result.skipped and result.testsRun==15
    from check_cara_s_endpoint_real_video_r1 import run
    media=run(args.stage/'CPU-video-checks')
    proof=dict(status='ENDPOINT_ARTIFACT_REAL_VIDEO_CPU_COMPLETE_NOT_WHOLE_CARD',host=args.host,
        started_unix=started,ended_unix=time.time(),source_revision=registration['parent_git_revision'],
        registration_sha256=sha(args.stage/'registration.json'),payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
        metadata_controls=dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped)),
        media=media,total_controls_passed=25,synthetic_lifecycle_and_historical_scores=True,
        temporary_ledger_only=True,whole_GPU_card_accepted=False,active_experiment_outputs_read=False,
        GPU_submissions=0,ledger_written=False,work_seconds=900,exit_seconds=60)
    signal.alarm(60)
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)


if __name__=='__main__':main()
