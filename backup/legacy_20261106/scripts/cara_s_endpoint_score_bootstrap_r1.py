"""Durable original CLI identity before executing the frozen CPU score command."""
import argparse
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('role',choices=('supervise','container-cli'))
    parser.add_argument('--stage',type=Path,required=True);args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts')]
    from wcomr import cara_s_endpoint_score_dispatch_r1 as dispatch
    dispatch.supervise(args.stage) if args.role=='supervise' else dispatch.exec_cli(args.stage)


if __name__=='__main__':main()
