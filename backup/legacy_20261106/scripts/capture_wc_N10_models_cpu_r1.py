#!/usr/bin/env python3
"""Read the original model CPU handle and artifacts once after its ETA."""
import argparse
import gzip
import json
from pathlib import Path
import shlex
import subprocess
import time


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--launch-ref',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    launch=json.loads(a.launch_ref.read_text())['launch']
    if launch['status']!='N10_FULL_FIVE_METRIC_MODEL_CPU_SINGLE_DISPATCHED':
        raise ValueError('Deferred/unknown dispatch is not an original running model CPU')
    if time.time()<launch['first_collection_not_before_unix']:raise SystemExit('Before CPU ETA; no SSH')
    code='LAUNCH='+repr(launch)+'\n'+r'''
import gzip,hashlib,json,pathlib,sys,time
stage=pathlib.Path(LAUNCH['stage']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
regpath=stage/'registration.json';assert sha(regpath)==LAUNCH['registration_sha256']
reg=json.loads(regpath.read_text());assert reg['source_revision']==LAUNCH['source_revision']
try:
 fields=(pathlib.Path('/proc')/str(LAUNCH['pid'])/'stat').read_text().split(') ',1)[1].split()
 proc=dict(pid=LAUNCH['pid'],state=fields[0],start_ticks=int(fields[19]))
except FileNotFoundError:proc=dict(pid=LAUNCH['pid'],state=None,start_ticks=None)
live=proc['state'] not in (None,'Z','X') and proc['start_ticks']==LAUNCH['start_ticks']
value=dict(status='N10_ORIGINAL_FIVE_MODEL_CPU_ONCE_CAPTURE',launch=LAUNCH,observed_unix=time.time(),
 registration=reg,registration_sha256=sha(regpath),payload_verified={n:sha(stage/n)==h for n,h in reg['payload_sha256'].items()},
 process=proc,original_process_alive=live,files={},role_result_files_present=[],GPU_submissions=0,ledger_written=False)
for role in LAUNCH['roles']:
 if (stage/('CPU-model-'+role+'.json')).is_file():value['role_result_files_present'].append(role)
if not live:
 for name in ['model-resources.json','CPU-model-bundle-result.json']+['CPU-model-'+r+'.json' for r in LAUNCH['roles']]:
  path=stage/name;row=dict(exists=path.is_file())
  if path.is_file():
   raw=path.read_bytes();row['sha256']=hashlib.sha256(raw).hexdigest()
   try:row['data']=json.loads(raw)
   except Exception as error:row.update(parse_error=str(error),original_raw_hex=raw.hex())
  value['files'][name]=row
 bundle=value['files']['CPU-model-bundle-result.json'].get('data')
 if bundle is None or bundle.get('exit_code')!=0:
  logs=['CPU-model-bundle.log']+['CPU-model-'+r+'.log' for r in LAUNCH['roles']]
  value['failure_log_tails']={n:(stage/n).read_text(errors='replace')[-18000:] for n in logs if (stage/n).is_file()}
sys.stdout.buffer.write(gzip.compress(json.dumps(value,allow_nan=False).encode()))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
        'gkd_minchen','python3 -c '+shlex.quote(code)],capture_output=True,timeout=120)
    if call.returncode:raise RuntimeError(call.stderr.decode())
    value=json.loads(gzip.decompress(call.stdout));a.output.write_bytes(call.stdout)
    print(json.dumps(dict(receipt=str(a.output),original_process_alive=value['original_process_alive'],
        role_result_files_present=value['role_result_files_present'],payload_files=len(value['payload_verified']),
        GPU_submissions=0,ledger_written=False)))


if __name__=='__main__':main()
