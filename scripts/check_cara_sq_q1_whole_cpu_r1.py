"""GPU-hidden full Q1 entry and source/backend binding; no real-state replay."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'tests')]
import torch
from wcomr.sq_q1_collection_r1 import COUNTS, STATE_KEYS, collect_saved_q1
from wcomr.sq_readout_subgraph_r1 import original_backend_policy, selected_settings


def run(args):
    scope = json.loads((ROOT/args.scope).read_text())
    if (scope['scope_counts'] != COUNTS or scope['GPU_authorization']
            or scope['original_B1_manifest_sha256'] != args.manifest_sha256):
        raise ValueError('Frozen Q1 whole-card scope differs')
    stream = io.StringIO()
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name)
        for name in ('test_sq_q1_collection_r1','test_sq_readout_subgraph_r1','test_sq_q1_readout_r1'))
    tests = unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not tests.wasSuccessful(): raise RuntimeError(stream.getvalue())
    from test_sq_q1_collection_r1 import fixture_cohort
    kernel,schema,values = fixture_cohort()
    events = []
    result = collect_saved_q1(kernel,[dict(prompt=p,step=s) for p,s in STATE_KEYS],
        lambda row: values[(row['prompt'],row['step'])],schema,device='cpu',
        max_copy_bytes=128*2**20,save_health=events.append)
    if not result['complete_Q1_cohort'] or sum(v['completed'] for v in result['head_calls'].values()) != 222:
        raise ValueError('Complete extra/formal Q1 head denominators differ')
    runtime = ROOT/'cache/runtime'
    settings = selected_settings(runtime)
    with original_backend_policy(runtime) as policy:
        backend = policy
    if torch.cuda.is_initialized(): raise RuntimeError('CPU Q1 entry initialized CUDA')
    return dict(status='SQ_Q1_WHOLE_ENTRY_CPU_PASS_FIXTURES_NOT_REAL_CUDA',profile=args.profile,
        scope=scope,fixture_checks=dict(tests=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),
            log=stream.getvalue(),real_model=False),
        production_entry_fixture=dict(complete=True,states=result['completed_states'],
            actual_head_calls=result['head_calls'],scope_counts=result['scope_counts'],
            actual_model_weights=False,selection_on_complete_fixture_only=True),
        selected_experiment_settings=settings,original_backend_policy=backend,
        health_has_no_scores=all('states' not in row and 'selections' not in row for row in events),
        actual_B1_replay=False,original_C_CUDA_parity_accepted=False,
        GPU_runner_entry_accepted=False,financial_lifecycle_accepted=False,
        CUDA_initialized=False,GPU_ready=False,new_GPU_submissions=0,new_GPUh=0,ledger_writes=0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--assets',type=Path,required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--profile',choices=('local','two_card','four_card'),required=True)
    p.add_argument('--scope',required=True);p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    if args.output.exists(): raise FileExistsError('Preserve original Q1 whole-entry CPU receipt')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('NVIDIA_VISIBLE_DEVICES') != 'void':
        raise RuntimeError('Q1 CPU entry must hide GPU devices')
    def forbidden(*args, **kwargs):raise RuntimeError('CPU entry cannot initialize CUDA or download models')
    torch.cuda._lazy_init = forbidden;torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2);os.nice(10)
    started,cpu = time.monotonic(),time.process_time()
    result = run(args)
    raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result.update(wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        peak_RSS_KiB=raw_rss/1024 if platform.system()=='Darwin' else raw_rss,
        raw_ru_maxrss=raw_rss,raw_ru_maxrss_unit='bytes' if platform.system()=='Darwin' else 'KiB',
        torch_version=torch.__version__,
        torch_threads=torch.get_num_threads(),observed_unix=time.time())
    result['actual_platform'] = dict(hostname=platform.node(),system=platform.system(),machine=platform.machine())
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(result['status'],flush=True)


if __name__=='__main__':main()
