#!/usr/bin/env python3
"""Independently accept one saved repair terminal capture without new SSH."""
import argparse
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('launch-ref','capture','output','cpu-acceptance'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--mode',choices=('admission','terminal'),default='terminal')
    a=p.parse_args();sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    if a.output.exists():raise FileExistsError('Keep the original independent acceptance')
    from wcomr.frozen_repair_gpu_r2 import json_file,sha,bind_launch,accepted_CPU,accept_admission
    from wcomr.frozen_repair_acceptance_r2 import accept
    launch=json_file(a.launch_ref)['dispatch'];value=json_file(a.capture)
    bind_launch(launch,a.cpu_acceptance)
    if a.mode=='admission':result=accept_admission(value,launch,a.cpu_acceptance)
    elif value.get('status')=='N07_REPAIR_ORIGINAL_OBSERVATION_UNKNOWN_NO_RESTART':
        result=dict(status=value['status'],scientific_full_scope_accepted=False,
            original_task_terminal=False,no_GPU_relaunch_authorized=True,GPU_submissions=0)
    else:
        cpu,original=accepted_CPU(a.cpu_acceptance)
        if (value.get('production_CPU_bundle_sha256')!=cpu['production_CPU_bundle_sha256']
                or value.get('production_CPU_launch')!=original['launch']):
            raise ValueError('The terminal observation must keep the exact independently accepted CPU bundle/handle')
        result=accept(value,launch)
    result.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture),launch_ref=str(a.launch_ref),launch_sha256=sha(a.launch_ref))
    with a.output.open('x') as h:json.dump(result,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='grouped_statistics'},ensure_ascii=False))


if __name__=='__main__':main()
