"""Original three-scene receipt/source/budget/release and video identity audit."""
import argparse
import json
import os
from pathlib import Path
import sys


def audit(project,stage,output):
    from wcomr.own_state_execution import read,validate_stage,settle_budget,reserve_budget,sha
    from wcomr.own_state_sampling import historical_bridge,decoded_rgb
    c=read(stage/'own-state-config.json');validate_stage(project,stage,project/'runtime',c,selected=True)
    s=read(output/'supervisor.json');r=read(output/'diagnostic/receipt.json')
    if (s['config']!=c or s['run_id']!=c['run_id'] or r['scope']!=c or r['run_card']!=c['card']
            or s['source_revision']!=r['source_revision'] or s['hard_wall_cap_exceeded']
            or s['exit_code']!=0 or s.get('stop_reason') or r['status']!='OWN_STATE_THREE_SCENE_TECH_PASS_REQUIRES_TERMINAL_AUDIT'
            or output.resolve()!=(project/'outputs'/c['run_id']).resolve()):raise ValueError('Full original terminal identity failed')
    expected=settle_budget(reserve_budget(s['budget_before'],c,s['pid']),s['budget_before'],c,s['wall_seconds'],s['pid'])
    if read(project/'reports/budget.json')!=s['budget_after'] or expected!=s['budget_after']:raise ValueError('Actual expense differs')
    pids=[s['pid'],s['child_pid'],r['pid']]
    if len(set(pids))!=3 or any(type(p) is not int or p<=0 or Path('/proc/'+str(p)).exists() for p in pids):
        raise ValueError('All original production handles must exit')
    release=s['release']
    if release.get('pids') or release.get('uuid')!=c['gpu_uuid'] or release.get('memory_used_mib',2048)>1024:
        raise ValueError('Release receipt incomplete')
    import fcntl
    with (project/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    old=read(stage/'reports/w1_replay_r1_runner.json');checks=[]
    if [v['name'] for v in r['cases']]!=c['sample_names']:raise ValueError('Complete original scope required')
    for case,i in zip(r['cases'],c['sample_indices']):
        obs=case['observed'];path=Path(obs['video_path'])
        if (not path.resolve().is_relative_to((output/'diagnostic/artifacts').resolve())
                or sha(path)!=obs['video_sha256'] or decoded_rgb(path)!=obs['decoded_rgb']):
            raise ValueError('Full93 artifact identity differs')
        checks.append(historical_bridge(old['cases'][i]['scalar_off'],obs,old['protocol']['samples'][i],c['fixed_CFG_calls']))
    return {'status':'OWN_STATE_FULL_TERMINAL_AUDIT_PASS','scenes':3,'observations':12,'checks':checks,
        'inclusive_GPU_seconds':s['wall_seconds'],'cumulative_GPU_hours':s['budget_after']['used_gpu_hours'],
        'all_original_PIDs_gone':True,'full93_new_video_decodes':3,'GPU_submissions':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['project','stage','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.stage/'src'));os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    torch.cuda._lazy_init=lambda *args,**kwargs:(_ for _ in ()).throw(RuntimeError('CPU audit denies CUDA'))
    value=audit(a.project,a.stage,a.output)
    if torch.cuda.is_initialized():raise ValueError('CPU audit initialized CUDA')
    print(json.dumps(value))


if __name__=='__main__':main()
