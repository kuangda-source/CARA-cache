"""Hash all real inputs before a new CPU-only two-recipe Wan5B fusion."""
import argparse
import json
import os
from pathlib import Path
import shutil
import time
from wcomr.lora_cpu_fusion import prepare_inputs, fuse, write_receipt, file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('Set CUDA_VISIBLE_DEVICES to empty for CPU-only work')
    protocol = json.loads(args.protocol.read_text())
    # Check live resource availability before loading large tensors. These
    # limits govern CPU preparation only and never grant GPU admission.
    if not args.validate_only:
        memory = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
        if int(memory['MemAvailable'].strip().split()[0]) * 1024 < protocol['minimum_available_memory_bytes']:
            raise ValueError('Insufficient CPU available memory')
        if shutil.disk_usage(args.output.parent).free < protocol['minimum_free_disk_bytes']:
            raise ValueError('Insufficient disk headroom')
    started = time.time()
    paths, index, records = prepare_inputs(protocol, args.base, args.cache, args.upstream, args.output)
    receipt = {'pid': os.getpid(), 'started_unix': started, 'protocol_sha256': file_hash(args.protocol),
               'upstream_sha256': file_hash(args.upstream), 'input_integrity': records,
               'gpu_workload_started': False, 'scope': 'Full CPU weights only; model/task/scheduler/GPU untested.'}
    if args.validate_only:
        print(json.dumps(dict(receipt, status='ALL_INPUTS_HASHED_NO_TORCH_IMPORT_OR_OUTPUT_WRITE')))
        return
    try:
        result = fuse(protocol, args.base, paths, args.upstream, args.output, index, receipt)
    except Exception as error:
        if args.output.is_dir():
            receipt.update(status='FAILED_PARTIAL_NOT_READY', finished_unix=time.time(),
                           error_type=type(error).__name__, error=str(error))
            write_receipt(args.output / 'fusion.json', receipt)
        raise
    print(json.dumps({'status': result['status'], 'arms': [x['name'] for x in result['arms']]}))


if __name__ == '__main__':
    main()
