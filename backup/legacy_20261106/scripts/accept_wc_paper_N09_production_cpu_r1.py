#!/usr/bin/env python3
"""Independently accept the saved original N09 CPU capture without another SSH."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original independent CPU acceptance')
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.runtime_profile40_cpu_acceptance_r1 import accept
    raw = args.capture.read_bytes(); result = accept(json.loads(gzip.decompress(raw)))
    result.update(capture_ref=str(args.capture), capture_sha256=hashlib.sha256(raw).hexdigest())
    with args.output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False); handle.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':main()
