#!/usr/bin/env python3
"""Collect the original download once after ETA; never fetch or retry a download."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--launch-ref',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    launch=json.loads(args.launch_ref.read_text())['launch']
    if time.time()<launch['first_collection_not_before_unix']:
        raise SystemExit('Before the original resource ETA; no SSH or monitoring')
    code='LAUNCH='+repr(launch)+'\n'+r'''
import hashlib,json,pathlib,time
stage=pathlib.Path(LAUNCH['stage']);registration=stage/'registration.json'
assert hashlib.sha256(registration.read_bytes()).hexdigest()==LAUNCH['registration_sha256']
assert hashlib.sha256((stage/'fetch_wc_N10_viclip_resource_r1.py').read_bytes()).hexdigest()==LAUNCH['worker_sha256']
try:
 fields=(pathlib.Path('/proc')/str(LAUNCH['pid'])/'stat').read_text().split(') ',1)[1].split()
 identity=dict(pid=LAUNCH['pid'],state=fields[0],start_ticks=int(fields[19]))
except FileNotFoundError:identity=dict(pid=LAUNCH['pid'],state=None,start_ticks=None)
live=identity['state'] not in (None,'Z','X') and identity['start_ticks']==LAUNCH['start_ticks']
result=stage/'resource-result.json';target=stage/LAUNCH['expected_weight']['name'];partial=target.with_name(target.name+'.part')
value=dict(status='N10_ORIGINAL_RESOURCE_ONCE_CAPTURE',launch=LAUNCH,observed_unix=time.time(),
 process=identity,original_process_alive=live,result=json.loads(result.read_text()) if result.is_file() else None,
 original_result_sha256=hashlib.sha256(result.read_bytes()).hexdigest() if result.is_file() else None,
 target_exists=target.is_file(),partial_bytes=partial.stat().st_size if partial.is_file() else None,
 GPU_submissions=0,ledger_written=False,server_files_written=False)
if not live and target.is_file():
 before=target.stat();h=hashlib.sha256()
 with target.open('rb') as handle:
  for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
 after=target.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
 value['independent_target_bytes']=after.st_size;value['independent_target_sha256']=h.hexdigest()
if not live and (not value['result'] or value['result']['exit_code']!=0):
 log=stage/'resource-worker.log'
 if log.is_file():value['original_log_tail']=log.read_text(errors='replace')[-8000:]
print(json.dumps(value,allow_nan=False))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
        'gkd_minchen','python3 -c '+shlex.quote(code)],capture_output=True,timeout=120)
    if call.returncode:raise RuntimeError(call.stderr.decode())
    value=json.loads(call.stdout)
    with args.output.open('x') as handle:json.dump(value,handle,indent=2,allow_nan=False)
    print(json.dumps(dict(receipt=str(args.output),original_process_alive=value['original_process_alive'],
        resource_status=value['result']['status'] if value['result'] else None,
        partial_bytes=value['partial_bytes'],GPU_submissions=0,server_files_written=False)))


if __name__=='__main__':main()
