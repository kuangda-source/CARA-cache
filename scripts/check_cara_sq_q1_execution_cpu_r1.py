"""GPU-hidden Linux execution controls; no real B1/weights/CUDA replay."""
import argparse
import io
import json
import os
import platform
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'scripts')]


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--assets',type=Path,required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--profile',choices=('local','two_card','four_card'),required=True)
    p.add_argument('--scope',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original execution CPU proof')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise RuntimeError('Execution CPU proof must hide GPU devices')
    import torch
    def forbidden(*args,**kwargs):raise RuntimeError('CPU proof cannot initialize CUDA or download')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    torch.set_num_threads(2);os.nice(10)
    started,cpu=time.monotonic(),time.process_time()
    children_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    from wcomr.sq_q1_spec_r1 import COUNTS,EXECUTION_CRITICAL,MANIFEST_SHA,SCOPE
    from wcomr.gpu_budget_pool_v2 import sha
    scope=json.loads((ROOT/args.scope).read_text())
    if args.scope!=SCOPE or scope['scope_counts']!=COUNTS or args.manifest_sha256!=MANIFEST_SHA:
        raise ValueError('Frozen full Q1 scope differs')
    # Compile the actual entry modules without executing their GPU-only main.
    for name in EXECUTION_CRITICAL:compile((ROOT/name).read_bytes(),str(ROOT/name),'exec')
    names=('test_sq_q1_execution_r1','test_sq_q1_terminal_r1','test_sq_q1_assets_r1',
           'test_sq_q1_collection_r1','test_sq_q1_readout_r1','test_sq_readout_subgraph_r1')
    stream=io.StringIO();suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not tests.wasSuccessful():raise RuntimeError(stream.getvalue())
    from test_sq_q1_execution_r1 import raw_fixture
    full=raw_fixture()
    if torch.cuda.is_initialized():raise RuntimeError('Execution CPU proof initialized CUDA')
    raw_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children_after=resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu=(children_after.ru_utime+children_after.ru_stime
               -children_before.ru_utime-children_before.ru_stime)
    result=dict(status='SQ_Q1_EXECUTION_CPU_PASS_FIXTURES_NOT_REAL_CUDA',profile=args.profile,
        scope=scope,tests=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),
        skipped=len(tests.skipped),test_log=stream.getvalue(),
        real_Linux_subprocess_control=platform.system()=='Linux' and not tests.skipped,
        subprocess_scenarios=['complete','numeric_failure','runner_failure','thermal','timeout'],
        fixture_head_calls=full['head_calls'],critical_source_sha256={name:sha(ROOT/name) for name in EXECUTION_CRITICAL},
        fixture_is_GPU_evidence=False,actual_B1_replay=False,actual_model_weights=False,
        CUDA_initialized=False,original_C_CUDA_parity_accepted=False,GPU_ready=False,
        actual_GPU_runner_entry_accepted=False,actual_financial_settlement_performed=False,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0,
        temporary_fixture_ledger_only=True,synthetic_authority_only=True,
        wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        child_CPU_seconds=child_cpu,total_process_CPU_seconds=time.process_time()-cpu+child_cpu,
        peak_RSS_KiB=raw_rss/1024 if platform.system()=='Darwin' else raw_rss,
        raw_ru_maxrss=raw_rss,raw_ru_maxrss_unit='bytes' if platform.system()=='Darwin' else 'KiB',
        torch_version=torch.__version__,torch_threads=torch.get_num_threads(),observed_unix=time.time(),
        actual_platform=dict(hostname=platform.node(),system=platform.system(),machine=platform.machine()))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(result['status'],flush=True)


if __name__=='__main__':main()
