"""New CPU after isolating local-only transport imports from remote test modules."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture,BASE_CAPTURE
from cara_source_lifecycle_p1_guardian_cpu_r2 import OVERLAY as ORIGINAL,REMOTE,verify_test_import_closure

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-source-lifecycle-P1-FIT-guardian-CPU-a6000-r3-20261102'
OVERLAY=ORIGINAL+('scripts/cara_source_lifecycle_p1_guardian_cpu_r3.py',)
PREFLIGHT='reports/cara_v1_P1_guardian_FIT_packaged_local_CPU_r1_20261102.json'


def mapping():
    result=json.loads((ROOT/BASE_CAPTURE).read_bytes())['result']['registration']['payload_sha256'].copy()
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in OVERLAY})
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in result.items())
    return result


def packaged_local_check():
    """Import/run precisely the registered payload, with the checkout absent."""
    files=mapping()
    with tempfile.TemporaryDirectory(prefix='cara-P1-guardian-package-') as temporary:
        root=Path(temporary)
        for n in files:
            target=root/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes())
        code="""import json,pathlib,sys,unittest
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'src'),str(root/'scripts'),str(root/'tests')]
names=('test_cara_source_lifecycle_p1_service_r1','test_cara_source_lifecycle_p1_guardian_fit_r1',
       'test_cara_source_lifecycle_fit_broker_r1','test_cara_source_lifecycle_fit_host_cpu_r1','test_cara_read_write_entry_r1')
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names)
result=unittest.TextTestRunner(verbosity=1).run(suite)
print(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped))))
assert result.testsRun==34 and result.wasSuccessful()
"""
        interpreter=ROOT/'.sync/cara-p0-plot-python/bin/python'
        tested=subprocess.run([str(interpreter),'-I','-c',code],cwd=root,capture_output=True,text=True,
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'),timeout=90)
        assert tested.returncode==0,tested.stderr[-5000:]
        result=json.loads(tested.stdout)
    assert result['tests']==34 and result['failures']==result['errors']==0 and result['skipped']==5
    return dict(status='EXACT_REGISTERED_PAYLOAD_ISOLATED_LOCAL_CPU_PASS_LINUX_PROCESSES_PENDING',
        tests_run=34,executed_and_passed=29,Linux_process_tests_skipped=5,payload_sha256=files,
        checkout_on_import_path=False,interpreter_isolated=True,tests_stderr=tested.stderr,
        original_R1_R2_failures_preserved=True,actual_Linux_CPU_accepted=False,
        P1_GPU_authorized=False,GPU_submissions=0,ledger_written=False)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        sys.argv.pop(1)
        verify_test_import_closure()
        proof=json.loads((ROOT/PREFLIGHT).read_bytes())
        assert proof['status']=='EXACT_REGISTERED_PAYLOAD_ISOLATED_LOCAL_CPU_PASS_LINUX_PROCESSES_PENDING'
        assert proof['payload_sha256']==mapping() and proof['executed_and_passed']==29 and proof['Linux_process_tests_skipped']==5
        transfer.main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,
            transfer_label='cara-V1-P1-FIT-guardian-R3-CPU-transfer',connect_timeout=60,probe_peer=True,
            inherited_capture_ref='reports/cara_v1_P1_guardian_FIT_Linux_CPU_capture_r2_20261102.json',
            work_seconds=600,exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale','ping',
            '--until-direct=false','--c','1','--timeout','5s','100.103.229.16'],
            capture_output=True,text=True,timeout=12)
        capture(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=600,exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
            connect_timeout=60)
