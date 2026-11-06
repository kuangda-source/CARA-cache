"""Run or recover the complete current CPU matrix once per registered host."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time

from cara_budget_calibration_cpu_hosts_r2 import DELTA_REMOTE
from cara_two_card_transport_r1 import password

ROOT=Path(__file__).resolve().parents[1]
STAGES={'four_card':'cara-budget-calibration-CPU-ada-r3-20261030',
        'two_card':'cara-budget-calibration-CPU-a6000-r3-20261030'}
BASES={'four_card':'cara-budget-calibration-CPU-ada-r2-20261030',
       'two_card':'cara-Q5-Native50-CPU-a6000-r1-20261030'}
REMOTE=DELTA_REMOTE.replace('check_cara_budget_calibration_cpu_r2.py','check_cara_budget_calibration_cpu_r3.py')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','capture'])
    parser.add_argument('--host',choices=list(STAGES),required=True)
    for key in ('ssh-config','output','binding'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--package',type=Path)
    parser.add_argument('--source-revision')
    args=parser.parse_args()
    if args.output.exists() or args.binding.exists():raise ValueError('Fresh local receipts required')
    if args.ssh_config.stat().st_mode&0o077:raise ValueError('Task SSH config must remain private')
    payload=dict(action=args.action,host=args.host,stage_name=STAGES[args.host])
    binding=dict(action=args.action,host=args.host,stage_name=STAGES[args.host],started_unix=time.time(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),
        transport_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),GPU_submissions=0)
    if args.action=='prepare':
        import re
        if args.package is None or not re.fullmatch('[0-9a-f]{40}',args.source_revision or ''):
            raise ValueError('Published package and full source revision required')
        from wcomr.immutable_stage_payload_r1 import overlay_bytes,git_archive
        from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG
        plan=json.loads((args.package/'source-plan.json').read_text())
        raw=(args.package/'source.tar.gz').read_bytes()
        overlay=overlay_bytes(raw,plan)
        # Recheck every uploaded byte against the nominated published commit.
        if overlay_bytes(git_archive(ROOT,plan,args.source_revision),plan)!=overlay:
            raise ValueError('Published CPU overlay differs')
        base_path=args.package/'base-registration.json';base=json.loads(base_path.read_text())
        if hashlib.sha256(base_path.read_bytes()).hexdigest()!=plan['base_registration_sha256'] or base['host']!=args.host:
            raise ValueError('Original CPU base differs')
        full={**base['payload_sha256'],**plan['overlay_sha256']}
        payload.update(base_stage='/data20t/gaokuangda/worldcache_workspace/.sync/'+BASES[args.host],
            base_registration_sha256=plan['base_registration_sha256'],parent_git_revision=args.source_revision,
            hashes=full,files={n:base64.b64encode(b).decode() for n,b in overlay.items()},
            expected_host_config=HOST_CONFIG,minimum_available_memory_GiB=8)
        binding.update(source_revision=args.source_revision,full_payload_sha256=full,
            archive_sha256=hashlib.sha256(raw).hexdigest(),expected_host_config=HOST_CONFIG,
            work_seconds=2400,exit_seconds=60,CPU_fixture_only=True)
    with args.binding.open('x') as f:json.dump(binding,f,indent=2);f.write('\n')
    interpreter='python3' if args.host=='four_card' else '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=shlex.quote(interpreter)+' -c '+shlex.quote(REMOTE)
    data=json.dumps(payload);secret=None
    if args.host=='two_card':
        secret=password();command="sudo -S -p '' -u gaokuangda -g docker "+command;data=secret+'\n'+data
    target='four_card' if args.host=='four_card' else 'two_card_lan'
    child=subprocess.Popen(['ssh','-F',str(args.ssh_config),'-o','BatchMode=yes','-o','ConnectTimeout=60',
        '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3',target,command],stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    timed_out=False
    try:out,err=child.communicate(data.encode(),timeout=180)
    except subprocess.TimeoutExpired:
        timed_out=True;os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
    message=err.decode(errors='replace')
    if secret:message=message.replace(secret,'[REDACTED]')
    row=dict(binding,observed_unix=time.time(),exit_code=child.returncode,transport_timed_out=timed_out,
        stderr=message,result=json.loads(out) if child.returncode==0 else None,
        recovery_only_on_unknown=True)
    with args.output.open('x') as f:json.dump(row,f,indent=2);f.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,transport_timed_out=timed_out,
        output=str(args.output),status=(row['result'] or {}).get('status'))))
    raise SystemExit(0 if child.returncode==0 else 1)


if __name__=='__main__':
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    main()
