#!/usr/bin/env python3
"""Run one complete local finite-grid fixture; offline/no weights/no server."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for name in ('runtime','artifacts','output','exit'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    assert not a.output.exists() and not a.exit.exists() and not a.artifacts.exists()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        HF_HUB_DISABLE_TELEMETRY='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(ROOT/'src'))
    import torch
    torch.set_num_threads(2)
    def forbidden(*args,**kw):raise RuntimeError('N05 local CPU forbids CUDA/model weights/downloads')
    assert not torch.cuda.is_initialized()
    original_load=torch.load
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    source_files=['src/wcomr/paper_baseline_grid_r1.py','src/wcomr/clean_speed20_r1.py',
        'tests/check_paper_baseline_grid_sampling_cpu_r1.py','scripts/check_wc_paper_N05_core216_local_cpu_r1.py',
        'manifests/wc_paper_N05_bounded_baseline_grid_preregistration_draft_20261016.json',
        'manifests/wc_paper_N05_core66_preregistration_r1_20261016.json',
        'tests/check_partial_mlp_guided_sampling_cpu_r1.py','tests/check_full_sampling.py',
        'src/wcomr/source_phase_absolute_h1_batch_r1.py','src/wcomr/simple26d_memory_r2.py',
        'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json',
        'manifests/wc_math_n2_frozen_parameters_r1_20261012.json']
    binding={n:sha(ROOT/n) for n in source_files}
    runtime_binding={str(p.relative_to(a.runtime)):sha(p) for p in a.runtime.rglob('*.py')}
    start=time.time();code=1;status='N05_CORE216_LOCAL_CPU_TECHNICAL_FAILURE'
    print(json.dumps(dict(status='N05_LOCAL_CORE216_STARTED',pid=os.getpid(),started_unix=start)),flush=True)
    try:
        spec=importlib.util.spec_from_file_location('N05_full216',ROOT/'tests/check_paper_baseline_grid_sampling_cpu_r1.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        def own_loader(path,**kw):
            path=Path(path).resolve()
            assert path.is_relative_to(a.artifacts.resolve()) and kw=={'weights_only':True,'map_location':'cpu'}
            return original_load(path,**kw)
        value=module.run(a.runtime,own_loader,a.artifacts)
        assert value['actual_CPU_paths']==216 and value['ordinary_pairs']==7360 and not torch.cuda.is_initialized()
        assert binding=={n:sha(ROOT/n) for n in binding}
        assert runtime_binding=={str(p.relative_to(a.runtime)):sha(p) for p in a.runtime.rglob('*.py')}
        value.update(source_sha256=binding,runtime_source_sha256=runtime_binding,
            CPU_wall_seconds=time.time()-start,CUDA_initialized=False,
            GPU_submissions=0,SSH_queries=0,ledger_written=False)
        a.output.write_text(json.dumps(value,indent=2)+'\n');code=0;status=value['status']
    except BaseException as error:
        a.output.with_suffix('.failure.json').write_text(json.dumps(dict(status=status,
            error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),
            source_sha256=binding,runtime_source_sha256=runtime_binding,expected_paths=216,
            full_scope_not_shrunk=True,GPU_submissions=0,SSH_queries=0,ledger_written=False),indent=2)+'\n')
        raise
    finally:
        a.exit.write_text(json.dumps(dict(status=status,exit_code=code,pid=os.getpid(),started_unix=start,
            ended_unix=time.time(),source_sha256=binding,result_ref=str(a.output),
            result_sha256=sha(a.output) if a.output.exists() else None,expected_paths=216,
            GPU_submissions=0,SSH_queries=0,ledger_written=False),indent=2)+'\n')
    print(json.dumps(dict(status=status,actual_CPU_paths=216,CPU_wall_seconds=value['CPU_wall_seconds'])),flush=True)

if __name__=='__main__':main()
