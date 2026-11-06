"""One bounded readonly pass over the20 frozen asset files; never deserialize weights."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for name in ('runtime','stage','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True)
    args=parser.parse_args()
    assert not args.output.exists() and args.host=='two_card'
    assert os.sched_getaffinity(0)=={26}
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    signal.alarm(1200)
    started=time.time()
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    registration=json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/name)==expected for name,expected in registration['payload_sha256'].items())
    assert all(sha(args.runtime/name)==expected for name,expected in registration['runtime_source_sha256'].items())
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.cara_fast_b36_dispatch_r2 import ASSETS,assets_check,assets_unchanged
    from wcomr.gpu_budget_pool_v2 import atomic_json
    specification=json.loads((args.stage/ASSETS).read_text())
    assets=[]
    for descriptor in specification['files']:
        assets+=assets_check(args.runtime.parent,dict(files=[descriptor],snapshot_links=[]))
        atomic_json(args.stage/'CPU-asset-progress.json',dict(checked=len(assets),denominator=len(specification['files']),
            bytes_checked=sum(row['stamp'][2] for row in assets),observed_unix=time.time(),scientific_scores_returned=False))
        print(json.dumps(dict(status='ASSET_DIGEST_PROGRESS',checked=len(assets),total=len(specification['files']))),flush=True)
    assets_unchanged(args.runtime.parent,specification,assets)
    assert len(assets)==20 and 'torch' not in sys.modules
    signal.alarm(30)
    result=dict(status='B36_FROZEN_ASSETS_READONLY_CPU_COMPLETE',host=args.host,
        started_unix=started,ended_unix=time.time(),assets=assets,asset_spec_sha256=sha(args.stage/ASSETS),
        asset_module_sha256=sha(args.stage/'src/wcomr/cara_fast_b36_dispatch_r2.py'),
        registration_sha256=sha(args.stage/'registration.json'),payload_sha256=registration['payload_sha256'],
        runtime_source_sha256=registration['runtime_source_sha256'],bytes_read=sum(row['stamp'][2] for row in assets),
        asset_files_checked=20,all_snapshot_links_verified=True,model_weights_deserialized=False,torch_imported=False,
        GPU_submissions=0,ledger_written=False,resource_bound=dict(cpus=1,memory_GiB=4,swap=False,cpuset=[26],
            work_seconds=1200,exit_seconds=30),GPU_authorized=False,GPU_dispatch_ready=False)
    with args.output.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps(dict(status=result['status'],asset_files_checked=20,bytes_read=result['bytes_read'])),flush=True)


if __name__=='__main__':
    main()
