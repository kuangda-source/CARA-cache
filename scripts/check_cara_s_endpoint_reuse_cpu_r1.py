"""Bounded CPU proof plus read-only original completed A32/B36 asset admission."""
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
    signal.alarm(180);started=time.time();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/p)==h for p,h in registration['payload_sha256'].items())
    assert all(sha(args.runtime/p)==h for p,h in registration['runtime_source_sha256'].items())
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.stage/'tests')]
    import test_cara_s_endpoint_gpu_dispatch_r1 as dispatch
    import test_cara_s_endpoint_container_r1 as container
    import test_cara_s_endpoint_gpu_dispatch_child_r1 as child
    import test_cara_s_endpoint_reuse_admission_r1 as reuse
    import test_cara_s_endpoint_entry_r1 as entry
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(m) for m in (dispatch,container,child,reuse,entry))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.testsRun==48 and result.wasSuccessful() and not result.skipped
    assert len(child.OBSERVATIONS)==1
    from wcomr.cara_s_endpoint_reuse_admission_r1 import verify_reuse
    proposal_ref='plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json'
    scores_ref='reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json'
    actual=verify_reuse(args.stage.parent.parent,json.loads((args.stage/proposal_ref).read_text()),
                        json.loads((args.stage/scores_ref).read_text()))
    assert actual['CPU_fixture_only'] is False and len(actual['files'])==32
    proof=dict(status='ENDPOINT_REUSE_ADMISSION_CPU_COMPLETE_NOT_WHOLE_CARD',host=args.host,
        started_unix=started,ended_unix=time.time(),source_revision=registration['parent_git_revision'],
        registration_sha256=sha(args.stage/'registration.json'),payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],actual_CPU_affinity=sorted(os.sched_getaffinity(0)),
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        reuse_controls=13,dispatch_container_controls=24,entry_controls=10,entry_model_and_CUDA_simulated=True,actual_Linux_child_controls=1,observations=child.OBSERVATIONS,
        actual_original_reuse=actual,original_proposal_ref=proposal_ref,original_scores_ref=scores_ref,
        original_proposal_sha256=sha(args.stage/proposal_ref),original_scores_sha256=sha(args.stage/scores_ref),
        work_seconds=180,exit_seconds=30,GPU_submissions=0,ledger_written=False,metrics_computed=0,
        whole_GPU_card_accepted=False,actual_GPU_resources_exercised=False,actual_Cosmos_model_load=False,
        real_Docker_GPU_lifecycle_exercised=False,actual_64GiB_storage_exercised=False,active_experiment_outputs_read=False)
    signal.alarm(30)
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=proof['status'],wall_seconds=time.time()-started,original_files=len(actual['files']))),flush=True)


if __name__=='__main__':main()
