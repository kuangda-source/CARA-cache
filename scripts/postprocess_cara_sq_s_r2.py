"""Bounded GPU-hidden S byte acceptance after original release and settlement."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage','capture','settlement','output'):
        p.add_argument('--'+key,type=Path,required=True)
    args=p.parse_args();sys.path.insert(0,str(args.stage/'src'))
    from wcomr.sq_s_execution_r2 import read,require
    from wcomr.sq_s_spec_r2 import RUN,SCOPE,RISK,HISTORY
    from wcomr.sq_s_terminal_r2 import audit_settlement,technical_terminal,record
    from wcomr.sq_s_artifact_terminal_r2 import check_artifacts
    from wcomr.gpu_budget_pool_v2 import sha,process_identity
    from wcomr.sq_s_stage_r2 import create
    require(not args.output.exists(),'Preserve original complete S post-release attempt')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and os.environ.get('NVIDIA_VISIBLE_DEVICES')=='void',
        'S post-release CPU must hide all GPUs')
    require(all(path.stat().st_size<=16*2**20 and not path.is_symlink() for path in (args.capture,args.settlement)),
        'Bounded original S capture and settlement required')
    started=time.monotonic();capture=read(args.capture);settlement=read(args.settlement);scope=read(args.stage/SCOPE)
    profile=record(capture,'profile');launch=record(capture,'launch');reg=record(capture,'registration')
    cpus={int(value) for value in profile['hosts'][launch['host']]['cpuset_cpus'].split(',')}
    require(len(cpus)==2 and os.sched_getaffinity(0)==cpus,'Original S post-release CPU affinity required')
    require(args.stage==Path(launch['stage']) and args.output.parent==args.stage
        and sha(__file__)==reg['payload_sha256']['scripts/postprocess_cara_sq_s_r2.py'],
        'Original registered S post-release entry and fresh stage output required')
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*2**20,16*2**20))
    signal.alarm(profile['CPU_post_wall_seconds_max']);os.nice(10)
    billing=audit_settlement(capture,scope,settlement);technical=technical_terminal(capture,scope)
    output=Path(record(capture,'storage')['output_mount'])
    require(output==args.project/'outputs'/RUN,'Original S artifact output differs')
    create(args.stage/'S-postprocess-consumed.json',dict(run_id=RUN,launch_id=launch['launch_id'],
        source_revision=launch['source_revision'],identity=process_identity(os.getpid()),output=str(args.output),
        capture_sha256=sha(args.capture),settlement_sha256=sha(args.settlement),started_unix=time.time(),
        authorizes_GPU_retry=False))
    artifacts=check_artifacts(record(capture,'collection'),output,
        collection_sha256=capture['files']['collection']['sha256'])
    require(artifacts['validator_sha256']==reg['payload_sha256']['src/wcomr/sq_s_artifact_terminal_r2.py'],
        'Original S artifact checker is unbound')
    from wcomr.sq_s_risk_post_r3 import from_validated_rows
    require(all(sha(args.stage/name)==reg['payload_sha256'][name] for name in (RISK,HISTORY)),
        'Original pre-data S risk/history bytes changed')
    rule=read(args.stage/RISK);history=read(args.stage/HISTORY);collection=record(capture,'collection')
    rows=[row for item in collection['matrix']['rows'] for row in item['result']['S_rows']]
    decisions=from_validated_rows(rows,scope,rule,history,dict(execution_identity_sha256=rule['execution_identity_sha256'],
        actual_precision_and_backend=collection['model_entry']['precision']))
    value=dict(status='S_COMPLETE_POST_RELEASE_FROZEN_RISK_AND_MASK_PROPOSALS',run_id=RUN,
        launch_id=launch['launch_id'],source_revision=launch['source_revision'],actual_GPUh=billing['actual_GPUh'],
        capture_sha256=sha(args.capture),settlement_sha256=sha(args.settlement),
        technical_acceptance=technical,artifact_acceptance=artifacts,complete_same_state_rows_accepted=108,
        original_GPU_release_accepted=True,original_financial_settlement_accepted=True,
        scientific_S_effect_established=False,risk_and_mask_proposals=decisions,
        generated_risk_mask={name:choice['dense'] for name,choice in decisions['choices'].items()},
        complete_video_deployment_or_speed_established=False,
        CPU_wall_seconds=time.monotonic()-started,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    require('torch' not in sys.modules,'Native S byte acceptance cannot import Torch')
    create(args.output,value)
    print(value['status'])


if __name__=='__main__':main()
