"""Remove only the six hash-verified synthetic files from the accepted IO test."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
from cara_two_card_transport_r1 import password

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import hashlib,json,os,pathlib,subprocess,sys,time
p=packet['arguments'];stage=pathlib.Path(p['stage']);out=pathlib.Path(p['output']);target=out/'CPU-storage-probe-r1-20261031'
sha=lambda path:hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
assert sha(stage/'CPU-proof.json')==p['proof_sha256']
proof=json.loads((stage/'CPU-proof.json').read_text());assert proof['fixture_directory']==str(target)
launch=json.loads((stage/'CPU-launch.json').read_text());assert launch==p['launch']
state=json.loads(subprocess.check_output(['docker','inspect',launch['container']]))[0]['State']
assert state['Status']=='exited' and state['ExitCode']==0 and not state['Running']
receipt=stage/'CPU-storage-cleanup.json'
if receipt.exists():
 assert list(out.iterdir())==[]
 print(receipt.read_text());raise SystemExit(0)
assert not target.is_symlink() and set(x.name for x in out.iterdir())=={target.name}
assert set(x.name for x in target.iterdir())=={'native','candidate'}
files=[]
for name in ('native','candidate'):
 directory=target/name;expected=proof['original_artifacts'][name]
 assert not directory.is_symlink() and set(x.name for x in directory.iterdir())=={'identity.json','complete.json','RGB.npy'}
 for filename in ('identity.json','complete.json','RGB.npy'):
  f=directory/filename;assert f.is_file() and not f.is_symlink()
  files.append(dict(path=str(f),sha256=sha(f),bytes=f.stat().st_size))
 assert json.loads((directory/'identity.json').read_text())==expected['identity']
 assert json.loads((directory/'complete.json').read_text())==expected
 assert sha(directory/'RGB.npy')==expected['RGB_sha256']
for row in files:pathlib.Path(row['path']).unlink()
for name in ('native','candidate'):(target/name).rmdir()
target.rmdir()
fd=os.open(out,os.O_RDONLY);os.fsync(fd);os.close(fd)
assert list(out.iterdir())==[]
journal=pathlib.Path(proof['storage_contract']['journal_path'])
with journal.open('rb') as stream:
 assert all(block==bytes(len(block)) for block in iter(lambda:stream.read(2**20),b''))
result=dict(status='ACCEPTED_SYNTHETIC_RGB_FILES_REMOVED_OUTPUT_EMPTY',observed_unix=time.time(),deleted_files=files,proof_sha256=p['proof_sha256'],output_empty=True,journal_pristine=True,GPU_submissions=0,ledger_written=False)
with receipt.open('x') as stream:
 json.dump(result,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
print(json.dumps(result))
'''


def main():
    output=Path(sys.argv[1]);assert not output.exists()
    accepted=json.loads((ROOT/'reports/cara_budget_private_RGB_CPU_accepted_r1_20261031.json').read_text())
    assert accepted['status']=='TWO_CARD_PRIVATE64_FULL93_RGB_CPU_IO_ACCEPTED'
    args=dict(stage=accepted['launch']['stage'],output=accepted['storage_contract']['output_mount'],
              proof_sha256=accepted['CPU_proof_sha256'],launch=accepted['launch'])
    secret=password()
    command="sudo -S -p '' -u gaokuangda -g docker python3 -c "+shlex.quote("import sys,json;packet=json.load(sys.stdin);exec(packet['code'])")
    started=time.time()
    child=subprocess.Popen(['ssh','-C','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),
        '-o','BatchMode=yes','-o','ConnectTimeout=35','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3',
        'two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:out,err=child.communicate((secret+'\n'+json.dumps(dict(code=REMOTE,arguments=args))).encode(),timeout=100)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGTERM);out,err=child.communicate()
    report=dict(started_unix=started,observed_unix=time.time(),exit_code=child.returncode,
        result=json.loads(out) if child.returncode==0 else None,
        stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        remote_code_sha256=hashlib.sha256(REMOTE.encode()).hexdigest(),GPU_submissions=0,four_card_contacted=False)
    with output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,result=report['result'])))


if __name__=='__main__':main()
