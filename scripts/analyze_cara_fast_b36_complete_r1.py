"""Read explicit complete B36 receipts and write one immutable analysis file."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from wcomr.cara_fast_b36_analysis_r1 import analyze_complete
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_capture_r2 import file_sha
from wcomr.cara_fast_execution_r2 import SPEC, require


def main():
    parser = argparse.ArgumentParser()
    for name in ('capture', 'settlement', 'manifest', 'score-capture', 'accepted-scores', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Fresh explicit output required; preserve every original receipt')
    inputs = {name: getattr(args, name.replace('-', '_'))
              for name in ('capture', 'settlement', 'manifest', 'score-capture', 'accepted-scores')}
    raw = {name: path.read_bytes() for name, path in inputs.items()}
    values = {name: json.loads(data) for name, data in raw.items()}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()}
    result = analyze_complete(values['capture'], load_card(ROOT, SPEC), values['settlement'],
        values['manifest'], hashes['manifest'], values['score-capture'], values['accepted-scores'])
    result['input_file_sha256'] = {name: dict(path=str(path), sha256=hashes[name]) for name, path in inputs.items()}
    result['analysis_source_sha256'] = {name: file_sha(ROOT/name) for name in (
        'scripts/analyze_cara_fast_b36_complete_r1.py', 'src/wcomr/cara_fast_b36_analysis_r1.py')}
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'], output=str(args.output),
                          formal_logical_positions=32, GPU_submissions=0, metrics_computed=False)))


if __name__ == '__main__':
    main()
