#!/usr/bin/env python3
"""Local-only full72 Toy sampler check; no production imports or GPU admission."""
import argparse, hashlib, importlib.metadata, importlib.util, json, os, sys, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for name in ('runtime','artifacts','output','exit'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists() and not a.exit.exists() and not a.artifacts.exists()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0,str(ROOT/'src'))
    import torch
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('Local phase CPU forbids CUDA, downloads and weights')
    assert not torch.cuda.is_initialized();torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    original_load=torch.load;torch.load=forbidden
    source_files=['src/wcomr/w3_phase_allocation_runtime_r1.py','tests/check_w3_phase_allocation_sampling_cpu_r2.py',
        'scripts/check_wc_w3_phase_runtime_local_cpu_r2.py','manifests/wc_w3_T1_primary6_ridge1_window4_frozen_candidate_20261016.json',
        'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json','manifests/wc_math_n2_frozen_parameters_r1_20261012.json']
    binding={name:digest(ROOT/name) for name in source_files}
    runtime_binding={str(path.relative_to(a.runtime)):digest(path) for path in a.runtime.rglob('*.py')}
    started=time.time();code=1;status='W3_LOCAL_FULL72_CPU_TECHNICAL_FAILURE'
    print(json.dumps(dict(status='STARTED_LOCAL_FULL72_CPU',pid=os.getpid(),started_unix=started,expected_paths=72)),flush=True)
    try:
        spec=importlib.util.spec_from_file_location('local_phase_full72_fixture',ROOT/'tests/check_w3_phase_allocation_sampling_cpu_r2.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        def own_loader(path,**kw):
            path=Path(path).resolve();assert path.is_relative_to(a.artifacts.resolve())
            assert kw=={'weights_only':True,'map_location':'cpu'}
            return original_load(path,**kw)
        value=module.run(a.runtime,own_loader,a.artifacts)
        assert value['actual_CPU_paths']==72 and value['ordinary_pairs']==2592 and not torch.cuda.is_initialized()
        assert binding=={name:digest(ROOT/name) for name in binding}
        assert runtime_binding=={str(path.relative_to(a.runtime)):digest(path) for path in a.runtime.rglob('*.py')}
        value.update(source_sha256=binding,runtime_source_sha256=runtime_binding,
            local_environment=dict(Python=sys.version,Torch=torch.__version__,Diffusers=importlib.metadata.version('diffusers')),
            CPU_wall_seconds=time.time()-started,CUDA_initialized=False,GPU_submissions=0,SSH_queries=0,
            weights_loaded=0,ledger_written=False,production_CPU_accepted=False)
        a.output.write_text(json.dumps(value,indent=2)+'\n');code=0;status=value['status']
    except BaseException as e:
        a.output.with_suffix('.failure.json').write_text(json.dumps(dict(status=status,error_type=type(e).__name__,error=str(e),
            traceback=traceback.format_exc(),expected_paths=72,full_scope_not_shrunk=True,GPU_submissions=0,SSH_queries=0,
            source_sha256=binding,runtime_source_sha256=runtime_binding,CPU_wall_seconds=time.time()-started),indent=2)+'\n')
        raise
    finally:
        a.exit.write_text(json.dumps(dict(status=status,exit_code=code,pid=os.getpid(),started_unix=started,
            ended_unix=time.time(),result_ref=str(a.output),result_sha256=digest(a.output) if a.output.exists() else None,
            source_sha256=binding,expected_paths=72,GPU_submissions=0,SSH_queries=0,ledger_written=False),indent=2)+'\n')
    print(json.dumps(dict(status=status,CPU_wall_seconds=value['CPU_wall_seconds'],actual_CPU_paths=72)),flush=True)

if __name__=='__main__':main()
