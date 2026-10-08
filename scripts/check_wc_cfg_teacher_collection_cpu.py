#!/usr/bin/env python3
"""Actual source-bound CPU invocation of the complete new teacher collector."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('stage','runtime','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.stage/'src'))
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*args,**kwargs):raise RuntimeError('Teacher CPU validation forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    reg=json.loads((args.stage/'collector-preregistration.json').read_text())
    for name,sha in reg['payload_sha256'].items():assert hashlib.sha256((args.stage/name).read_bytes()).hexdigest()==sha,name
    for name,sha in reg['runtime_source_sha256'].items():assert hashlib.sha256((args.runtime/name).read_bytes()).hexdigest()==sha,name
    spec=importlib.util.spec_from_file_location('teacher_collector_CPU',args.stage/'tests/check_cfg_teacher_collection_cpu.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    started=time.perf_counter()
    measurement_spec=importlib.util.spec_from_file_location('measurement_CPU',args.stage/'tests/check_cfg_measurement_cpu.py')
    measurement_module=importlib.util.module_from_spec(measurement_spec);measurement_spec.loader.exec_module(measurement_module)
    try:
        measurement_checks=measurement_module.run()
        result=module.run(args.runtime,artifact_root=args.stage/'CPU-artifacts')
    except BaseException as error:
        args.output.with_suffix('.failure.json').write_text(json.dumps({'status':'COLLECTOR_CPU_FAILED_NOT_PASS','error':str(error),
            'CPU_wall_seconds':time.perf_counter()-started,'CUDA_initialized':torch.cuda.is_initialized(),'GPU_submissions':0},indent=2)+'\n')
        raise
    assert not torch.cuda.is_initialized() and not args.output.exists()
    result.update(CPU_wall_seconds=time.perf_counter()-started,pid=os.getpid(),payload_sha256=reg['payload_sha256'],
                  measurement_checks=measurement_checks)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','CPU_wall_seconds','successful_CFG_pairs','failed_attempts_retained','GPU_submissions')}))


if __name__=='__main__':main()
