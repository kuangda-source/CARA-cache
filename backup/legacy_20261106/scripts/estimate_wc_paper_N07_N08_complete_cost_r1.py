#!/usr/bin/env python3
"""Price the complete frozen180 and40 plans from saved accepted source bills."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('N05-capture','N05-acceptance','N06-capture','N06-acceptance',
                 'shared-bound-inputs','method-freeze','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.frozen_card_cost_r1 import preview,source_costs
    sources=[]
    for kind in ('N05','N06'):
        capture=getattr(args,kind+'_capture');accepted=getattr(args,kind+'_acceptance')
        data=json.loads(gzip.decompress(capture.read_bytes()))
        source=source_costs(data,json.loads(accepted.read_text()),capture_sha256=sha(capture),kind=kind)
        source.update(capture_ref=str(capture),acceptance_ref=str(accepted),acceptance_sha256=sha(accepted))
        sources.append(source)
    result=preview(json.loads(args.shared_bound_inputs.read_text()),json.loads(args.method_freeze.read_text()),sources)
    result.update(shared_bound_inputs_ref=str(args.shared_bound_inputs),shared_bound_inputs_sha256=sha(args.shared_bound_inputs),
                  method_freeze_ref=str(args.method_freeze),method_freeze_sha256=sha(args.method_freeze))
    with args.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(receipt=str(args.output),status=result['status'],
        N07_complete_positions=result['N07']['scope_counts']['total_paths'],
        N08_complete_positions=result['N08']['scope_counts']['total_paths'],
        N07_forecast_GPUh=result['N07']['forecast_complete_GPUh'],N08_forecast_GPUh=result['N08']['forecast_complete_GPUh'],
        combined_forecast_GPUh=result['combined_estimate_GPUh'],
        snapshot_budget_gap_GPUh=result['additional_budget_needed_for_both_at_snapshot_GPUh'],
        GPU_submissions=0,SSH_queries=0,server_ledger_written=False)))


if __name__=='__main__':main()
