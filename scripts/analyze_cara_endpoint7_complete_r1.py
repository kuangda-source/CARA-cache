"""Explicit complete receipts only; keep outputs immutable and disallow CPU fixtures."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_endpoint7_analysis_r1 import analyze

def main():
 p=argparse.ArgumentParser()
 names=('card','collection','accepted','packet','config','result','execution')
 for name in names+('output',):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--figures',type=Path)
 a=p.parse_args();assert not a.output.exists()
 raw={n:getattr(a,n).read_bytes() for n in names};values={n:json.loads(v) for n,v in raw.items()}
 report=analyze(**values,manifest_sha256=hashlib.sha256(raw['config']).hexdigest())
 report['input_file_sha256']={n:dict(path=str(getattr(a,n)),sha256=hashlib.sha256(v).hexdigest()) for n,v in raw.items()}
 with a.output.open('x') as f:json.dump(report,f,indent=2,allow_nan=False);f.write('\n')
 if a.figures:
  from wcomr.cara_endpoint7_figures_r1 import render
  render(report,a.figures)
 print(report['status'])
if __name__=='__main__':main()
