#!/usr/bin/env python3
"""One original N08 halfway technical check from its saved live admission."""
import argparse
import gzip
import json
from pathlib import Path
import sys


def read(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('launch-ref','admission-ref','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.balanced_repeat_health_r1 import bind,collect
    expected=bind(read(args.launch_ref)['dispatch'],read(args.admission_ref))
    value,queried=collect(expected,args.output)
    print(json.dumps(dict(receipt=str(args.output),new_SSH_observation_attempted=queried,
        status=value['status'],technical_classification=value.get('technical_classification'),
        technical_progress=value.get('technical_progress'),final_scientific_results_read=False,GPU_submissions=0)))


if __name__=='__main__':main()
