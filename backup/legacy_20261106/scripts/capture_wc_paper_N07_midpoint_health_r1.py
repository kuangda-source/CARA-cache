#!/usr/bin/env python3
"""One schedule-bound N07 health observation; no preliminary scientific data."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

LAUNCH='reports/wc_paper_N07_frozen_shared180_GPU_launch_20261016.json'
ADMISSION='reports/wc_paper_N07_full180_independent_admission_acceptance_20261016.json'
SCHEDULE='reports/wc_paper_N07_midpoint_and_final_schedule_20261016.json'
OUTPUT='reports/wc_paper_N07_midpoint_health_20261016_2130.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_binding(root):
    root=Path(root)
    sys.path.insert(0,str(root/'src'))
    from wcomr.frozen_shared_health_r1 import bind
    launch=json.loads((root/LAUNCH).read_text())['dispatch']
    admission=json.loads((root/ADMISSION).read_text());schedule=json.loads((root/SCHEDULE).read_text())
    capture=root/admission['capture_ref']
    if sha(capture)!=admission['capture_sha256']:raise ValueError('Original admission capture differs')
    admitted=json.loads(gzip.decompress(capture.read_bytes()))
    return bind(launch,admission,admitted,schedule)


def collect(expected,output,*,now=None,execute=None):
    from wcomr.frozen_shared_health_r1 import check_window,remote_code
    output=Path(output)
    if output.exists():
        value=json.loads(output.read_text())
        if value.get('expected')!=expected:raise ValueError('An existing midpoint receipt belongs to another launch')
        return value,False
    check_window(expected,time.time() if now is None else now)
    fence=output.with_name(output.name+'.attempt')
    with fence.open('x') as handle:
        json.dump(dict(expected=expected,collector_pid=os.getpid(),
            attempted_local_unix=time.time(),single_observation=True),handle,indent=2)
    command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes',
        'gkd_minchen','python3 -c '+shlex.quote(remote_code(expected))]
    execute=subprocess.run if execute is None else execute
    try:
        call=execute(command,capture_output=True,timeout=45)
        if call.returncode:
            value=dict(status='N07_MIDPOINT_TRANSPORT_OR_COMMAND_UNKNOWN_NO_RESTART',expected=expected,
                observed_local_unix=time.time(),transport_exit_code=call.returncode,
                stderr=call.stderr.decode(errors='replace')[-4096:],original_task_terminal=False,
                final_scientific_results_read=False,GPU_submissions=0,ledger_written=False)
        else:
            value=json.loads(call.stdout)
            if (value.get('expected')!=expected or value.get('status')!='N07_MIDPOINT_READONLY_TECHNICAL_HEALTH'
                    or value.get('final_scientific_results_read') is not False
                    or value.get('no_quality_or_method_latency_readout') is not True
                    or set(value.get('original_processes',{}))!={'supervisor','runner','CPU_post'}
                    or not expected['health_not_before_unix']<=value.get('observed_unix',0)<expected['final_not_before_unix']):
                raise ValueError('The midpoint reply differs from the original technical-only scope')
    except (subprocess.TimeoutExpired,OSError,ValueError) as error:
        value=dict(status='N07_MIDPOINT_OBSERVATION_UNKNOWN_NO_RESTART',expected=expected,
            observed_local_unix=time.time(),error_type=type(error).__name__,error=str(error)[-4096:],
            original_task_terminal=False,final_scientific_results_read=False,GPU_submissions=0,ledger_written=False)
    # A failed observation is retained too. It never authorizes restarting the
    # original task; connection diagnosis/re-observation uses a new receipt.
    with output.open('x') as handle:json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')
    return value,True


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();root=args.project.resolve();expected=expected_binding(root)
    output=args.output or root/OUTPUT
    value,queried=collect(expected,output)
    print(json.dumps(dict(receipt=str(output),new_SSH_observation_attempted=queried,
        status=value['status'],technical_classification=value.get('technical_classification'),
        technical_progress=value.get('technical_progress'),
        final_scientific_results_read=False,GPU_submissions=0)))


if __name__=='__main__':main()
