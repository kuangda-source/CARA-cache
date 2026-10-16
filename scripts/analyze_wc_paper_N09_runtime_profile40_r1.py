#!/usr/bin/env python3
"""Offline reconstruction from one saved N09 terminal capture, never another SSH."""
import argparse
import gzip
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','launch-ref','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original independent result')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.runtime_profile40_acceptance_r1 import accept
    from wcomr.frozen_shared_production_r1 import sha
    value=json.loads(gzip.decompress(args.capture.read_bytes()))
    launch=json.loads(args.launch_ref.read_text())['dispatch']
    result=accept(value,launch)
    result.update(capture_ref=str(args.capture),capture_sha256=sha(args.capture),
        launch_ref=str(args.launch_ref),launch_ref_sha256=sha(args.launch_ref))
    with args.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(receipt=str(args.output),status=result['status'],
        full_runtime_profile_scope_accepted=result.get('full_runtime_profile_scope_accepted'))))


if __name__=='__main__':main()
