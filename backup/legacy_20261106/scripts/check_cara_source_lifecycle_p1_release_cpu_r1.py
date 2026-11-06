"""Bounded new P1 production-binding/released-file/post-score Linux CPU probe."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest


def main():
    parser=argparse.ArgumentParser()
    for name in ('runtime','stage','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True)
    args=parser.parse_args()
    assert args.host=='two_card' and os.sched_getaffinity(0)=={26}
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert not args.output.exists()
    started=time.time();deadline=time.monotonic()+1080;signal.alarm(1200)
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg=json.loads((args.stage/'registration.json').read_bytes())
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(sha(args.runtime/n)==h for n,h in reg['runtime_source_sha256'].items())
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.stage/'tests')]
    scratch=args.stage/'CPU-release-scratch';scratch.mkdir();tempfile.tempdir=str(scratch)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CARA_READ_WRITE_RUNTIME=str(args.runtime))
    import torch
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()
    def forbidden(*args,**kwargs):raise RuntimeError('P1 release CPU forbids CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    modules=[importlib.import_module(n) for n in ('test_cara_source_lifecycle_p1_entry_r1',
        'test_cara_source_lifecycle_p1_inventory_r1','test_cara_source_lifecycle_p1_scores_r1')]
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromModule(m) for m in modules))
    assert result.wasSuccessful() and result.testsRun==21 and not result.skipped
    from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import RUNTIME_ENTRY
    extra=json.loads((args.stage/RUNTIME_ENTRY).read_bytes())['files']
    assert all(sha(args.runtime/n)==h for n,h in extra.items())
    from check_cara_source_lifecycle_p1_post_scores_cpu_r1 import run
    post=run(scratch/'full146-release',args.stage,deadline=deadline)
    assert post['status']=='P1_REAL_FULL146_READER_AND_ORIGINAL_POST_SCORE_CPU_PASS'
    assert post['logical_quality_positions']==52 and post['identity_controls']==12 and len(post['refusals'])==5
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    proof=dict(status='P1_ORIGINAL_RELEASED_ENTRY_FILES_AND_POST_SCORES_LINUX_CPU_PASS',host=args.host,
        source_revision=reg['parent_git_revision'],registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
        supplemental_runtime_sha256=extra,started_unix=started,ended_unix=time.time(),
        tests_run=21,work_seconds=1200,exit_seconds=60,actual_CPU_affinity=[26],post_release=post,
        prior_accepted_components_replayed=False,whole_GPU_entry_accepted=False,P1_GPU_authorized=False,
        actual_central_ledger_accessed=False,GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as stream:json.dump(proof,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=proof['status'],tests_run=21,new_real_pairs=post['original_postrelease_new_pairs'],
                         wall_seconds=time.time()-started)),flush=True)
    signal.alarm(60)


if __name__=='__main__':main()
