#!/usr/bin/env python3
"""Offline whole24 frame/statistic/finance acceptance, never another SSH."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve original independent acceptance')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.drop1_window24_acceptance_r1 import accept
    raw=a.capture.read_bytes();value=json.loads(gzip.decompress(raw));launch=json.loads(a.launch_ref.read_text())['dispatch']
    result=accept(value,launch);result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest(),
        independent_verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='contrasts'}))


if __name__=='__main__':main()
