"""Prepare/capture the repaired successor source from its ended CPU parent."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

from cara_two_card_transport_r1 import password
from cara_source_lifecycle_p1_source_r1 import REMOTE
from cara_source_lifecycle_p1_control_r1 import wrapped_rpc_code

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('prepare','capture'))
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    read=lambda n:json.loads((ROOT/n).read_bytes())
    proof=read('reports/cara_v1_P1_successor_whole_CPU_accepted_r2_20261102.json')
    accepted=read('reports/cara_v1_P1_successor_identity_Linux_CPU_accepted_r2_20261102.json')
    assert proof['whole_card_CPU_accepted'] is True and proof['execution_authorized'] is False
    assert hashlib.sha256((ROOT/accepted['capture_ref']).read_bytes()).hexdigest()==accepted['capture_sha256']
    cap=read(accepted['capture_ref'])['result'];assert cap['original_host_observation']['original_live'] is False
    assert cap['host_terminal']['error'] is None and cap['payload_intact'] and cap['runtime_intact']
    assert cap['registration']['payload_sha256']==proof['payload_sha256']
    old=read('reports/cara_fast_B36_original_score_manifest_r1_20261029.json')
    project=Path('/data20t/gaokuangda/worldcache_workspace')
    environment={k:old[k] for k in ('torch_home','piq_site')}
    environment['weights_sha256']={str(Path(environment['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth'):
        '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02',
        str(project/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages/lpips/weights/v0.1/alex.pth'):
        'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'}
    payload=dict(action=args.action,stage=str(project/'.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102'),
        source_revision=proof['source_revision'],base_stage=cap['launch']['stage'],base_registration_sha256=cap['registration_sha256'],
        proof=proof,quote=read('plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R2.json'),
        storage=read('reports/cara_v1_P1_successor_storage_accepted_r2_20261102.json'),score_environment=environment)
    packet=dict(code=wrapped_rpc_code(REMOTE),arguments=payload)
    body=base64.b64encode(gzip.compress(json.dumps(packet).encode())).decode();secret=password()
    cmd="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote(
        "import sys,json,gzip,base64;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read())));exec(packet['code'])")
    private=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private'
    assert private.stat().st_mode&0o077==0
    started=time.time();child=subprocess.Popen(['ssh','-C','-F',str(private),'-o','BatchMode=yes','-o','ConnectTimeout=60',
        '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','two_card_lan',cmd],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate((secret+'\n'+body).encode(),timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
    result=None
    if child.returncode==0:
        envelope=json.loads(out);raw=gzip.decompress(base64.b64decode(envelope['gzip_base64']))
        assert hashlib.sha256(raw).hexdigest()==envelope['sha256'];result=json.loads(raw)
    receipt=dict(action=args.action,exit_code=child.returncode,result=result,started_unix=started,observed_unix=time.time(),
        stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),
        transport_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),GPU_submissions=0,ledger_written=False,
        unknown_requires_original_capture=True)
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,status=(result or {}).get('status'),
        preparation_complete=(result or {}).get('preparation_complete'),stderr=receipt['stderr'][-1500:])))


if __name__=='__main__':main()
