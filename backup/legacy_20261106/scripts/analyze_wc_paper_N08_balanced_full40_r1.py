#!/usr/bin/env python3
"""Offline original full40 statistics, source, finance and resource acceptance."""
import argparse
import gzip
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.balanced_repeat_acceptance_r1 import accept
    value = json.loads(gzip.decompress(args.capture.read_bytes()))
    result = accept(value, value['launch'])
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result.get(k) for k in ('status', 'scientific_full_scope_accepted', 'stable_repeated_clean_speed_claim',
                                              'actual_GPUh', 'accepted_scientific_videos', 'scored_scientific_videos')}, ensure_ascii=False))


if __name__ == '__main__': main()
