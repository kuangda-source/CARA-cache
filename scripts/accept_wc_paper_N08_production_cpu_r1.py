#!/usr/bin/env python3
"""Accept one saved full40 production CPU observation without another SSH."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.balanced_repeat_cpu_acceptance_r1 import accept
    raw = args.capture.read_bytes(); result = accept(json.loads(gzip.decompress(raw)))
    result.update(capture_ref=str(args.capture), capture_sha256=hashlib.sha256(raw).hexdigest())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'); print(json.dumps(result))


if __name__ == '__main__': main()
