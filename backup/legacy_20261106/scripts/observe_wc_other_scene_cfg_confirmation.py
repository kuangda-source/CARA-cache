#!/usr/bin/env python3
"""Read original Common handles and nested progress; no score or submission."""
import argparse
import json
from pathlib import Path
import subprocess


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    assert not args.output.exists()
    launch=json.loads(Path('reports/wc_other_scene_cfg_confirmation_r1_GPU_launch_20261009.json').read_text())
    source='L='+repr(launch)+'\n'+r'''
import hashlib,json,pathlib,subprocess,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=pathlib.Path(L['stage']);post=pathlib.Path(L['post_CPU_stage']);run=root/'outputs'/L['run_id']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sup=json.loads((run/'supervisor.json').read_text());cpu=json.loads((post/'receipt.json').read_text());runner=json.loads((run/'diagnostic/receipt.json').read_text())
pids=[L['supervisor_pid'],sup['child_pid'],L['post_CPU_pid']]
if cpu.get('CPU_child_pid'):pids.append(cpu['CPU_child_pid'])
commands={str(p):(pathlib.Path('/proc/'+str(p)+'/cmdline').read_bytes().replace(b'\0',b' ').decode() if pathlib.Path('/proc/'+str(p)).exists() else None) for p in pids}
config=json.loads((stage/'teacher-config.json').read_text())
assert sha(stage/'teacher-config.json')==L['config_sha256']
assert {n:sha(stage/n) for n in config['payload_sha256']}==config['payload_sha256'] and len(config['payload_sha256'])==95
assert sup['pid']==L['supervisor_pid'] and cpu['pid']==L['post_CPU_pid']
assert sup['source_revision']==cpu['source_revision']==L['source_revision']
for p in pids:
 if commands[str(p)]:assert L['stage'] in commands[str(p)] or L['post_CPU_stage'] in commands[str(p)]
parents=[]
for row in runner['teacher']['parents']:
 parents.append({'phase':row['phase'],'status':row['status'],'net_records':len(row.get('inputs',[])),'solver_records':len(row.get('solver_outputs',[])),
  'saved_artifact':row.get('artifact'),'origins':[{'label':o['label'],'status':o['status'],'pair_records':len(o.get('pairs',[])),
    'complete_pairs':sum(p.get('status')=='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT' for p in o.get('pairs',[]))} for o in row.get('origins',[])]})
budget=json.loads((root/'reports/budget.json').read_text())
print(json.dumps({'status':'ORIGINAL_COMMON_READONLY_HANDLE_PROGRESS_NOT_SCIENTIFIC_ACCEPTANCE','run_id':L['run_id'],'source_revision':L['source_revision'],
 'original_PIDs':pids,'original_live_PIDs':[p for p in pids if commands[str(p)]],'original_proc_cmdlines':commands,'GPU_status':sup['status'],'CPU_status':cpu['status'],
 'parents':parents,'parent_progress_source':'runner.teacher.parents','complete_pair_status':'COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT',
 'earlier_progress_parser_omitted_nested_teacher_or_used_wrong_pair_status':True,
 'payload95_and_config_unchanged':True,'settled_before_run_GPUh':L['budget_before']['used_gpu_hours'],
 'budget_status':budget['status'],'budget_used_field_is_live_reservation_not_actual_spent':bool(budget.get('wc_cfg_teacher_inflight')),
 'GPU':subprocess.check_output(['nvidia-smi','-i',config['gpu_uuid'],'--query-gpu=uuid,name,memory.used','--format=csv,noheader,nounits'],text=True).strip(),
 'subset_scoring_or_raw_tensor_loading':False,'GPU_submissions_by_observation':0,'observed_unix':time.time()}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=source,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    value=json.loads(call.stdout);args.output.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k!='original_proc_cmdlines'}))


if __name__=='__main__':main()
