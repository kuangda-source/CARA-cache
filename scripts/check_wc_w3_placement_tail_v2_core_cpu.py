#!/usr/bin/env python3
"""Only the affected R2 scope/router/composition on CPU fixtures; no model load."""
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
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU-only environment required')
    if args.output.exists(): raise ValueError('Keep previous affected CPU receipts')
    sys.path.insert(0,str(args.stage/'src'))
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**k): raise RuntimeError('CUDA initialization forbidden in R2 CPU validation')
    torch.cuda._lazy_init=forbidden
    from wcomr.rv0_placement_v2_evaluation import validate_frozen_scope
    config=json.loads((args.stage/'tail-scope.json').read_text())
    assert config['GPU_execution_selected'] is False and config['execution_scope_authority'] is None
    scope_check=validate_frozen_scope(config['scope'])
    prereg=json.loads((args.stage/'manifests/wc_w3_placement_tail_alignment_r2_preregistered_20261007.json').read_text())
    for name in ['src/wcomr/rv0_fixed_mask_v2.py','src/wcomr/rv0_placement_v2_scope.py',
                 'src/wcomr/rv0_placement_v2_causal.py','src/wcomr/rv0_placement_v2_evaluation.py']:
        assert hashlib.sha256((args.stage/name).read_bytes()).hexdigest()==prereg['source_sha256'][name]
    path=args.stage/'tests/check_rv0_placement_tail_v2_cpu.py'
    spec=importlib.util.spec_from_file_location('r2_tail_delta_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    started=time.perf_counter();fixture=module.run(args.runtime)
    assert not torch.cuda.is_initialized()
    result={'status':'R2_PREREGISTERED_CORE_DELTA_CPU_PASS_NOT_PRODUCTION_GPU_OR_METHOD_RESULT',
        'scope':scope_check,'fixture':fixture,'CPU_wall_seconds':time.perf_counter()-started,
        'CUDA_initialized':False,'GPU_submissions':0,'real_pair_feasibility':'NOT_TESTED_BY_CPU_FIXTURES'}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['status','CPU_wall_seconds','CUDA_initialized','GPU_submissions']}))


if __name__=='__main__':main()
