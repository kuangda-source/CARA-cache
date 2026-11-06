"""Analyze only a completely accepted original P1 score run; never score again."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]

from wcomr.cara_source_lifecycle_p1_report_r1 import complete


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--cpu-validation', action='store_true')
    parser.add_argument('--fixture-summary', type=Path)
    args = parser.parse_args()
    result = complete(args.stage, cpu_validation=args.cpu_validation, fixture_summary=args.fixture_summary)
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
