#!/usr/bin/env python3
"""Read the original local CPU handle/artifacts once after the registered ETA."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    launch=json.loads(a.launch_ref.read_text());now=time.time()
    if now<launch['first_collection_not_before_unix']:
        raise ValueError('Do not collect N05 CPU before its original ETA')
    proc=subprocess.run(['ps','-p',str(launch['pid']),'-o','pid=,lstart=,stat=,command='],capture_output=True,text=True)
    alive=bool(proc.stdout.strip());same=None
    if alive:
        date=r'\w{3}\s+\w{3}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4}'
        prior=re.match(r'^\d+\s+('+date+r')\s+(.*)$',launch['process_at_admission'])
        current=re.match(r'^\s*\d+\s+('+date+r')\s+(\S+)\s+(.*)$',proc.stdout.strip())
        assert prior and current
        same=(' '.join(prior[1].split())==' '.join(current[1].split()) and prior[2]==current[3])
        alive=bool(same and current[2][0] not in ('Z','X'))
    files={}
    for name in (launch['result_ref'],launch['exit_ref'],str(Path(launch['result_ref']).with_suffix('.failure.json'))):
        path=ROOT/name
        files[name]=dict(exists=path.exists(),sha256=sha(path) if path.exists() else None,
                         data=json.loads(path.read_text()) if path.exists() else None)
    outputs=[]
    for path in sorted((ROOT/launch['artifacts_ref']).rglob('*.mp4')):
        try:data=json.loads(path.read_text());error=None
        except (UnicodeError,ValueError) as e:data=None;error=str(e)
        outputs.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bytes=path.stat().st_size,data=data,error=error))
    log=ROOT/launch['log_ref']
    v=dict(status='N05_LOCAL_CORE216_ORIGINAL_ONCE_CAPTURE',at_unix=now,launch=launch,
        launch_ref=str(a.launch_ref),launch_sha256=sha(a.launch_ref),process_stdout=proc.stdout,
        original_handle_confirmed_live_now=alive,PID_identity_matches=same,
        payload_verified={name:sha(ROOT/name)==s for name,s in launch['payload_sha256'].items()},
        files=files,mock_outputs=outputs,log_tail=log.read_text(errors='replace')[-18000:] if log.exists() else None,
        GPU_submissions=0,SSH_queries=0,ledger_written=False)
    a.output.write_bytes(gzip.compress(json.dumps(v,indent=2).encode(),mtime=0))
    print(json.dumps(dict(status=v['status'],original_handle_confirmed_live_now=alive,
        result_exists=files[launch['result_ref']]['exists'],exit_exists=files[launch['exit_ref']]['exists'],mock_outputs=len(outputs))))

if __name__=='__main__':main()
