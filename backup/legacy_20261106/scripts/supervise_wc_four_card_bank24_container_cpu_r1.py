#!/usr/bin/env python3
"""Host-side real FD broker around the accepted CPU-only Docker supervisor."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path

from four_card_bank24_container_transport_r1 import LeaseBroker,atomic


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    job=a.manifest.parent;m=json.loads(a.manifest.read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==m['supervisor_sha256']
    assert m['CPU_only'] is True and m['GPU_submissions']==0
    parent=job/'TEST_ONLY/.sync/gpu-locks';parent.mkdir(parents=True)
    path=parent/'GPU-CPU-LIFECYCLE-PROBE.lock';handle=path.open('a+')
    fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    broker=LeaseBroker(job,handle.fileno(),path,m['CPU_transport_nonce'],
        hashlib.sha256(a.manifest.read_bytes()).hexdigest(),m['run_id'])
    broker.start()
    original=(job/'legacy-supervisor.py').read_text()
    assert hashlib.sha256(original.encode()).hexdigest()==m['legacy_supervisor_sha256']
    before="args=['docker','run','--rm','--read-only'"
    after="args=['docker','run','--rm','--pid','host','--read-only'"
    assert original.count(before)==1
    adapted=original.replace(before,after)
    assert adapted.count(after)==1 and adapted.replace(after,before)==original
    mount_before="'-w',str(job)]"
    mount_after="'-w',str(job),'-v',WC_OWNED_IPC_DIR+':'+WC_OWNED_IPC_DIR+':ro']"
    assert adapted.count(mount_before)==1
    adapted=adapted.replace(mount_before,mount_after)
    assert adapted.replace(mount_after,mount_before).replace(after,before)==original
    try:
        # All resource, native-library and cache handling remains the accepted
        # supervisor's code. Only this job's explicit PID namespace is added.
        namespace={'__name__':'__main__','__file__':str(Path(__file__).resolve()),'WC_OWNED_IPC_DIR':str(broker.ipc_directory)}
        exec(compile(adapted,'<reversibly-adapted-accepted-CPU-container-supervisor>','exec'),namespace)
    finally:
        broker.close();fcntl.flock(handle,fcntl.LOCK_UN);handle.close()
        atomic(job/'host-CPU-lease-release.json',dict(status='CPU_FIXTURE_HOST_FD_RELEASED_AFTER_CONTAINER',
            actual_authoritative_UUID_lock_opened=False,fixture_lock_path=str(path),
            handoff_success=broker.record is not None,broker_failure=broker.failure,
            GPU_submissions=0,ledger_written=False))


if __name__=='__main__':main()
