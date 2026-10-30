"""Actual Linux child identities; no GPU, Docker mutation or shared ledger."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
from uuid import uuid4


def main():
    parser=argparse.ArgumentParser()
    for name in ('stage','runtime','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--host',required=True);args=parser.parse_args()
    signal.alarm(120);started=time.time();sys.path[:0]=[str(args.stage/'src'),str(args.stage/'tests')]
    from wcomr.cara_budget_original_handles_r1 import ROLES,bind_original_process,observe_original_process,observe_original_handles
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    reg=json.loads((args.stage/'registration.json').read_text())
    assert not args.output.exists() and reg['host']==args.host
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert all(sha(args.stage/n)==h for n,h in reg['payload_sha256'].items())
    suite=unittest.defaultTestLoader.discover(str(args.stage/'tests'),pattern='test_cara_budget_original_handles_r1.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun==7 and not result.skipped
    children={};handles={};observations={}
    try:
        for role in ROLES:
            p=subprocess.Popen([sys.executable,'-c',"import sys;print('READY',flush=True);sys.stdin.read(1)"],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            children[role]=p;assert p.stdout.readline().strip()=='READY'
            handles[role]=bind_original_process(p.pid)
        observations['all_live']=observe_original_handles(handles)
        assert all(r['original_live'] is True for r in observations['all_live']['handles'].values())
        children['runner'].communicate('x',timeout=5)
        observations['runner_ended_others_live']=observe_original_handles(handles)
        assert observations['runner_ended_others_live']['handles']['runner']['original_live'] is False
        assert observations['runner_ended_others_live']['any_original_handle_live']
        assert not observations['runner_ended_others_live']['all_original_handles_not_live']
        for field,value in [('boot_id',str(uuid4())),('pid_namespace_inode',handles['guardian']['host_view']['pid_namespace_inode']+1)]:
            altered=copy.deepcopy(handles['guardian']);altered['host_view'][field]=value
            observations['different_'+field]=observe_original_process(altered)
            assert observations['different_'+field]['original_live'] is None
        reused=copy.deepcopy(handles['guardian']);reused['start_ticks']-=1
        observations['simulated_reused_identity_against_real_live_PID']=observe_original_process(reused)
        assert observations['simulated_reused_identity_against_real_live_PID']['reason']=='PID_REUSED_ORIGINAL_PROCESS_EXITED'
        for role,p in children.items():
            if p.poll() is None:p.communicate('x',timeout=5)
            assert p.returncode==0
        observations['all_ended']=observe_original_handles(handles)
        assert observations['all_ended']['all_original_handles_not_live']
        assert not any(observations['all_ended'][k] for k in ('dispatch_allowed','financial_settlement_allowed','scientific_read_allowed'))
        try:bind_original_process(children['runner'].pid)
        except ValueError:ended_bind_refused=True
        else:raise AssertionError('Ended process bound retrospectively')
    finally:
        for p in children.values():
            if p.poll() is None:
                p.terminate()
                try:p.communicate(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.communicate()
    assert 'torch' not in sys.modules
    proof=dict(status='ORIGINAL_PROCESS_VIEW_CPU_CONTROLS_COMPLETE_NOT_GPU',host=args.host,
        started_unix=started,ended_unix=time.time(),registration_sha256=sha(args.stage/'registration.json'),
        source_sha256=reg['payload_sha256'],tests_run=7,tests_skipped=0,real_children=4,
        original_handles=handles,observations=observations,ended_process_bind_refused=ended_bind_refused,
        simulated_PID_reuse=True,actual_OS_PID_reuse_forced=False,all_own_children_exited_zero=True,
        actual_GPU_handle_observed=False,complete_GPU_terminal_reader_accepted=False,
        GPU_submissions=0,ledger_written=False)
    with args.output.open('x') as f:json.dump(proof,f,indent=2,allow_nan=False);f.write('\n')
    signal.alarm(30);print(json.dumps({k:proof[k] for k in ['status','tests_run','real_children']}),flush=True)


if __name__=='__main__':main()
