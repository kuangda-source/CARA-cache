import argparse,json
from pathlib import Path
from wcomr.w1d_summary import summarize
p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--partial',action='store_true');a=p.parse_args()
result=summarize(json.loads(a.receipt.read_text()),partial=a.partial)
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
