#!/usr/bin/env python3
"""Launch only a separately approved complete180 from its accepted original CPU."""
import argparse
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('authorization','cpu-acceptance','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--stage',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root/'src'))
    from wcomr.frozen_repair_gpu_r2 import launch_once
    result=launch_once(root,a.stage,json.loads(a.authorization.read_text()),a.cpu_acceptance,a.output)
    print(json.dumps(result,ensure_ascii=False))
    if result.get('transport_exit_code',1) or 'dispatch' not in result:raise SystemExit(1)


if __name__=='__main__':main()
