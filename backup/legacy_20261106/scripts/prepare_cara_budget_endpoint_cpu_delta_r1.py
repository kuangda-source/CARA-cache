"""Same frozen CPU payload, reusing byte-verified unchanged parent files."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess

from cara_budget_endpoint_cpu_hosts_r1 import ROOT, STAGES, PARENTS, NEW_FILES, REMOTE
from cara_two_card_transport_r1 import password

OLD=""" for n,encoded in p['files'].items():
  path=pathlib.Path(n);assert not path.is_absolute() and '..' not in path.parts
  raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==p['hashes'][n]
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
"""
NEW=""" for n,expected in p['hashes'].items():
  path=pathlib.Path(n);assert not path.is_absolute() and '..' not in path.parts
  raw=base64.b64decode(p['files'][n]) if n in p['files'] else (base/n).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==expected,'Original inherited or uploaded CPU source differs: '+n
  target=stage/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
"""
if REMOTE.count(OLD)!=1:
    raise ValueError('Original bounded CPU source-copy block changed')
DELTA_REMOTE=REMOTE.replace(OLD,NEW)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',choices=list(STAGES),required=True)
    parser.add_argument('--ssh-config',type=Path,required=True)
    parser.add_argument('--binding',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.binding.exists(): raise ValueError('Fresh control binding and launch receipt required')
    if args.ssh_config.stat().st_mode&0o077: raise ValueError('Private SSH configuration must remain0600')
    intent=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_ENDPOINT_CPU_FRAGMENT_R1.json').read_text())
    if intent['stages']!=STAGES: raise ValueError('Original CPU stages differ')
    for name,expected in intent['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Original frozen CPU source changed: '+name)
    parent=json.loads((ROOT/PARENTS[args.host]).read_text())
    original=parent['registration']['payload_sha256']
    paths=sorted(set(original)|set(NEW_FILES))
    raw={name:(ROOT/name).read_bytes() for name in paths}
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in raw.items()}
    upload={name:base64.b64encode(data).decode() for name,data in raw.items() if hashes[name]!=original.get(name)}
    binding=dict(status='SAME_CPU_PAYLOAD_DELTA_TRANSPORT_BOUND_BEFORE_REMOTE_CALL',host=args.host,
        stage_name=STAGES[args.host],script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(DELTA_REMOTE.encode()).hexdigest(),full_payload_sha256=hashes,
        uploaded_files=len(upload),reused_parent_files=len(paths)-len(upload),
        uploaded_raw_bytes=sum(len(raw[n]) for n in upload),full_raw_bytes=sum(map(len,raw.values())),
        base_registration_sha256=parent['registration_sha256'],GPU_submissions=0)
    with args.binding.open('x') as stream:json.dump(binding,stream,indent=2);stream.write('\n')
    payload=dict(action='prepare',host=args.host,stage_name=STAGES[args.host],
        base_stage=parent['launch']['stage'],base_registration_sha256=parent['registration_sha256'],
        parent_git_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        files=upload,hashes=hashes)
    interpreter='python3' if args.host=='four_card' else '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=shlex.quote(interpreter)+' -c '+shlex.quote(DELTA_REMOTE)
    data=json.dumps(payload);secret=None
    if args.host=='two_card':
        secret=password();command="sudo -S -p '' -u gaokuangda -g docker "+command;data=secret+'\n'+data
    target='four_card' if args.host=='four_card' else 'two_card_lan'
    child=subprocess.Popen(['/usr/bin/ssh','-F',str(args.ssh_config),'-o','BatchMode=yes','-o','ConnectTimeout=15',
        target,command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        out,err=child.communicate(data.encode(),timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGTERM);child.communicate()
        raise RuntimeError('CPU preparation transport unknown; recover this original stage before any new prepare') from None
    if child.returncode:
        message=err.decode(errors='replace');message=message.replace(secret,'[REDACTED]') if secret else message
        raise RuntimeError('CPU preparation failed; recover original stage: '+message[-1600:])
    receipt=json.loads(out)
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps(receipt))


if __name__=='__main__': main()
