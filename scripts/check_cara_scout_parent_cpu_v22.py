"""Local full-sampler small-weight control; no SSH, CUDA or dispatch."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
import resource
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or a.artifacts.exists():raise FileExistsError('Unique evidence paths required')
    a.artifacts.mkdir(parents=True)
    import torch
    assert not torch.cuda.is_initialized()
    def forbid(*a,**kw):raise RuntimeError('Local CPU only: GPU/download forbidden')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid;torch.set_num_threads(1)
    from check_scout_parent_cpu_v22 import run
    begin=time.monotonic();cpu=time.process_time()
    try:
        value=run(ROOT/'cache/runtime',lambda path:torch.load(path,map_location='cpu',weights_only=True),a.artifacts)
    except Exception:
        value=dict(status='CPU_FAILED',traceback=traceback.format_exc())
    files=['src/wcomr/scout_parent_v22.py','src/wcomr/scout_readout_v22.py',
        'tests/check_scout_parent_cpu_v22.py','scripts/check_cara_scout_parent_cpu_v22.py',
        'tests/check_full_sampling.py','tests/check_partial_mlp_guided_sampling_cpu_r1.py',
        'tests/check_rv0_video_actions_cpu.py',
        'src/wcomr/cfg_guided_w1_forward.py','src/wcomr/cfg_paired_probe_forward.py',
        'src/wcomr/policy_interval_readout_r1.py','src/wcomr/full_sampling.py',
        'src/wcomr/partial_mlp_deployment_state.py','src/wcomr/partial_mlp.py',
        'src/wcomr/source_phase_fixed_mask_r1.py','src/wcomr/clean_speed20_r1.py',
        'plans/cara_predictor_refresh_scout_v2_20261026/E1_STATE_METADATA_V22.json',
        'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json']
    value.update(observed_unix=time.time(),wall_seconds=time.monotonic()-begin,CPU_seconds=time.process_time()-cpu,
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
        peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        CUDA_initialized=torch.cuda.is_initialized(),server_actions=0,GPU_submissions=0,
        dual_host_production_accepted=False,artifact_root=str(a.artifacts))
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(value,indent=2) if value['status']=='CPU_FAILED' else json.dumps({k:value[k] for k in ('status','wall_seconds','actual_CPU_paths')}))
    if value['status']=='CPU_FAILED':raise SystemExit(1)
if __name__=='__main__':main()
