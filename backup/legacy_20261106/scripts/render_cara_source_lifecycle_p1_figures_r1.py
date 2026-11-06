"""Export fixed P1 scientific figures after original complete score acceptance."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]

from wcomr.cara_source_lifecycle_p1_figures_r1 import render


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--cpu-validation',action='store_true')
    parser.add_argument('--fixture-summary',type=Path)
    args=parser.parse_args()
    print(json.dumps(render(args.stage,cpu_validation=args.cpu_validation,fixture_summary=args.fixture_summary),allow_nan=False))


if __name__=='__main__':
    main()
