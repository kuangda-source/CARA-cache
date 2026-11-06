#!/usr/bin/env python3
"""Wait for the one bound GPU terminal, then audit the entire card on CPU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','post'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--supervisor-pid',type=int,required=True);a=p.parse_args()
    c=json.loads((a.stage/'teacher-config.json').read_text());run=a.project/'outputs'/c['execution_run_id']
    scorer=a.stage/'scripts/audit_score_wc_other_scene_cfg_confirmation_cpu.py'
    assert sha(scorer)==c['payload_sha256']['scripts/audit_score_wc_other_scene_cfg_confirmation_cpu.py']
    binding={'stage':str(a.stage),'run_id':c['execution_run_id'],'source_revision':a.source_revision,
             'supervisor_pid':a.supervisor_pid,'scorer_sha256':sha(scorer),
             'config_sha256':sha(a.stage/'teacher-config.json'),'planned_scope':c['preregistration']['scope_counts']}
    assert not (a.post/'binding.json').exists();(a.post/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
    state={'status':'WAITING_FOR_BOUND_ORIGINAL_GPU_RELEASE','pid':os.getpid(),
           'bound_supervisor_pid':a.supervisor_pid,'source_revision':a.source_revision,'GPU_submissions':0,'CUDA_initialized':False}
    receipt=a.post/'receipt.json';assert not receipt.exists()
    def save():
        tmp=receipt.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(receipt)
    save();start=time.perf_counter()
    try:
        while Path('/proc/'+str(a.supervisor_pid)).exists():time.sleep(2)
        sup=json.loads((run/'supervisor.json').read_text())
        assert sup['pid']==a.supervisor_pid and sup['source_revision']==a.source_revision
        state['bound_child_pid']=sup['child_pid'];save()
        assert not Path('/proc/'+str(sup['child_pid'])).exists()
        if sup['exit_code']!=0:raise RuntimeError('Original GPU did not complete; preserve full scope without scoring a subset')
        assert sha(a.stage/'teacher-config.json')==binding['config_sha256'] and sha(scorer)==binding['scorer_sha256']
        state['status']='BOUND_GPU_RELEASED_COMPLETE_CPU_AUDIT_RUNNING';save()
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        python='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
        with (a.post/'score.log').open('x') as log:
            child=subprocess.Popen([python,str(scorer),'--project',str(a.project),'--stage',str(a.stage),
                    '--output',str(a.post/'score.json')],env=env,stdout=log,stderr=subprocess.STDOUT)
            state['CPU_child_pid']=child.pid;save();state['exit_code']=child.wait()
        if state['exit_code']:raise RuntimeError('Original complete CPU tensor/video audit failed')
        result=json.loads((a.post/'score.json').read_text())
        assert result['net_condition_witnesses_verified']==224 and result['solver_space_witnesses_verified']==76
        assert (result['local_CFG_pairs'],result['raw_tensor_count'],result['strict_repeat_groups'])==(40,120,20)
        state.update(status='TEACHER_POST_GPU_CPU_AUDIT_SCORE_COMPLETE',score_sha256=sha(a.post/'score.json'),exit_code=0)
    except BaseException as error:
        state.update(status='BOUND_ORIGINAL_GPU_OR_CPU_FAILURE_SCOPE_RETAINED',exit_code=1,error=str(error),error_type=type(error).__name__)
    finally:
        state['CPU_driver_wall_seconds_including_wait']=time.perf_counter()-start;save()
    raise SystemExit(state['exit_code'])


if __name__=='__main__':main()
