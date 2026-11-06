#!/usr/bin/env python3
"""Estimate all40 registered N09 paths from saved original N05/N06 bills."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('N05-capture','N05-acceptance','N06-capture','N06-acceptance',
                 'scope','timing-protocol','method-freeze','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError('Preserve the original cost preview')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.frozen_card_cost_r1 import source_costs
    from wcomr.runtime_profile40_cost_r1 import estimate
    sources=[]
    for kind in ('N05','N06'):
        capture=getattr(a,kind+'_capture');accepted=getattr(a,kind+'_acceptance')
        value=json.loads(gzip.decompress(capture.read_bytes()))
        record=source_costs(value,json.loads(accepted.read_text()),capture_sha256=sha(capture),kind=kind)
        record.update(capture_ref=str(capture),acceptance_ref=str(accepted),acceptance_sha256=sha(accepted))
        sources.append(record)
    scope=json.loads(a.scope.read_text())
    for path,ref in [(a.timing_protocol,'manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json'),
                     (a.method_freeze,'manifests/wc_paper_N07_N08_method_freeze_r1_20261016.json')]:
        if sha(path)!=scope['source_bindings'][ref]['sha256']:
            raise ValueError('Use the source-bound original protocol and five-role freeze')
    result=estimate(scope,json.loads(a.timing_protocol.read_text()),json.loads(a.method_freeze.read_text()),sources)
    result['references']={name:dict(ref=str(getattr(a,name)),sha256=sha(getattr(a,name)))
                          for name in ('scope','timing_protocol','method_freeze')}
    assert 'torch' not in sys.modules
    result['neural_framework_imported']=False
    with a.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(status=result['status'],output=str(a.output),positions=result['complete_plan_positions'],
        forecast_complete_GPUh=result['forecast_complete_GPUh'],GPU_submissions=0,server_ledger_written=False)))


if __name__=='__main__':main()
