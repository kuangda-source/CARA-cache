"""Read archived arm receipts; no GPU, SSH, or mutation of raw evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.result_summary import summarize

p = argparse.ArgumentParser()
p.add_argument('--native', type=Path, required=True)
p.add_argument('--worldcache', type=Path, required=True)
p.add_argument('--supervisor', type=Path, required=True)
p.add_argument('--smoke', type=Path, default=Path('manifests/smoke.json'))
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
files = [a.native, a.worldcache, a.supervisor]
data = [json.loads(path.read_text()) for path in files]
expected = [case['name'] for case in json.loads(a.smoke.read_text())['cases']]
result = summarize(*data, expected)
result['sources'] = [{'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                     for path in files + [a.smoke]]
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(result['status'])
