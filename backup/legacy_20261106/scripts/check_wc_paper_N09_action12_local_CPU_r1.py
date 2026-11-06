#!/usr/bin/env python3
"""Full12-parent adapter in both local pinned Toy flows, never real model/GPU."""
import argparse
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def hash_files(paths):
    """Read original files in a bounded, stdlib-only child process."""
    absolute={n:str(Path(p).resolve()) for n,p in paths.items()}
    if any('\n' in p or '\r' in p for p in absolute.values()):
        raise ValueError('Unambiguous original file names required')
    code=("import hashlib,json,stat,sys\nfrom pathlib import Path\n"
          "result={}\nfor name in json.load(sys.stdin):\n"
          " path=Path(name)\n"
          " if not stat.S_ISREG(path.stat().st_mode): raise ValueError('Regular original files required')\n"
          " result[name]=hashlib.sha256(path.read_bytes()).hexdigest()\n"
          "print(json.dumps(result))\n")
    call=subprocess.run([sys.executable,'-S','-c',code],
        input=json.dumps(sorted(set(absolute.values()))),capture_output=True,
        text=True,timeout=30)
    if call.returncode:raise RuntimeError('Original source checksum failed: '+call.stderr[-2000:])
    found=json.loads(call.stdout)
    for digest in found.values():
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Original SHA256 output required')
    if set(found)!=set(absolute.values()):raise ValueError('Every original file must be checksummed')
    return {n:found[p] for n,p in absolute.items()}


def sha(path):return hash_files({'original':path})['original']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('runtime','stage'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    args.stage.mkdir(parents=True,exist_ok=False)
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
        PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    sys.path[:0]=[str(root/'src'),str(root/'tests')]
    accepted=json.loads((root/'reports/wc_deployment_profile_full102_local_CPU_R2_independent_acceptance_20261016.json').read_text())
    prior_path=root/accepted['capture_ref']
    if sha(prior_path)!=accepted['capture_sha256']:raise ValueError('Original accepted102 CPU capture differs')
    prior=json.loads(gzip.decompress(prior_path.read_bytes()))
    old_sources=prior['payload_actual_sha256']
    names=set(old_sources)|{
        'src/wcomr/action_price16_collection_r1.py','src/wcomr/post_probe_action_clock_r1.py',
        'src/wcomr/action_price12_execution_r1.py','tests/check_action_price12_execution_cpu_r1.py',
        'tests/check_source_phase16_sampling_cpu_r1.py',
        str(Path(__file__).relative_to(root))}
    sources=hash_files({n:root/n for n in sorted(names)})
    for n,h in old_sources.items():
        if sources[n]!=h:raise ValueError('An accepted local runtime fixture source changed: '+n)
    runtime=hash_files({str(p.relative_to(args.runtime)):p for p in args.runtime.rglob('*.py')})
    if runtime!=prior['runtime_actual_sha256']:
        raise ValueError('The complete original accepted nine-file runtime is required')
    registration=dict(status='N09_ACTION12_LOCAL_SOURCE_BOUND_CPU_ONLY',source_sha256=sources,
        runtime_root=str(args.runtime.resolve()),runtime_source_sha256=runtime,expected_actual_CPU_paths=32,
        registered_adapter_CPU_paths=24,additional_Toy_selection_reference_paths=8,
        GPU_submissions=0,ledger_written=False)
    (args.stage/'registration.json').write_text(json.dumps(registration,indent=2))
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized();load=torch.load
    def forbidden(*a,**kw):raise RuntimeError('Action12 local CPU denies CUDA/weights/downloads')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
    artifacts=args.stage.resolve()/'artifacts'
    def loader(path,**kw):
        p=Path(path).resolve();p.relative_to(artifacts)
        if kw!={'weights_only':True,'map_location':'cpu'}:raise ValueError('Only original local CPU artifacts may load')
        return load(p,**kw)
    started=time.time();code=1;result_path=args.stage/'CPU-result.json.gz'
    try:
        path=root/'tests/check_action_price12_execution_cpu_r1.py'
        spec=importlib.util.spec_from_file_location('action12_actual_local_fixture',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        value=module.run(args.runtime,loader,artifacts)
        assert value['actual_complete_CPU_paths']==32 and value['registered_adapter_CPU_paths']==24
        assert not torch.cuda.is_initialized()
        value.update(source_sha256=sources,runtime_source_sha256=runtime,CPU_wall_seconds=time.time()-started,
            CUDA_initialized=False,actual_Cosmos_production_CPU=False,GPU_submissions=0,SSH_queries=0,ledger_written=False)
        # Preserve the complete sampler result before any unrelated metadata
        # I/O. A source-check error cannot turn this into an accepted run.
        numerical=args.stage/'CPU-numerical-result.json.gz'
        with numerical.open('xb') as handle:handle.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
        assert hash_files({n:root/n for n in sources})==sources
        assert hash_files({str(p.relative_to(args.runtime)):p for p in args.runtime.rglob('*.py')})==runtime
        value['final_source_verification']=dict(passed=True,checked_source_files=len(sources),
            checked_runtime_files=len(runtime),engine='INDEPENDENT_BOUNDED_STDLIB_CHILD_SHA256')
        value['CPU_wall_seconds']=time.time()-started
        with result_path.open('xb') as handle:handle.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
        code=0
        print(json.dumps({k:value[k] for k in ('status','actual_complete_CPU_paths','actual_pairs','CPU_wall_seconds')}))
    except BaseException as error:
        (args.stage/'CPU-failure.json').write_text(json.dumps(dict(status='N09_ACTION12_LOCAL_CPU_FAILURE_RETAINED',
            error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),
            source_sha256=sources,full_scope_not_reduced=True,GPU_submissions=0),indent=2))
        raise
    finally:
        (args.stage/'CPU-exit.json').write_text(json.dumps(dict(exit_code=code,pid=os.getpid(),started_unix=started,
            ended_unix=time.time(),source_sha256=sources,result_sha256=sha(result_path) if result_path.exists() else None,
            actual_Cosmos_production_CPU=False,GPU_submissions=0,ledger_written=False),indent=2))


if __name__=='__main__':main()
