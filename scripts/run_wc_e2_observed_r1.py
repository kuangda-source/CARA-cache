#!/usr/bin/env python3
"""External metadata only: preserve the exact accepted E2 method entry."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys


def main():
    parser=argparse.ArgumentParser(add_help=False)
    for n in ('project','stage'):parser.add_argument('--'+n,type=Path,required=True)
    args,_=parser.parse_known_args()
    if '--cpu-check' in sys.argv:
        os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_CACHE=str(args.project/'hfhub'))
        import torch
        def forbidden(*a,**k):raise RuntimeError('E2 execution CPU forbids CUDA/weights/downloads')
        torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
        import triton
        class ImportOnlyDriver:
            def get_benchmarker(self):return forbidden
            def __getattr__(self,n):raise RuntimeError('E2 execution CPU forbids Triton: '+n)
        triton.runtime.driver.active=ImportOnlyDriver()
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e2_execution_r1 import validate_execution,instrument_save,RUN
    c=json.loads((args.stage/'e2-config.json').read_text())
    p=json.loads((args.stage/'execution-protocol.json').read_text());validate_execution(c,p,args.stage)
    import torch
    from wcomr import e2_confirmation_timing_sampling_r1 as sampler
    original=sampler.run_matrix
    def observed(*a,**k):
        path=args.project/'outputs'/RUN/'diagnostic/memory-boundaries.jsonl'
        with path.open('x') as journal:
            def sink(record):journal.write(json.dumps(record)+'\n');journal.flush()
            def provider():
                if not torch.cuda.is_initialized():return {'status':'CUDA_NOT_INITIALIZED_NO_MEMORY_QUERY'}
                free,total=torch.cuda.mem_get_info()
                return {'allocated_bytes':torch.cuda.memory_allocated(),'reserved_bytes':torch.cuda.memory_reserved(),
                    'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
                    'device_free_bytes':free,'device_total_bytes':total,'scope':'WHOLE_PATH_INCLUDING_OUTER_RESEARCH_WORK'}
            def reset():
                if torch.cuda.is_initialized():torch.cuda.reset_peak_memory_stats()
            k['save']=instrument_save(k['state'],k['save'],sink,provider,reset)
            return original(*a,**k)
    sampler.run_matrix=observed
    try:runpy.run_path(str(args.stage/'scripts/run_wc_e2_confirmation_r1.py'),run_name='__main__')
    finally:sampler.run_matrix=original


if __name__=='__main__':main()
