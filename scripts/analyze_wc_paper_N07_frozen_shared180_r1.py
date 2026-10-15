#!/usr/bin/env python3
"""Independent local acceptance of one saved original final-card capture."""
import argparse
import gzip
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.frozen_shared_acceptance_r1 import accept
    from wcomr.frozen_shared_production_r1 import sha
    launch = json.loads(args.launch_ref.read_text())['dispatch']
    value = json.loads(gzip.decompress(args.capture.read_bytes()))
    result = accept(value, launch)
    result.update(capture_ref=str(args.capture), capture_sha256=sha(args.capture),
                  launch_ref=str(args.launch_ref), launch_sha256=sha(args.launch_ref))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'grouped_statistics'}, ensure_ascii=False))


if __name__ == '__main__': main()
