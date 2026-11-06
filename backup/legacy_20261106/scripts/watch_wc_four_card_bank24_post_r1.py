#!/usr/bin/env python3
"""Watch one original GPU handle; run original CPU post only after settlement."""
import argparse
import os
from pathlib import Path
import time
import traceback

from four_card_bank24_container_transport_r1 import atomic,alive,identity
from four_card_bank24_execution_tools_r1 import read,sha,verify_registration,post_conditions,cpu_container,module


def once(stage):
    stage=Path(stage);verify_registration(stage)
    L=read(stage/'scout-GPU-launch.json');project=Path(L['project']);out=project/'outputs'/L['run_id']
    with (stage/'post-watcher-once.json').open('x') as f:
        import json
        json.dump(dict(identity=identity(os.getpid()),launch_id=L['launch_id'],restore_only=True),f)
    deadline=L['started_unix']+L['billed_limit_GPUh']*3600+1800
    result=dict(status='POST_WATCHER_WAITING_ORIGINAL_GPU_EXIT',GPU_submissions=0,ledger_written=False)
    try:
        while True:
            sup=read(out/'supervisor.json') if (out/'supervisor.json').is_file() else {}
            if not alive(L['supervisor_identity']) and sup.get('status')=='SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT':
                controller=module('post_owned_GPU_state',stage/'supervise_wc_four_card_bank24_gpu_r1.py')
                state=(controller.owned_container_state(sup['container'],sup['container_manifest_sha256']) if sup.get('container') else 'ABSENT')
                post_conditions(project,stage,L,state);break
            if not alive(L['supervisor_identity']):
                raise ValueError('Original GPU supervisor exited without verified container exit and settlement; no post or replay')
            if time.time()>=deadline:raise TimeoutError('Original GPU exit/settlement not verified; CPU post was not started')
            time.sleep(5)
        observation=stage/'post-CPU-observation';observation.mkdir()
        atomic(observation/'host-snapshot.json',dict(launch=L,GPU_container_state=state,
            original_GPU_parent_exit_verified=True,settled_bill_sha256=sha(out/'billing.json')))
        with (stage/'post-started-once.json').open('x') as f:f.write('{"original_GPU_exit_and_settlement_verified":true}\n')
        meta=read(stage/'host-lifecycle-dependency.json')
        cpu=cpu_container(project,stage,observation,'post',meta['container_image_id'],timeout=7200)
        result.update(cpu['post'],CPU_container_peer_binding=cpu['host_verified_Docker_peer'],
            CPU_container_exit_verified=cpu['host_verified_CPU_container_exit'],
            post_source_sha256=sha(stage/'bank24-fourcard-post.py'),original_GPU_settled_before_post=True)
    except BaseException as error:
        result.update(status='POST_WATCHER_FAILURE_RETAINED_NO_GPU_REPLAY',exit_code=125,
            error_type=type(error).__name__,error=str(error),registered_paths=24,formal_denominator=18)
        (stage/'post-watcher-failure.log').write_text(traceback.format_exc())
    finally:atomic(stage/'post-CPU-exit.json',result)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True,type=Path);a=p.parse_args()
    result=once(a.stage);return result.get('exit_code',125)


if __name__=='__main__':raise SystemExit(main())
