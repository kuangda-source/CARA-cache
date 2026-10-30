"""Accept/freeze only a complete original GPU calibration after release."""
import argparse
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    for name in ('project','stage','capture','settlement','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--expected-launch-sha256',required=True)
    parser.add_argument('--freeze',action='store_true')
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh acceptance receipt required')
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr.cara_budget_complete_r1 import accept,freeze_once
    from wcomr.cara_budget_search_journal_r1 import read_record,create_record
    from wcomr.gpu_budget_pool_v2 import sha
    from wcomr.policy_price_terminal_r1 import record,require
    capture=read_record(args.capture)
    require(record(capture,'registration')['payload_sha256'].get('scripts/accept_cara_budget_complete_r1.py')==sha(__file__),
            'Original registered complete-acceptance CLI required')
    result=(freeze_once if args.freeze else accept)(args.project,args.stage,capture,
        args.expected_launch_sha256,read_record(args.settlement))
    require(result['CPU_fixture_only'] is False and result['complete_search_accepted'] is True,
            'CPU fixtures cannot form production acceptance')
    create_record(args.output,result)
    print(result['status'])


if __name__=='__main__':main()
