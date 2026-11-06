#!/usr/bin/env python3
"""Offline old-card receipt audit, binding later GPU reuse to its accepted admission."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('launch-ref', 'capture', 'newer-launch-ref', 'newer-admission-ref',
                 'newer-cpu-acceptance', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Retain the original independent terminal acceptance')
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.frozen_shared_reused_device_acceptance_r1 import (
        accept, bound_later_admission, read_json, sha,
    )
    later, admission = bound_later_admission(args.newer_launch_ref,
                                            args.newer_admission_ref, args.newer_cpu_acceptance)
    result = accept(read_json(args.capture), read_json(args.launch_ref)['dispatch'], later, admission)
    for field, path in [('capture', args.capture), ('launch', args.launch_ref),
                        ('newer_launch', args.newer_launch_ref),
                        ('newer_admission', args.newer_admission_ref),
                        ('newer_CPU_acceptance', args.newer_cpu_acceptance)]:
        result[field + '_ref'] = str(path)
        result[field + '_sha256'] = sha(path)
    with args.output.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'grouped_statistics'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
