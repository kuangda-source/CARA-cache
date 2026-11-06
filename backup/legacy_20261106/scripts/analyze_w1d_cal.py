import argparse
import hashlib
import json
from pathlib import Path
from wcomr.w1d_analysis import analyze

p = argparse.ArgumentParser()
p.add_argument('--receipt', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--partial', action='store_true')
a = p.parse_args()
raw = a.receipt.read_bytes()
result = analyze(json.loads(raw), partial=a.partial)
result['input_receipt_sha256'] = hashlib.sha256(raw).hexdigest()
a.output.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({key: result[key] for key in ['status', 'frozen_screen_status', 'completed_pair_samples', 'planned_samples']}, indent=2))
