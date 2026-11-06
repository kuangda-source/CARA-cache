#!/usr/bin/env python3
"""One original R2 observation at admission, halfway or the recorded final ETA."""
import argparse
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('launch-ref','cpu-acceptance','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--mode',choices=('admission','health','terminal'),default='terminal')
    p.add_argument('--admission-ref',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root/'src'))
    from wcomr.frozen_repair_gpu_r2 import json_file,collect_once
    launch=json_file(a.launch_ref)['dispatch'];admission=json_file(a.admission_ref) if a.admission_ref else None
    result,queried=collect_once(root,launch,a.mode,a.cpu_acceptance,a.output,admission=admission)
    print(json.dumps(dict(receipt=str(a.output),mode=a.mode,new_SSH_observation_attempted=queried,
        status=result.get('status'),technical_classification=result.get('technical_classification'),
        observed_paths=len(result.get('runner',{}).get('runs',[])))))


if __name__=='__main__':main()
