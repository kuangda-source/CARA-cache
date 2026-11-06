#!/usr/bin/env python3
"""Analyze a registered P1 endpoint export after its original acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.policy_generator_r1.evaluation_analysis import analyze


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();d=json.loads(a.input.read_text())
    bindings=d.get('source_bindings',[])
    if d['evidence_kind']=='ACCEPTED_ENDPOINT_EXPORT' and not bindings:
        raise ValueError('Bind original endpoint export and independent acceptance receipts')
    for b in bindings:
        path=(ROOT/b['ref']).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=b['sha256']:
            raise ValueError('Original export binding differs: '+b['ref'])
    result=analyze(d)
    result.update(input_ref=str(a.input),input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),source_bindings=bindings)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=result['status'],selection_status=result['selection']['status'])))


if __name__=='__main__':main()
