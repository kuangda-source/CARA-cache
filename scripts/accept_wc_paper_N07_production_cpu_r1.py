#!/usr/bin/env python3
"""Accept one saved production CPU capture locally; no second SSH query."""
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
    assert not args.output.exists()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.frozen_shared_cpu_acceptance_r1 import accept
    result = accept(json.loads(gzip.decompress(args.capture.read_bytes())))
    result.update(capture_ref=str(args.capture), capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__': main()
