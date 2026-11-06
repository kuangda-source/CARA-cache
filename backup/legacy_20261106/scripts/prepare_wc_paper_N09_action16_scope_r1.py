#!/usr/bin/env python3
"""Write the full current action-price scope; never contact the server or launch."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Preserve the original scope registration')
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
    from wcomr.action_price16_plan_r1 import scope
    result=scope(root)
    with args.output.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(output=str(args.output),scope_counts=result['scope_counts'],GPU_submissions=0)))


if __name__=='__main__':main()
