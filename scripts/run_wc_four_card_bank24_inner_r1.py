#!/usr/bin/env python3
"""Container-local parent of the unchanged BANK24 neural runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from four_card_bank24_container_transport_r1 import receive,run_inherited,atomic,identity,socket_path


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    m=json.loads(a.manifest.read_text());stage=a.manifest.parent
    assert m['namespace']=='BANK24_FOURCARD_GPU_PORT_R1'
    assert m['source_revision'] and m['gpu_uuid'].startswith('GPU-')
    fd,receipt=receive(socket_path(stage),m['handoff_nonce'],hashlib.sha256(a.manifest.read_bytes()).hexdigest())
    result=dict(status='INNER_ORIGINAL_FD_ACQUIRED',identity=identity(os.getpid()),original_handoff=receipt)
    try:
        assert str(Path(receipt['path']).resolve())==str((Path(m['project'])/'.sync/gpu-locks'/(m['gpu_uuid']+'.lock')).resolve())
        environment=dict(os.environ,CUDA_VISIBLE_DEVICES=m['gpu_uuid'],WC_SCOUT_KIND='BANK24')
        remaining=m['billed_limit_GPUh']*3600-30-(time.monotonic()-m['host_start_monotonic'])
        assert remaining>0
        command=[sys.executable,'-u',str(stage/'bank24-fourcard-runner.py'),
            '--project',m['project'],'--stage',str(stage),'--source-revision',m['source_revision'],'--gpu-uuid',m['gpu_uuid']]
        with (Path(m['output'])/'GPU.log').open('x') as log:
            result.update(run_inherited(command,fd,environment,remaining,log))
        result['status']='INNER_RUNNER_EXITED'
    finally:
        os.close(fd);result['inner_FD_closed_after_child_exit']=True
        atomic(stage/'inner-supervisor.json',result)
    return result.get('exit_code',125)


if __name__=='__main__':raise SystemExit(main())
