#!/usr/bin/env python3
"""Clone passed CPU stage, bind selected fields, launch a single complete8 chain."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for n in ('project','CPU-stage','selected-stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);args=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']=''
    sys.path.insert(0,str(args.CPU_stage/'src'))
    from wcomr.e1_diag8_production_r2 import CONFIG,RUN,UUID,sha,write,binding,validate,validate_selected
    c,*_=validate(args.project,args.CPU_stage)
    proof_path=args.CPU_stage/'production-CPU-receipt.json';proof=json.loads(proof_path.read_text())
    assert proof['exit_code']==proof['child_exit_code']==0 and proof['source_revision']==args.source_revision
    assert proof['config_binding_sha256']==binding(c) and proof['payload_after_sha256']==c['payload_sha256']
    assert not any(Path('/proc/'+str(pid)).exists() for pid in (proof['pid'],proof['child_pid']))
    assert not args.selected_stage.exists() and not (args.project/'outputs'/RUN).exists()
    args.selected_stage.mkdir()
    for n in list(c['payload_sha256'])+['production-CPU-receipt.json','production-CPU.log','registration.json']:
        target=args.selected_stage/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.CPU_stage/n,target)
    original_binding=binding(c)
    c.update(GPU_execution_selected=True,gpu_uuid=UUID,production_CPU_receipt_sha256=sha(proof_path))
    assert binding(c)==original_binding;write(args.selected_stage/CONFIG,c)
    validate(args.project,args.selected_stage);validate_selected(c,args.selected_stage)
    selection={'source_revision':args.source_revision,'selected_config_sha256':sha(args.selected_stage/CONFIG),
        'production_CPU_receipt_sha256':sha(args.selected_stage/'production-CPU-receipt.json'),
        'original_CPU_stage':str(args.CPU_stage),'config_binding_sha256':original_binding}
    write(args.selected_stage/'selection.json',selection)
    command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python',
        str(args.selected_stage/'scripts/supervise_wc_e1_diag8_r2.py'),'--project',str(args.project),
        '--stage',str(args.selected_stage),'--source-revision',args.source_revision]
    with (args.selected_stage/'GPU-supervisor.log').open('x') as log:
        gpu=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    post_command=['python3',str(args.selected_stage/'scripts/supervise_wc_e1_diag8_post_cpu_r2.py'),
        '--project',str(args.project),'--stage',str(args.selected_stage),'--source-revision',args.source_revision,
        '--original-supervisor-pid',str(gpu.pid)]
    with (args.selected_stage/'post-driver.log').open('x') as log:
        post=subprocess.Popen(post_command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
    value={'status':'E1_COMPLETE8_DISPATCHED_RESOURCE_ADMISSION_IN_SUPERVISOR',
        'source_revision':args.source_revision,'stage':str(args.selected_stage),'GPU_supervisor_pid':gpu.pid,
        'post_CPU_pid':post.pid,'forecast_complete_GPUh':c['forecast_complete_GPUh'],'planned_paths':8,
        'selected_config_sha256':sha(args.selected_stage/CONFIG),'observed_unix':time.time()}
    write(args.selected_stage/'GPU-launch.json',value);print(json.dumps(value))


if __name__=='__main__':main()
