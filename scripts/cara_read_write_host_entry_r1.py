"""Original M1 dispatcher child; the reused guardian owns the sole clock."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    for key in ('project', 'stage'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    sys.path[:0] = [str(args.stage/'src'), str(args.stage/'scripts')]
    from wcomr.cara_read_write_dispatch_r1 import publish_launch, GUARDIAN
    from wcomr.cara_s_endpoint_host_guardian_r1 import allocate
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.gpu_budget_pool_v2 import sha
    if read_record(args.stage/'registration.json')['payload_sha256'][GUARDIAN] != sha(__file__):
        raise ValueError('Original M1 guardian entry source differs')
    password = None
    try:
        incoming = json.load(sys.stdin)
        if set(incoming) == {'sudo_password'} and isinstance(incoming['sudo_password'], str) and incoming['sudo_password']:
            password = incoming['sudo_password']
    except (ValueError, TypeError):
        pass
    _, storage = publish_launch(args.project, args.stage)
    allocate(args.project, args.stage, storage, password)


if __name__ == '__main__':
    main()
