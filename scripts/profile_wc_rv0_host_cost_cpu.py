#!/usr/bin/env python3
"""CPU allocation/hash timing at recorded shapes; never a GPU cost bound."""
import argparse
import ast
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import time
from collections.abc import Mapping

import numpy as np
import torch


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--digest-source',type=Path,required=True)
    p.add_argument('--digest-sha256',required=True)
    p.add_argument('--shape-input',type=Path,required=True)
    a=p.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or torch.cuda.is_initialized():
        raise ValueError('Explicit CPU-only host profile required')
    def forbidden(*args,**kwargs):raise RuntimeError('CUDA forbidden in host cost profile')
    torch.cuda._lazy_init=forbidden
    raw=a.digest_source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.digest_sha256:
        raise ValueError('Current state hash source differs')
    fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='tree_digest')
    namespace={'torch':torch,'np':np,'hashlib':hashlib,'Mapping':Mapping}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(a.digest_source),'exec'),namespace)
    digest=namespace['tree_digest']
    shapes=json.loads(a.shape_input.read_text())
    latent=shapes['recorded_parent_latent_shape']
    hidden=shapes['inferred_hidden_shape_from_recorded_QKV_and_latent']
    if latent!=[1,16,24,54,96] or hidden!=[1,24,27,48,2048]:
        raise ValueError('Frozen observed/inferred shape context differs')
    torch.set_num_threads(2)
    rows=[]; started=time.perf_counter()
    for dtype in (torch.bfloat16,torch.float32):
        x=torch.ones(hidden,dtype=dtype,device='cpu')
        timings={'clone':[],'finite_and_SHA256':[]}; hashes=[]
        for _ in range(3):
            begin=time.perf_counter();y=x.detach().clone()
            timings['clone'].append(time.perf_counter()-begin)
            begin=time.perf_counter();hashes.append(digest(y))
            timings['finite_and_SHA256'].append(time.perf_counter()-begin)
            del y;gc.collect()
        if len(set(hashes))!=1:raise ValueError('CPU shape hash repeat differs')
        rows.append({'dtype':str(dtype),'shape':hidden,'bytes_per_tensor':x.numel()*x.element_size(),
                     'timing_seconds':timings,'max_seconds':{k:max(v) for k,v in timings.items()},
                     'stable_synthetic_tensor_sha256':hashes[0]})
        del x;gc.collect()
    print(json.dumps({'status':'CPU_RECORDED_SHAPE_HASH_COST_MEASURED_NOT_GPU_BOUND',
                      'rows':rows,'wall_seconds':time.perf_counter()-started,
                      'CPU_peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                      'torch_version':torch.__version__,'torch_threads':torch.get_num_threads(),
                      'digest_source_sha256':a.digest_sha256,
                      'shape_input_sha256':hashlib.sha256(a.shape_input.read_bytes()).hexdigest(),
                      'shape_provenance':shapes,
                      'CUDA_initialized':torch.cuda.is_initialized(),'GPU_submissions':0,'RV_labels':0,
                      'D2H_H2D_or_GPU_snapshot_timing_measured':False,
                      'complete_GPU_cost_or_peak_bound_validated':False}))


if __name__=='__main__':main()
