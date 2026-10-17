#!/usr/bin/env python3
"""One technical-only midpoint observation of the original five-model CPU."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

ROLES = ['DINO', 'AMT_S', 'RAFT_THINGS', 'ViCLIP', 'MUSIQ_SPAQ']


def validate(launch, now):
    if (launch['status'] != 'N10_FULL_FIVE_METRIC_MODEL_CPU_SINGLE_DISPATCHED'
            or launch['roles'] != ROLES or launch['GPU_submissions']
            or launch['ledger_written'] or launch['paper_quality_scores_generated']):
        raise ValueError('Only the original complete five-model CPU handle')
    gate = launch['started_unix'] + 450
    if now < gate:
        raise ValueError('Before the original halfway time; no SSH or PID query')
    return gate


CODE = r'''
import hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);regpath=stage/'registration.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(regpath)==L['registration_sha256']
reg=json.loads(regpath.read_text())
assert reg['source_revision']==L['source_revision'] and reg['roles']==L['roles']
workers=['scripts/evaluate_wc_N10_models_cpu_bundle_r1.py','scripts/evaluate_wc_N10_metric_model_cpu_r1.py']
assert all(sha(stage/n)==reg['payload_sha256'][n] for n in workers)
proc=pathlib.Path('/proc')/str(L['pid'])
try:
 fields=(proc/'stat').read_text().split(') ',1)[1].split()
 p=dict(pid=L['pid'],state=fields[0],start_ticks=int(fields[19]),command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode().strip())
except FileNotFoundError:p=dict(pid=L['pid'],state=None,start_ticks=None,command=None)
same=p['start_ticks']==L['start_ticks'];live=same and p['state'] not in (None,'Z','X')
rows=[]
for role in L['roles']:
 path=stage/('CPU-model-'+role+'.json');row=dict(role=role,result_file_exists=path.is_file())
 if path.is_file():
  try:
   d=json.loads(path.read_text());row.update(status=d.get('status'),exit_code=d.get('exit_code'),error_type=d.get('error_type'))
  except Exception as e:row.update(parse_error_type=type(e).__name__,parse_error=str(e))
 rows.append(row)
bundle=stage/'CPU-model-bundle-result.json';terminal=None
if bundle.is_file():
 d=json.loads(bundle.read_text());terminal={k:d.get(k) for k in ('status','exit_code','attempted_role_slots','role_denominator','error_type','error')}
errors={}
for n in ['CPU-model-bundle.log']+['CPU-model-'+r+'.log' for r in L['roles']]:
 path=stage/n
 if path.is_file():
  with path.open('rb') as h:
   h.seek(0,2);size=h.tell();h.seek(max(0,size-65536));tail=h.read().decode(errors='replace')
  lines=[x for x in tail.splitlines() if any(k in x for k in ('Traceback','RuntimeError','AssertionError','Error:','No space left','MemoryError'))]
  if lines:errors[n]=lines[-12:]
print(json.dumps(dict(status='N10_ORIGINAL_FIVE_MODEL_CPU_MIDPOINT_TECHNICAL_ONLY',observed_unix=time.time(),source_revision=L['source_revision'],registration_sha256=sha(regpath),registered_role_denominator=5,process=p,PID_start_identity_matches=same,original_process_alive=live,worker_source_SHA_accepted=True,role_files=rows,terminal_technical_status=terminal,error_lines=errors,models_loaded_by_observer=0,weight_hashes_read_by_observer=0,paper_quality_scores_generated=0,GPU_submissions=0,ledger_written=False,scientific_final_acceptance=False),allow_nan=False))
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--launch-ref', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Existing midpoint receipt; read offline without a new query')
    raw = a.launch_ref.read_bytes(); launch = json.loads(raw)['launch']
    gate = validate(launch, time.time())
    code = 'L=' + repr(launch) + '\n' + CODE
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        '-o', 'ClearAllForwardings=yes', 'gkd_minchen', 'python3 -c ' + shlex.quote(code)],
        capture_output=True, timeout=90)
    if call.returncode:
        raise RuntimeError(call.stderr.decode())
    value = json.loads(call.stdout)
    value.update(original_launch_ref=str(a.launch_ref),
        original_launch_sha256=hashlib.sha256(raw).hexdigest(),
        midpoint_not_before_unix=gate,
        observer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with a.output.open('x') as h:
        json.dump(value, h, indent=2, allow_nan=False);h.write('\n')
    print(json.dumps({k:value[k] for k in ('status','original_process_alive','error_lines','scientific_final_acceptance')}))


if __name__ == '__main__':
    main()
