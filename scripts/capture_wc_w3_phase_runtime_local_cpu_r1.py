#!/usr/bin/env python3
"""One local read-only collection after ETA; never SSH or task restart."""
import argparse, gzip, hashlib, json, re, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    launch=json.loads(a.launch_ref.read_text());now=time.time()
    if now<launch['first_collection_not_before_unix']:raise ValueError('Do not collect original CPU before ETA')
    proc=subprocess.run(['ps','-p',str(launch['pid']),'-o','pid=,lstart=,stat=,command='],capture_output=True,text=True)
    alive=bool(proc.stdout.strip());same=None
    if alive:
        date=r'\w{3}\s+\w{3}\s+\d+\s+\d\d:\d\d:\d\d\s+\d{4}'
        old=re.match(r'^\d+\s+('+date+r')\s+(.*)$',launch['process_at_admission'])
        current=re.match(r'^\s*\d+\s+('+date+r')\s+(\S+)\s+(.*)$',proc.stdout.strip())
        assert old and current
        same=(' '.join(old[1].split())==' '.join(current[1].split()) and old[2]==current[3])
        # A reused PID is not the original live handle.
        alive=bool(same and current[2][0] not in ('Z','X'))
    refs=[launch['result_ref'],launch['exit_ref'],str(Path(launch['result_ref']).with_suffix('.failure.json'))]
    captured={}
    for ref in refs:
        path=ROOT/ref
        captured[ref]=dict(exists=path.exists(),sha256=sha(path) if path.exists() else None,
            data=json.loads(path.read_text()) if path.exists() else None)
    log=ROOT/launch['log_ref']
    artifacts=ROOT/launch['runtime_ref'];artifacts=artifacts.parent/'artifacts'
    mock_outputs=[]
    if artifacts.exists():
        for path in sorted(artifacts.rglob('*.mp4')):
            try:data=json.loads(path.read_text());error=None
            except (ValueError,UnicodeError) as e:data=None;error=str(e)
            mock_outputs.append(dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=sha(path),data=data,error=error))
    value=dict(status='W3_LOCAL_FULL72_CPU_ONCE_CAPTURE',at_unix=now,launch_ref=str(a.launch_ref),
        launch_sha256=sha(a.launch_ref),launch=launch,process_stdout=proc.stdout,
        original_handle_confirmed_live_now=alive,PID_identity_matches=same,
        payload_verified={name:sha(ROOT/name)==digest for name,digest in launch['payload_sha256'].items()},
        files=captured,mock_outputs=mock_outputs,log_tail=log.read_text(errors='replace')[-18000:] if log.exists() else None,
        GPU_submissions=0,SSH_queries=0,ledger_written=False)
    a.output.write_bytes(gzip.compress(json.dumps(value,indent=2).encode(),mtime=0))
    print(json.dumps(dict(status=value['status'],original_handle_confirmed_live_now=alive,
        result_exists=captured[launch['result_ref']]['exists'],exit_exists=captured[launch['exit_ref']]['exists'],
        mock_outputs=len(mock_outputs))))

if __name__=='__main__':main()
