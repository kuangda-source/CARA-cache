"""Analyze only the fully accepted eight-pair M1 score file."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--accepted', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from wcomr.cara_read_write_analysis_r1 import analyze
    from wcomr.cara_read_write_runner_binding_r1 import CARD
    if args.output.exists():
        raise ValueError('Preserve the original analysis output')
    result = analyze(json.loads((ROOT/CARD).read_text()), json.loads(args.accepted.read_text()))
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], output=str(args.output))))


if __name__ == '__main__':
    main()
