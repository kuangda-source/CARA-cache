#!/usr/bin/env python3
"""Read-only hardware exclusivity preflight; never stop jobs or change GPU modes.

Run immediately before a future dispatch, then with --phase active and the
actual runner identity after it owns its CUDA context. A pass is a snapshot,
not an ownership reservation. Keep the project lease and active monitoring.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.policy_asset_price_review_r1 import exclusive_gate
from wc_four_card_policy_assets_r1 import ssh

OBSERVE = r'''
import json, os, subprocess, sys, time
from pathlib import Path
d=json.load(sys.stdin);uuid=d['gpu_uuid']
def query(columns,kind):
 r=subprocess.run(['/usr/bin/nvidia-smi','-i',uuid,'--query-'+kind+'='+columns,
   '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=20)
 if r.returncode:raise RuntimeError('NVIDIA query failed')
 return [x.strip().split(', ') for x in r.stdout.splitlines() if x.strip()]
g=query('uuid,compute_mode','gpu')
if len(g)!=1 or g[0][0]!=uuid:raise RuntimeError('UUID binding failed')
apps=[]
for u,pid,mem in query('gpu_uuid,pid,used_gpu_memory','compute-apps'):
 p=Path('/proc')/pid
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split()
  apps.append(dict(gpu_uuid=u,pid=int(pid),uid=p.stat().st_uid,
    start_ticks=int(fields[19]),used_GPU_memory_MiB=mem))
 except (OSError,ValueError):
  apps.append(dict(gpu_uuid=u,pid=int(pid),identity_unknown=True))
mps=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  name=(p/'comm').read_text().strip()
  if name.startswith('nvidia-cuda-mps'):mps.append(int(p.name))
 except FileNotFoundError:pass
 except PermissionError:mps=None;break
print(json.dumps(dict(gpu_uuid=uuid,compute_mode=g[0][1],compute_apps=apps,
 mps_processes=mps,observed_unix=time.time(),compute_mode_changed=False)))
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gpu-uuid', required=True)
    p.add_argument('--phase', choices=('idle', 'active'), default='idle')
    p.add_argument('--runner-pid', type=int)
    p.add_argument('--runner-start-ticks', type=int)
    p.add_argument('--runner-uid', type=int)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    if not re.fullmatch(r'GPU-[0-9a-fA-F-]{36}', a.gpu_uuid):
        p.error('An actual physical GPU UUID is required')
    runner = dict(pid=a.runner_pid, start_ticks=a.runner_start_ticks, uid=a.runner_uid)
    if a.phase == 'active' and any(v is None for v in runner.values()):
        p.error('Active verification requires PID, start ticks and UID')
    started = time.monotonic()
    snapshot = ssh(OBSERVE, dict(gpu_uuid=a.gpu_uuid))
    elapsed = time.monotonic() - started
    # The server and laptop wall clocks may differ. A fresh synchronous query's
    # age is bounded by its entire monotonic round trip, not their wall delta.
    result = exclusive_gate(snapshot, gpu_uuid=a.gpu_uuid, phase=a.phase,
                            runner=runner, now=snapshot.get('observed_unix', 0) + elapsed)
    result.update(snapshot=snapshot, GPU_submissions=0, observed_local_unix=time.time(),
                  freshness_basis='LIVE_QUERY_MONOTONIC_ROUNDTRIP_BOUND', roundtrip_seconds=elapsed)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'reasons')}))
    return 0 if result['observation_passed'] else 2


if __name__ == '__main__':
    sys.exit(main())
