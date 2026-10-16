#!/usr/bin/env python3
"""Price the complete action12/944 scope using the original accepted full368 bill."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('scope','source-capture','source-acceptance','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original full-card price preview')
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
    from wcomr.action_price16_cost_r1 import source_costs,estimate
    scope=json.loads(args.scope.read_text());ref=scope['references']['H1_parameters'];p=root/ref['ref']
    if sha(p)!=ref['sha256']:raise ValueError('Use the unchanged original H1 costs only as a declared mixture allowance')
    source=source_costs(json.loads(args.source_capture.read_text()),json.loads(args.source_acceptance.read_text()),
        capture_sha256=sha(args.source_capture))
    result=estimate(scope,source,frozen_historical_D_incremental_seconds=json.loads(p.read_text())['cost_seconds']['D'])
    result['references']={n:dict(ref=str(getattr(args,n)),sha256=sha(getattr(args,n)))
        for n in ('scope','source_capture','source_acceptance')}
    result['references']['historical_D_allowance']=ref
    assert 'torch' not in sys.modules
    result['neural_framework_imported']=False
    with args.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(status=result['status'],forecast_complete_GPUh=result['forecast_complete_GPUh'],
        billed_limit_GPUh=result['billed_limit_GPUh'],positions=result['complete_parent_positions'],GPU_submissions=0)))


if __name__=='__main__':main()
