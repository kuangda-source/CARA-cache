"""Bound affected-path orchestration proof: real CPU children, no GPU or real ledger."""
import sys,os,json,hashlib,time,signal,py_compile
from pathlib import Path
s=Path(sys.argv[1]);signal.alarm(150);start=time.time();sys.path[:0]=[str(s/'src'),str(s/'scripts'),str(s/'tests')]
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
reg=json.loads((s/'registration.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert all(sha(s/n)==h for n,h in reg['payload_sha256'].items())
import torch
assert not torch.cuda.is_initialized()
def deny(*a,**k):raise RuntimeError('Admission CPU forbids CUDA')
torch.cuda._lazy_init=deny
import unittest,test_wc73_observer_r1
observer=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(test_wc73_observer_r1));assert observer.wasSuccessful()
from check_wc73_execution_cpu_r1 import run as phases
from check_wc73_whole_cpu_r1 import run as whole
r=dict(passed=True,observer_tests=observer.testsRun,phase_supervision=phases(s,s/'phase-fixtures'),whole_transition=whole(s,s/'whole-fixtures'),payload_sha256=reg['payload_sha256'],host=reg['host'],started_unix=start,ended_unix=time.time(),CUDA_initialized=torch.cuda.is_initialized(),GPU_submissions=0,authoritative_ledger_touched=False)
assert not r['CUDA_initialized'];(s/'CPU-proof.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('passed','host','started_unix','ended_unix','GPU_submissions')}))
