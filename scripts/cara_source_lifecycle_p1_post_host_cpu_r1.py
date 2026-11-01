"""One new actual host post-score CPU probe, with a source-complete preflight."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture,BASE_CAPTURE
from cara_source_lifecycle_p1_release_cpu_r3 import OVERLAY as ORIGINAL
from cara_source_lifecycle_fit_host_cpu_r1 import REMOTE as PREVIOUS

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-source-lifecycle-P1-post-CPU-host-r1-20261102'
NEW=(
    'src/wcomr/cara_source_lifecycle_p1_identity_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_central_r1.py','src/wcomr/cara_source_lifecycle_p1_dispatch_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_capture_r1.py','src/wcomr/cara_source_lifecycle_p1_score_capture_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_score_dispatch_r1.py','scripts/cara_source_lifecycle_p1_host_entry_r1.py',
    'scripts/cara_source_lifecycle_p1_dispatch_r1.py','scripts/cara_source_lifecycle_p1_score_bootstrap_r1.py',
    'scripts/cara_source_lifecycle_p1_container_r1.py','scripts/cara_source_lifecycle_p1_supervisor_worker_r1.py',
    'tests/check_cara_source_lifecycle_p1_outer_fixture_r1.py','tests/test_cara_source_lifecycle_p1_central_r1.py',
    'tests/test_cara_source_lifecycle_p1_dispatch_r1.py','tests/check_cara_source_lifecycle_p1_post_capture_fixture_r1.py',
    'tests/test_cara_source_lifecycle_p1_post_capture_r1.py','tests/test_cara_source_lifecycle_p1_post_probe_packet_r1.py',
    'tests/test_cara_source_lifecycle_p1_host_entry_r1.py','tests/test_cara_source_lifecycle_p1_capture_r1.py',
    'scripts/check_cara_source_lifecycle_p1_post_host_cpu_r1.py','scripts/cara_source_lifecycle_p1_post_host_cpu_r1.py',
)
OVERLAY=tuple(dict.fromkeys(ORIGINAL+NEW))
REMOTE=PREVIOUS.replace('cara-source-lifecycle-P1-FIT-host-CPU-a6000-r1-20261102',STAGE).replace(
    'check_cara_source_lifecycle_fit_host_cpu_r1.py','check_cara_source_lifecycle_p1_post_host_cpu_r1.py').replace(
    'HOST_FIT','P1_POST_SCORE')
PREFLIGHT='reports/cara_v1_P1_post_host_packaged_local_CPU_r1_20261102.json'


def mapping():
    result=json.loads((ROOT/BASE_CAPTURE).read_bytes())['result']['registration']['payload_sha256'].copy()
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in OVERLAY})
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in result.items())
    return result


def packaged_local_check():
    files=mapping()
    with tempfile.TemporaryDirectory(prefix='cara-P1-post-host-package-') as temporary:
        root=Path(temporary)
        for n in files:
            target=root/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes())
        code="""import importlib,pathlib,sys,unittest
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'src'),str(root/'scripts'),str(root/'tests')]
names=('test_cara_source_lifecycle_p1_central_r1','test_cara_source_lifecycle_p1_dispatch_r1',
       'test_cara_source_lifecycle_p1_post_capture_r1','test_cara_source_lifecycle_p1_post_probe_packet_r1',
       'test_cara_source_lifecycle_p1_host_entry_r1','test_cara_source_lifecycle_p1_capture_r1')
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names)
result=unittest.TextTestRunner(verbosity=1).run(suite)
assert result.testsRun==31 and result.wasSuccessful() and not result.skipped
importlib.import_module('check_cara_source_lifecycle_p1_post_host_cpu_r1')
print('P1_POST_HOST_ISOLATED31_PASS')
"""
        tested=subprocess.run([str(ROOT/'.sync/cara-p0-plot-python/bin/python'),'-I','-c',code],cwd=root,
            capture_output=True,text=True,timeout=90,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
        assert tested.returncode==0,tested.stderr[-7000:]
        assert tested.stdout.strip()=='P1_POST_HOST_ISOLATED31_PASS'
    return dict(status='EXACT_REGISTERED_P1_POST_HOST_PAYLOAD_ISOLATED_LOCAL31_PASS',payload_sha256=files,
        tests_run=31,checkout_on_import_path=False,interpreter_isolated=True,stderr=tested.stderr,
        actual_Docker_post_score_CPU_accepted=False,prior32_metric_worker_experiment_replayed=False,
        P1_GPU_authorized=False,GPU_submissions=0,ledger_written=False)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        sys.argv.pop(1);proof=json.loads((ROOT/PREFLIGHT).read_bytes())
        assert proof['status']=='EXACT_REGISTERED_P1_POST_HOST_PAYLOAD_ISOLATED_LOCAL31_PASS' and proof['payload_sha256']==mapping()
        transfer.main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,
            transfer_label='cara-V1-P1-post-host-R1-CPU-transfer',connect_timeout=60,probe_peer=True,
            inherited_capture_ref='reports/cara_v1_P1_release_Linux_CPU_capture_r7_20261102.json',work_seconds=1200,exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale','ping','--until-direct=false','--c','1',
                        '--timeout','5s','100.103.229.16'],capture_output=True,text=True,timeout=12)
        capture(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',connect_timeout=60)
