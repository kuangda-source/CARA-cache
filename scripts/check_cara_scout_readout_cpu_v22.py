"""Local small-tensor source-bound evidence; never dispatches or accepts a card."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    import torch
    assert not torch.cuda.is_initialized()
    def forbid(*a,**kw):raise RuntimeError('CPU preparation forbids GPU or weight downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid;torch.set_num_threads(1)
    started=time.monotonic();cpu=time.process_time();stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_scout_readout_v22'))
    files=['src/wcomr/scout_readout_v22.py','tests/test_scout_readout_v22.py',str(Path(__file__).relative_to(ROOT)),
        'src/wcomr/policy_interval_readout_r1.py','src/wcomr/cfg_guided_w1_forward.py','src/wcomr/cfg_guided_w1_outputs.py',
        'plans/cara_predictor_refresh_scout_v2_20261026/E1_STATE_METADATA_V22.json']
    out=dict(status='SOURCE_BOUND_SMALL_TENSOR_CPU_PASS_NOT_FULL_PRODUCTION' if result.wasSuccessful() else 'CPU_PREPARATION_FAILED',
        observed_unix=time.time(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        log=stream.getvalue(),source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
        checks=dict(pinned_WC_C_body=True,pinned_RF_condition_body=True,nonlinear_head='DECLARED_TOY',
        source_exact_warp_flows=[False,True],A_equivalence_state_steps=[22,23,25,33,34,35],
        sparse_parent_free_running=False,real_Cosmos_weights=False,real_frozen_request_entry=False,
        dual_server_CPU_accepted=False,full_production_CPU_accepted=False),
        wall_seconds=time.monotonic()-started,CPU_seconds=time.process_time()-cpu,
        peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,platform=sys.platform,
        CUDA_initialized=torch.cuda.is_initialized(),new_GPU_submissions=0,server_actions=0)
    with a.output.open('x') as f:json.dump(out,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:out[k] for k in ('status','tests','failures','errors','wall_seconds')}))
    if not result.wasSuccessful():raise SystemExit(1)


if __name__=='__main__':main()
