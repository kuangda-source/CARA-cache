"""Bounded actual Linux CPU once-dispatch checks; simulated Docker/metrics."""
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
    def interrupted(signum,frame):raise TimeoutError('Original dispatch CPU proof stopped: '+str(signum))
    signal.signal(signal.SIGALRM,interrupted);signal.signal(signal.SIGTERM,interrupted);signal.alarm(300)
    started=time.time();sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert registration['host']==args.host
    assert all(sha(args.stage/p)==h for p,h in registration['payload_sha256'].items())
    assert all(sha(args.runtime/p)==h for p,h in registration['runtime_source_sha256'].items())
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'tests')]
    import test_cara_s_endpoint_score_dispatch_r1
    tests=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cara_s_endpoint_score_dispatch_r1))
    assert tests.wasSuccessful() and not tests.skipped and tests.testsRun==13
    from check_cara_s_endpoint_score_dispatch_process_r1 import run
    actual=run(args.stage/'CPU-dispatch-checks')
    from wcomr.cara_s_endpoint_score_dispatch_r1 import resource_admission
    fixture_stage=args.stage/'CPU-dispatch-checks/complete/.sync/cara-S-endpoint-CPU-fixture-recovery'
    intent=json.loads((fixture_stage/'endpoint-score-control/intent.json').read_text())
    environment_config=json.loads(Path(intent['manifest_path']).read_text())
    overlay=args.stage.parent/'wc-time-score-CPU-two_card-r1-20261027'
    environment_config.update(torch_home=str(overlay/'torch'),piq_site=str(overlay/'site'))
    environment_check=resource_admission(fixture_stage,environment_config,cpu_validation=True)
    environment_check.update(actual_Alex_checkpoint_SHA_checked=True,actual_PIQ_site_checked=True,
                             future_dispatch_admission=False,production_two_core_affinity_checked=False)
    proof=dict(status='ENDPOINT_SCORE_ONCE_DISPATCH_CPU_COMPLETE_NOT_WHOLE_CARD',host=args.host,
        started_unix=started,ended_unix=time.time(),source_revision=registration['parent_git_revision'],
        registration_sha256=sha(args.stage/'registration.json'),payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
        metadata_controls=dict(tests_run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors),skipped=len(tests.skipped)),
        actual=actual,actual_readonly_CPU_environment=environment_check,total_controls_passed=21,Docker_observations_simulated=True,score_rows_synthetic=True,
        metric_computations=0,whole_GPU_card_accepted=False,active_experiment_outputs_read=False,
        GPU_submissions=0,ledger_written=False,work_seconds=300,exit_seconds=30)
    signal.alarm(30)
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started)),flush=True)


if __name__=='__main__':main()
