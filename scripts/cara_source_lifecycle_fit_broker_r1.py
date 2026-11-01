"""Original host P1 score service/CLI bootstrap; no GPU dispatch or reservation."""
import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('role', choices=('serve', 'cpu-cli', 'status', 'recover'))
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--candidate')
    args = parser.parse_args()
    sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'src'), str(Path(__file__).parent)]
    from wcomr.cara_source_lifecycle_fit_broker_r1 import Host, exec_cli, operational_status
    from wcomr.cara_source_lifecycle_p1_clock_r1 import OriginalAllocationClock
    from wcomr.cara_budget_search_journal_r1 import read_record
    import json
    spec = read_record(args.queue/'binding.json')
    if args.role == 'cpu-cli':
        exec_cli(args.queue, args.candidate)
    elif args.role == 'status':
        print(json.dumps(operational_status(spec)))
    elif args.role == 'recover':
        print(json.dumps(Host.reader(spec).recover_query(args.candidate)))
    else:
        if spec['CPU_fixture_only']:
            raise ValueError('Explicit CPU service fixture owns its own clock; production CLI has no fixture bypass')
        import os
        import resource
        os.sched_setaffinity(0, {26, 27})
        resource.setrlimit(resource.RLIMIT_AS, (4*2**30, 4*2**30))
        guardian = read_record(Path(spec['stage'])/'guardian.json')
        Host(spec, OriginalAllocationClock(guardian, spec['context'])).serve()


if __name__ == '__main__':
    main()
