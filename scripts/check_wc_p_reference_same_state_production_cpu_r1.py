#!/usr/bin/env python3
"""Actual new production entry plus admission/failure controls, strictly CPU."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tempfile
import shutil


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);args=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(args.stage/'src'))
    from wcomr.p_reference_same_state_production_r1 import CONFIG,UUID,binding,sha,write,admit
    from wcomr.e1_diag8_production_r2 import validate_required_assets
    c=json.loads((args.stage/CONFIG).read_text());target=args.stage/'production-CPU-receipt.json'
    assert not target.exists() and not c['GPU_execution_selected']
    r={'status':'P_REFERENCE_ACTUAL_PRODUCTION_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
        'source_revision':args.source_revision,'config_binding_sha256':binding(c),'started_unix':time.time(),
        'GPU_submissions':0,'ledger_written':False,'budget_before_sha256':sha(args.project/'reports/budget.json')}
    write(target,r);start=time.perf_counter()
    try:
        results=[];child_exits=[]
        for arm,flow in c['flow_arms'].items():
            command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',
                str(args.stage/'scripts/run_wc_p_reference_same_state_r1.py'),'--project',str(args.project),
                '--stage',str(args.stage),'--cpu-check','--arm',arm]
            logfile=args.stage/('production-CPU-'+arm+'.log')
            with logfile.open('x') as log:
                child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,cwd=args.project/'runtime',
                    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                        PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
                r.setdefault('actual_entry_children',[]).append({'arm':arm,'pid':child.pid,'command':command})
                write(target,r);code=child.wait();child_exits.append(code)
            assert code==0,arm
            values=[]
            for line in logfile.read_text().splitlines():
                try:v=json.loads(line)
                except ValueError:continue
                if isinstance(v,dict) and v.get('status')=='P_REFERENCE_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU':values.append(v)
            assert len(values)==1;v=values[0]
            assert v['config_binding_sha256']==binding(c) and v['payload_sha256']==c['payload_sha256']
            assert not v['CUDA_initialized'] and v['scope_counts']==c['scope_counts']
            assert len(v['contract_mutation_refusals'])==10 and v['guardrail_less_entry_refused']
            assert v['arm']==arm and v['flow']==flow
            assert v['per_flow_scope_counts']['total_pair_computations']==344
            assert v['production_entry_inverse_proof']['accepted_E4c_actual_entry_inverse_bytes_equal']
            results.append(v)
        assert [v['flow'] for v in results]==[False,True]
        r['child_exit_codes']=child_exits
        # Control missing/changed GPU-only startup inputs in isolated copies,
        # and prove the unchanged native topology/eval adaptation on meta.
        assets=[]
        with tempfile.TemporaryDirectory(prefix='E1_REQUIRED_ASSET_CPU_') as folder:
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
                    else:raise AssertionError('Missing or changed GPU-only startup asset admitted')
                    path.write_bytes(original)
        # Unchanged exact native topology/helper proof is reused, not repeated.
        import gzip,hashlib
        raw=gzip.decompress((args.stage/c['native_meta_CPU_receipt_ref']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==c['native_meta_CPU_receipt_raw_sha256']
        accepted=json.loads(raw);assert accepted['exit_code']==accepted['child_exit_code']==0
        mode=accepted['native_mode_meta_CPU_result']
        assert mode['parameter_count']==2059174912 and not mode['cuda_initialized']
        assert mode['contract_sha256']==c['model_mode_contract_sha256']
        assert mode['mode']['after']['training_modules']==0
        budget=copy.deepcopy(c['admission_fixture_budget'])
        fake_gpu={'uuid':UUID,'compute_cap':'8.6','memory_used_mib':24,'pids':[]}
        proof={'status':'P_REFERENCE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU','exit_code':0,'config_binding_sha256':binding(c)}
        remaining,limit=admit(c,budget,fake_gpu,proof,exact_above8_approval_verified=True)
        assert limit==remaining and remaining>c['forecast_complete_GPUh']
        cases=[]
        for label,kind,key,value in [('foreign_gpu','gpu','uuid','OTHER'),('busy_gpu','gpu','pids',[123]),
                ('insufficient_VRAM','gpu','memory_used_mib',2000),('wrong_arch','gpu','compute_cap','8.0'),
                ('insufficient_budget','ledger','used_gpu_hours',budget['cap_gpu_hours']-1),
                ('inflight','ledger','other_inflight',{}),('CPU_failed','proof','exit_code',1),
                ('CPU_other_source','proof','config_binding_sha256','BAD')]:
            b,g,t=copy.deepcopy(budget),copy.deepcopy(fake_gpu),copy.deepcopy(proof)
            {'ledger':b,'gpu':g,'proof':t}[kind][key]=value
            try:admit(c,b,g,t,exact_above8_approval_verified=True)
            except ValueError:cases.append(label)
            else:raise AssertionError('E1 admission accepted invalid case: '+label)
        try:admit(c,budget,fake_gpu,proof)
        except ValueError:cases.append('above8_missing_exact_whole_card_approval')
        else:raise AssertionError('Above8 preparation authorized GPU without direct approval')
        assert not (args.project/'outputs'/c['run_id']).exists()
        r.update(status='P_REFERENCE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',exit_code=0,CUDA_initialized=False,
            actual_entry_results=results,admission_refusals=cases,
            required_GPU_startup_asset_refusals=assets,native_mode_meta_CPU_result=mode,
            original_native_meta_CPU_proof_reused=True,
            synthetic_admission_is_not_live_GPU_admission=True,
            synthetic_above8_gate_is_not_direct_human_authorization=True,
            original_two_flow_full_sampler_CPU_proof_reused=True)
    except BaseException as error:
        r.update(status='P_REFERENCE_ACTUAL_PRODUCTION_CPU_FAILED_NOT_GPU',exit_code=1,
            error_type=type(error).__name__,error=str(error))
    finally:
        r.update(CPU_wall_seconds=time.perf_counter()-start,ended_unix=time.time(),
            payload_after_sha256={n:sha(args.stage/n) for n in c['payload_sha256']},
            budget_after_sha256=sha(args.project/'reports/budget.json'))
        if r['payload_after_sha256']!=c['payload_sha256'] or r['budget_before_sha256']!=r['budget_after_sha256']:
            r.update(status='P_REFERENCE_PRODUCTION_CPU_IDENTITY_FAILED',exit_code=1)
        write(target,r)
    print(json.dumps({k:r[k] for k in ('status','exit_code','CPU_wall_seconds','GPU_submissions')}))
    raise SystemExit(r['exit_code'])


if __name__=='__main__':main()
