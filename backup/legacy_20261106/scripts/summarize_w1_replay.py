import argparse,json,hashlib
from pathlib import Path
from wcomr.replay_results import summarize
p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--partial',action='store_true');a=p.parse_args()
raw=a.receipt.read_bytes();receipt=json.loads(raw)
reference_raw=Path(receipt['protocol']['reference_receipt']).read_bytes()
assert hashlib.sha256(reference_raw).hexdigest()==receipt['protocol']['reference_receipt_sha256']
result=summarize(receipt,partial=a.partial,reference=json.loads(reference_raw))
result['input_receipt_sha256']=hashlib.sha256(raw).hexdigest()
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
