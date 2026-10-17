#!/usr/bin/env python3
"""Offline original full960 acceptance; never fetches or resumes a task."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import traceback


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('launch-ref','capture','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Keep the original independent receipt')
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.automatic_quality_terminal_r1 import accept
    raw=a.capture.read_bytes();launch=json.loads(a.launch_ref.read_text())['dispatch'];value=json.loads(gzip.decompress(raw));code=0
    try:result=accept(value,launch)
    except (ValueError,KeyError,TypeError) as e:
        result=dict(status='N10_ORIGINAL_INDEPENDENT_AUDIT_FAILED_CAPTURE_PRESERVED',full_protocol_accepted=False,
            full_scientific_scope_accepted=False,error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),GPU_submissions=0);code=1
    result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(raw).hexdigest(),
        verifier_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with a.output.open('x') as h:json.dump(result,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','summary','lifecycle')},ensure_ascii=False))
    raise SystemExit(code)


if __name__=='__main__':main()
