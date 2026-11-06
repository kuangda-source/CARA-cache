#!/usr/bin/env python3
"""Accept the already-saved original N08 capture; no SSH or GPU access."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import sys

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--verified-source', type=Path)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    if a.output.exists():
        raise ValueError('New independent receipt required')
    if a.verified_source:
        sys.path.insert(0, str(a.verified_source / 'src'))
    else:
        sys.path.insert(0, str(root / 'src'))
    import wcomr
    name = 'wcomr.balanced_repeat_roundoff_acceptance_r1'
    spec = importlib.util.spec_from_file_location(name, root / 'src/wcomr/balanced_repeat_roundoff_acceptance_r1.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = json.loads(gzip.decompress(a.capture.read_bytes()))
    result = module.accept(value, value['launch'])
    result['capture_ref'] = str(a.capture)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result.get(k) for k in ('status', 'scientific_full_scope_accepted',
        'stable_repeated_clean_speed_claim', 'actual_GPUh', 'accepted_scientific_videos', 'scored_scientific_videos')},
        ensure_ascii=False))

if __name__ == '__main__':
    main()

