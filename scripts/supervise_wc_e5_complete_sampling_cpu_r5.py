"""Run isolated E5 CPU prototype, without a GPU/resource/ledger writer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--revision',required=True);args=p.parse_args();stage=args.stage
    reg=json.loads((stage/'registration.json').read_text());project=stage.parents[1]
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    files=dict(reg['inherited_payload_sha256'],**reg['new_payload_sha256'])
    assert {n:sha(stage/n) for n in files}==files
    state={'status':'E5_EARLY_HEAD_CPU_RUNNING_NOT_GPU','pid':os.getpid(),
        'source_revision':args.revision,'started_unix':time.time(),
        'budget_before_sha256':sha(project/'reports/budget.json'),'GPU_submissions':0,'ledger_written':False}
    receipt=stage/'receipt.json';assert not receipt.exists()
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(receipt)
    save();start=time.monotonic()
    try:
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                 PYTHONPATH=str(stage/'src')+':'+str(stage/'tests'))
        meta_stage=project/reg['reused_Meta_stage']
        prior=json.loads((meta_stage/'receipt.json').read_text())
        row=next(x for x in prior['CPU_parts'] if x['part']=='meta')
        assert row['exit_code']==0 and not Path('/proc/'+str(row['pid'])).exists()
        assert sha(meta_stage/'CPU-artifacts/meta-result.json')==row['result_sha256']==reg['reused_Meta_result_sha256']
        assert {n:sha(meta_stage/n) for n in reg['reused_Meta_payload_sha256']}==reg['reused_Meta_payload_sha256']
        assert all(files[n]==v for n,v in reg['reused_Meta_payload_sha256'].items())
        (stage/'CPU-artifacts').mkdir(exist_ok=True)
        (stage/'CPU-artifacts/meta-result.json').write_bytes((meta_stage/'CPU-artifacts/meta-result.json').read_bytes())
        state['CPU_parts']=[dict(row,part='meta',reused_component_only=True,original_stage=str(meta_stage))]
        part='sampler';result=stage/'CPU-artifacts/sampler-result.json'
        command=[sys.executable,str(stage/'scripts/check_wc_e5_complete_sampling_cpu_r5.py'),
                 '--stage',str(stage),'--runtime',str(project/'runtime'),'--output',str(result)]
        with (stage/'sampler-CPU.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
            state['child_pid']=child.pid;row={'part':part,'pid':child.pid,'command':command};state['CPU_parts'].append(row);save()
            state['child_exit_code']=child.wait();row['exit_code']=state['child_exit_code']
        state['exit_code']=state['child_exit_code']
        if result.exists():row['result_sha256']=sha(result)
        save()
        state['status']='E5_EARLY_HEAD_CPU_EXIT0_REQUIRES_INDEPENDENT_CAPTURE' if state['exit_code']==0 else 'E5_EARLY_HEAD_CPU_FAILED_RETAIN_ATTEMPT'
        if state['exit_code']==0:
            meta=json.loads((stage/'CPU-artifacts/meta-result.json').read_text())
            result=stage/'CPU-artifacts/result.json';value=json.loads((stage/'CPU-artifacts/sampler-result.json').read_text())
            assert meta['status']=='E5_ACTUAL_NATIVE_META_HEAD_AND_WRAPPER_GUARD_CPU_PASS'
            value['actual_native_meta_head']=meta['actual_native_meta_head']
            value['native_meta_derivation_inverse_bytes_AST_equal']=meta['native_meta_derivation_inverse_bytes_AST_equal']
            value['Meta_and_Toy_sampler_used_separate_CPU_processes']=True
            result.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');state['result_sha256']=sha(result)
        assert {n:sha(stage/n) for n in files}==files
        state['payload_after_sha256']=files
    except Exception as error:
        state.update(exit_code=1,status='E5_EARLY_HEAD_CPU_FAILED_RETAIN_ATTEMPT',error=repr(error));raise
    finally:
        state.update(CPU_wall_seconds=time.monotonic()-start,ended_unix=time.time(),
            budget_after_sha256=sha(project/'reports/budget.json'),
            concurrent_GPU_may_legitimately_update_ledger=True)
        save()
    return state['exit_code']


if __name__=='__main__':raise SystemExit(main())
