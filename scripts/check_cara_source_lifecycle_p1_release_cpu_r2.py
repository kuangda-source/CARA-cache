"""New media/post-score CPU after R1's fixture-only missing-parent failure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile
import time
import unittest


def main():
    parser=argparse.ArgumentParser()
    for name in ('runtime','stage','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True);args=parser.parse_args()
    assert args.host=='two_card' and os.sched_getaffinity(0)=={26}
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void' and not args.output.exists()
    started=time.time();deadline=time.monotonic()+1080;signal.alarm(1200)
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    reg=json.loads((args.stage/'registration.json').read_bytes())
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(sha(args.runtime/n)==h for n,h in reg['runtime_source_sha256'].items())
    old=json.loads((args.stage/'reports/cara_v1_P1_release_Linux_CPU_original_failure_r1_20261102.json').read_bytes())
    captured_file=args.stage/old['capture_ref'];assert sha(captured_file)==old['capture_sha256']
    previous=json.loads(captured_file.read_bytes())['result']
    assert previous['container_state']['Status']=='exited' and previous['container_state']['Pid']==0
    assert previous['container_state']['ExitCode']==1 and previous['CPU_proof'] is None
    assert previous['payload_intact'] and previous['runtime_intact']
    assert len(re.findall(r'^test_.* \.\.\. ok$',previous['log_tail'],re.M))==21
    assert 'Ran 21 tests' in previous['log_tail'] and '\nOK\n' in previous['log_tail']
    changed={n for n,h in previous['registration']['payload_sha256'].items() if reg['payload_sha256'].get(n)!=h}
    assert changed=={'tests/check_cara_source_lifecycle_p1_released_fixture_r1.py'}
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.stage/'tests')]
    scratch=args.stage/'CPU-release-scratch';scratch.mkdir();tempfile.tempdir=str(scratch)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CARA_READ_WRITE_RUNTIME=str(args.runtime))
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1);assert not torch.cuda.is_initialized()
    def forbidden(*args,**kwargs):raise RuntimeError('P1 release CPU forbids CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import RUNTIME_ENTRY
    extra=json.loads((args.stage/RUNTIME_ENTRY).read_bytes())['files']
    assert all(sha(args.runtime/n)==h for n,h in extra.items())
    from check_cara_source_lifecycle_p1_post_scores_cpu_r1 import run
    post=run(scratch/'full146-release',args.stage,deadline=deadline)
    assert post['status']=='P1_REAL_FULL146_READER_AND_ORIGINAL_POST_SCORE_CPU_PASS'
    assert post['logical_quality_positions']==52 and post['identity_controls']==12 and len(post['refusals'])==5
    import test_cara_source_lifecycle_p1_analysis_r1 as analysis
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(analysis))
    assert result.testsRun==4 and result.wasSuccessful() and not result.skipped
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    proof=dict(status='P1_ORIGINAL_RELEASED_ENTRY_FILES_AND_POST_SCORES_LINUX_CPU_PASS',host=args.host,
        source_revision=reg['parent_git_revision'],registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
        supplemental_runtime_sha256=extra,started_unix=started,ended_unix=time.time(),
        tests_run=4,reused_original_R1_controls=21,reused_original_R1_capture_sha256=old['capture_sha256'],
        reused_control_tests_replayed=False,work_seconds=1200,exit_seconds=60,actual_CPU_affinity=[26],post_release=post,
        prior_accepted_components_replayed=False,whole_GPU_entry_accepted=False,P1_GPU_authorized=False,
        actual_central_ledger_accessed=False,GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=proof['status'],tests_run=4,reused_controls=21,
        new_real_pairs=post['original_postrelease_new_pairs'],wall_seconds=time.time()-started)),flush=True)
    signal.alarm(60)


if __name__=='__main__':main()
