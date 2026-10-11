#!/usr/bin/env python3
"""Actual four inputs/twenty compiled entry blocks and CPU-only admission checks."""
import argparse
import copy
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);args=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(args.stage/'src'))
    from wcomr.e3_complete64_production_r1 import (CONFIG,UUID,binding,sha,write,admit,
        protected_capacity_failure,validate_required_assets,MODE_REF,MODE_SCRIPT)
    c=json.loads((args.stage/CONFIG).read_text());target=args.stage/'production-CPU-receipt.json'
    assert not target.exists() and not c['GPU_execution_selected']
    r={'status':'E3_COMPLETE64_ACTUAL_PRODUCTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
        'source_revision':args.source_revision,'config_binding_sha256':binding(c),'started_unix':time.time(),
        'GPU_submissions':0,'ledger_written':False,'budget_before_sha256':sha(args.project/'reports/budget.json')}
    write(target,r);start=time.perf_counter()
    try:
        command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
            str(args.stage/'scripts/run_wc_e3_complete64_block_r1.py'),'--project',str(args.project),'--stage',str(args.stage),'--cpu-check']
        with (args.stage/'production-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                    PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
            r.update(child_pid=child.pid,command=command);write(target,r);r['child_exit_code']=child.wait()
        assert r['child_exit_code']==0
        results=[]
        for line in (args.stage/'production-CPU.log').read_text().splitlines():
            try:v=json.loads(line)
            except ValueError:continue
            if isinstance(v,dict) and v.get('status')=='E3_COMPLETE64_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU':results.append(v)
        assert len(results)==1;v=results[0]
        assert v['config_binding_sha256']==binding(c) and v['payload_sha256']==c['payload_sha256']
        assert not v['CUDA_initialized'] and v['scope_counts']==c['scope_counts']
        assert len(v['contract_mutation_refusals'])==15 and len(v['registered_block_derivations'])==20
        assert v['guardrail_less_entries_refused']==20
        assets=[]
        with tempfile.TemporaryDirectory(prefix='E3_REQUIRED_ASSET_CPU_') as folder:
            temporary=Path(folder)
            for n in c['required_stage_assets']:
                (temporary/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.stage/n,temporary/n)
            validate_required_assets(c,temporary)
            for name in c['required_stage_assets']:
                path=temporary/name;original=path.read_bytes()
                for action in ('missing','changed'):
                    if action=='missing':path.unlink()
                    else:path.write_bytes(original+b'CHANGED_CPU_CONTROL')
                    try:validate_required_assets(c,temporary)
                    except ValueError:assets.append({'asset':name,'control':action})
                    else:raise AssertionError('Missing or changed E3 startup asset admitted')
                    path.write_bytes(original)
        # Startup topology/eval policy is unchanged: reuse independently
        # accepted actual native meta CPU instead of repeating that forward-free check.
        proof=json.loads((args.stage/c['startup_CPU_capture_ref']).read_text())
        item=proof['files']['production-CPU-receipt.json'];z=(args.stage/item['local_path']).read_bytes()
        import hashlib
        raw=gzip.decompress(z)
        assert sha(args.stage/c['startup_CPU_capture_ref'])==c['startup_CPU_capture_sha256']
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        assert hashlib.sha256(z).hexdigest()==item['compressed_sha256']
        old=json.loads(raw);mode=old['native_mode_meta_CPU_result']
        assert proof['exit_code']==old['exit_code']==0 and proof['original_source_actual_entry_contract_and_wrapper_independently_verified']
        assert mode['parameter_count']==2059174912 and mode['mode']['before']['module_count']==1173
        assert mode['mode']['after']['training_modules']==0 and mode['contract_sha256']==c['model_mode_contract_sha256']
        assert not mode['cuda_initialized'] and not mode['weights_loaded'] and not mode['forward_executed']
        assert old['payload_after_sha256'][MODE_REF]==c['required_stage_assets'][MODE_REF]
        assert old['payload_after_sha256'][MODE_SCRIPT]==c['required_stage_assets'][MODE_SCRIPT]
        protected=[('ValueError','Dynamic complete checkpoint GPU headroom unavailable'),
            ('ValueError','Insufficient live GPU headroom before any snapshot copies'),
            ('ValueError','CPU-owned checkpoint next-copy GPU headroom unavailable: physical_restore'),
            ('ValueError','CPU-owned checkpoint next-copy GPU headroom unavailable: owned_restore')]
        unexpected=[('OutOfMemoryError','CUDA out of memory'),('ValueError','Original combined logical copy cap exceeded'),
            ('ValueError','Complete ordinary guarded calibration parent output missing'),
            ('RuntimeError','Dynamic complete checkpoint GPU headroom unavailable')]
        assert all(protected_capacity_failure(*x) for x in protected)
        assert not any(protected_capacity_failure(*x) for x in unexpected)
        budget=json.loads((args.project/'reports/budget.json').read_text())
        fake_gpu={'uuid':UUID,'compute_cap':'8.6','memory_used_mib':24,'pids':[]}
        receipt={'status':'E3_COMPLETE64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU','exit_code':0,'config_binding_sha256':binding(c)}
        try:admit(c,budget,fake_gpu,receipt)
        except ValueError as error:assert str(error)=='E3 whole above8 requires exact direct complete-card approval'
        else:raise AssertionError('Missing exact above8 authorization admitted')
        synthetic=copy.deepcopy(c);synthetic['single_job_exception_authority']={'CPU_ONLY_FIXTURE_NEVER_SELECTED':True}
        remaining,limit=admit(synthetic,budget,fake_gpu,receipt);assert limit==remaining>c['forecast_complete_GPUh']
        cases=[]
        for label,kind,key,value in [('foreign_gpu','gpu','uuid','OTHER'),('busy_gpu','gpu','pids',[123]),
                ('insufficient_VRAM','gpu','memory_used_mib',2000),('wrong_arch','gpu','compute_cap','8.0'),
                ('insufficient_budget','ledger','used_gpu_hours',budget['cap_gpu_hours']-1),
                ('inflight','ledger','other_inflight',{}),('CPU_failed','proof','exit_code',1),
                ('CPU_other_source','proof','config_binding_sha256','BAD')]:
            b,g,t=copy.deepcopy(budget),copy.deepcopy(fake_gpu),copy.deepcopy(receipt)
            {'ledger':b,'gpu':g,'proof':t}[kind][key]=value
            try:admit(synthetic,b,g,t)
            except ValueError:cases.append(label)
            else:raise AssertionError('E3 admission accepted invalid control: '+label)
        import importlib.util
        test_path=args.stage/'tests/check_e3_complete64_supervisor_cpu_r1.py'
        test_spec=importlib.util.spec_from_file_location('E3_supervisor_affected_CPU',test_path)
        test=importlib.util.module_from_spec(test_spec);test_spec.loader.exec_module(test)
        lifecycle=test.run(args.stage,c);assert len(lifecycle)==4
        r.update(status='E3_COMPLETE64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',exit_code=0,CUDA_initialized=False,
            actual_entry_result=v,admission_refusals=cases,missing_above8_exact_authorization_refused=True,
            required_GPU_startup_asset_refusals=assets,unchanged_native_meta_CPU_result_reused=mode,
            protected_failure_classification_controls={'known_capacity':protected,'unexpected_stops_remaining_scope':unexpected},
            synthetic_admission_is_not_live_GPU_admission=True,no_authorization_or_selected_file_created=True,
            actual_full20_supervisor_CPU_lifecycle_controls=lifecycle)
    except BaseException as error:
        r.update(status='E3_COMPLETE64_ACTUAL_PRODUCTION_CPU_FAILED_NOT_GPU',exit_code=1,
            error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            payload_after_sha256={n:sha(args.stage/n) for n in c['payload_sha256']},
            budget_after_sha256=sha(args.project/'reports/budget.json'))
        if r['payload_after_sha256']!=c['payload_sha256'] or r['budget_before_sha256']!=r['budget_after_sha256']:
            r.update(status='E3_COMPLETE64_PRODUCTION_CPU_IDENTITY_FAILED',exit_code=1)
        write(target,r)
    print(json.dumps({k:r[k] for k in ('status','exit_code','CPU_wall_seconds','GPU_submissions')}))
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
