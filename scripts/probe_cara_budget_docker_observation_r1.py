"""Read-only exact missing-container observation on an original registered host."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time
from cara_two_card_transport_r1 import password

ROOT=Path(__file__).resolve().parents[1]
SOURCE='src/wcomr/cara_budget_lifecycle_capture_r1.py'
NAME='cara-budget-calibration-GPU-observation-only-r1-20261030-gpu'
REMOTE='''import ast,hashlib,json,subprocess,sys,time
p=json.load(sys.stdin)
assert p['name']=='cara-budget-calibration-GPU-observation-only-r1-20261030-gpu'
assert hashlib.sha256(p['source'].encode()).hexdigest()==p['source_sha256']
tree=ast.parse(p['source']);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect_container'];assert len(nodes)==1
calls=[];run=subprocess.run
def observed_run(*args,**kwargs):
 assert args[0]==['docker','inspect','--type','container',p['name']]
 result=run(*args,**kwargs);calls.append(dict(argv=args[0],exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr));return result
def require(value,message):
 if not value:raise ValueError(message)
subprocess.run=observed_run
exec(compile(ast.Module(body=nodes,type_ignores=[]),p['source_ref'],'exec'))
result=inspect_container(p['name'])
assert result is None and len(calls)==1
print(json.dumps(dict(status='EXACT_DOCKER_ABSENCE_OBSERVED_READONLY',host=p['host'],source_sha256=p['source_sha256'],name=p['name'],calls=calls,normalized_result=result,observed_unix=time.time(),GPU_submissions=0,ledger_written=False,container_created=False)))
'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['four_card','two_card'],required=True)
    parser.add_argument('--ssh-config',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists() and not args.ssh_config.stat().st_mode&0o077
    raw=(ROOT/SOURCE).read_text();payload=dict(host=args.host,name=NAME,source=raw,source_ref=SOURCE,
        source_sha256=hashlib.sha256(raw.encode()).hexdigest())
    interpreter='python3' if args.host=='four_card' else '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
    command=shlex.quote(interpreter)+' -c '+shlex.quote(REMOTE);data=json.dumps(payload);secret=None
    if args.host=='two_card':
        secret=password();command="sudo -S -p '' -u gaokuangda -g docker "+command;data=secret+'\n'+data
    target='four_card' if args.host=='four_card' else 'two_card_lan'
    result=subprocess.run(['/usr/bin/ssh','-F',str(args.ssh_config),'-o','BatchMode=yes','-o','ConnectTimeout=45',target,command],
        input=data,text=True,capture_output=True,timeout=120)
    if result.returncode:
        error=result.stderr.replace(secret,'[REDACTED]') if secret else result.stderr
        raise RuntimeError('Read-only original Docker probe failed: '+error[-1200:])
    receipt=json.loads(result.stdout)
    assert receipt['host']==args.host and receipt['source_sha256']==payload['source_sha256'] and receipt['normalized_result'] is None
    receipt.update(probe_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),observed_locally_unix=time.time())
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(host=args.host,status=receipt['status'])))


if __name__=='__main__':main()
