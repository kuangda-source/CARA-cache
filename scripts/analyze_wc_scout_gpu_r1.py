#!/usr/bin/env python3
"""Offline whole scout frame/statistic/finance acceptance, never another SSH."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--gate-output',type=Path,help='CAL12 only: freeze four-CAL gate before the DEV bank')
    a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve original independent acceptance')
    if a.gate_output and a.gate_output.exists():raise ValueError('Preserve the original frozen gate')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.scout_gpu_lifecycle_r1 import accept_terminal as accept
    raw=a.capture.read_bytes();value=json.loads(gzip.decompress(raw));launch=json.loads(a.launch_ref.read_text())['dispatch']
    result=accept(value,launch);result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest(),
        independent_verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    gate=None
    if a.gate_output:
        from wcomr.scout_gpu_lifecycle_r1 import freeze_cal_gate
        gate=freeze_cal_gate(value,result)
    with a.output.open('x') as h:json.dump(result,h,indent=2,allow_nan=False);h.write('\n')
    if gate is not None:
        with a.gate_output.open('x') as h:json.dump(gate,h,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='contrasts'}))


if __name__=='__main__':main()
