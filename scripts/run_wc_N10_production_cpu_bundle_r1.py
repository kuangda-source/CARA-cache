#!/usr/bin/env python3
"""Run all four CPU groups and actual quoted full960 entry, without models."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();stage=a.stage.resolve();sys.dont_write_bytecode=True
    sys.path[:0]=[str(stage/'src'),str(stage/'scripts')]
    from wcomr.automatic_quality_production_r1 import CONFIG,load,read
    from wcomr.automatic_quality_models_r1 import sha
    from wcomr.automatic_quality_production_cpu_r1 import PATTERNS,BUNDLE,PROOF,STATUS
    from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
    config,reg,_,accepted,*_=load(stage)
    identity=process_identity(os.getpid());commands=[];begin=time.monotonic()
    value=dict(status='N10_FULL960_PRODUCTION_CPU_RUNNING',source_revision=reg['source_revision'],
        project=str(a.project.resolve()),stage=str(stage),python_executable=sys.executable,
        registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),
        commands=commands,control_source_sha256={'tests/'+n:reg['payload_sha256']['tests/'+n] for n in PATTERNS},
        GPU_submissions=0,ledger_written=False,model_weights_loaded=0,actual_original_five_model_proof_reaccepted=False)
    if (stage/BUNDLE).exists():raise FileExistsError('Never repeat original production CPU')
    exit_code=1
    try:
        from accept_wc_N10_models_cpu_r1 import accept as accept_models
        raw=read(stage/'reports/wc_paper_N10_full_five_model_CPU_R2_collection_20261018_0230.json.gz')
        actual=accept_models(raw)
        assert actual['CPU_accepted'] and actual['accepted_models']==5 and all(accepted.get(k)==v for k,v in actual.items())
        value['actual_original_five_model_proof_reaccepted']=True
        planned=[[sys.executable,'-m','unittest','discover','-s',str(stage/'tests'),'-p',n,'-v'] for n in PATTERNS]
        planned.append([sys.executable,str(stage/'scripts/score_wc_paper_N10_full960_r1.py'),
            '--project',str(a.project.resolve()),'--stage',str(stage),'--cpu-check'])
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(stage/'src'),PYTHONDONTWRITEBYTECODE='1',
            OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        for i,command in enumerate(planned):
            tick=time.monotonic()
            with (stage/('production-CPU-command-'+str(i)+'.log')).open('x') as log:
                result=subprocess.run(command,cwd=a.project,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
            commands.append(dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-tick))
            if result.returncode:raise ValueError('Original production CPU command failed: '+str(i))
        assert 'torch' not in sys.modules
        value.update(status=STATUS,proof_sha256=sha(stage/PROOF));exit_code=0
    except BaseException as error:
        value.update(status='N10_FULL960_PRODUCTION_CPU_FAILURE_RETAINED',error_type=type(error).__name__,
            error=str(error),traceback=traceback.format_exc())
    finally:
        value.update(exit_code=exit_code,wall_seconds=time.monotonic()-begin)
        atomic_json(stage/BUNDLE,value)
        atomic_json(stage/'N10-production-CPU-exit.json',dict(exit_code=exit_code,source_revision=reg['source_revision'],
            original_CPU_identity=identity,bundle_sha256=sha(stage/BUNDLE)))
    raise SystemExit(exit_code)


if __name__=='__main__':main()
