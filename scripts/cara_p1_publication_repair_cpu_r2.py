"""Prepare one distinct repair CPU stage, then recover only that original."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture, BASE_CAPTURE
from cara_source_lifecycle_p1_final_cpu_r1 import OVERLAY as FINAL
from cara_source_lifecycle_fit_host_cpu_r1 import REMOTE as HOST

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-P1-publication-RPC-repair-CPU-a6000-r2-20261102'
NEW = ('src/wcomr/cara_source_lifecycle_fit_broker_r1.py',
       'scripts/cara_source_lifecycle_p1_control_r1.py',
       'src/wcomr/cara_source_lifecycle_p1_runner_binding_r1.py',
       'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_CONTAINER_PROFILE_R1.json',
       'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json',
       'tests/test_cara_source_lifecycle_p1_dispatch_r1.py',
       'tests/test_cara_p1_publication_repair_r2.py',
       'scripts/check_cara_p1_publication_repair_cpu_r2.py',
       'scripts/cara_p1_publication_repair_cpu_r2.py')
OVERLAY = tuple(dict.fromkeys(FINAL+NEW))
REMOTE = HOST.replace('cara-source-lifecycle-P1-FIT-host-CPU-a6000-r1-20261102',STAGE).replace(
    'check_cara_source_lifecycle_fit_host_cpu_r1.py','check_cara_p1_publication_repair_cpu_r2.py').replace(
    'HOST_FIT','P1_PUBLICATION_RPC_REPAIR')
PREFLIGHT = 'reports/cara_v1_P1_publication_RPC_packaged_local_CPU_r2_20261102.json'
INHERITED = 'reports/cara_v1_P1_final_CPU_capture_r1_20261102.json'


def mapping():
    files = json.loads((ROOT/BASE_CAPTURE).read_bytes())['result']['registration']['payload_sha256'].copy()
    files.update({name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in OVERLAY})
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in files.items())
    return files


def local_check():
    files = mapping()
    parent = json.loads((ROOT/INHERITED).read_bytes())['result']
    transfer.require_ended_source_parent(parent,host_parent=True)
    with tempfile.TemporaryDirectory(prefix='cara-P1-publication-repair-') as temporary:
        root = Path(temporary)
        for name in files:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
        code = "import sys,unittest;sys.path[:0]=['src','scripts','tests'];from check_cara_p1_publication_repair_cpu_r2 import TESTS;import test_cara_source_lifecycle_p1_guardian_fit_r1;r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in TESTS[:-1]));assert r.testsRun==28 and r.wasSuccessful() and not r.skipped;print('P1_REPAIR_ISOLATED28_PASS')"
        result = subprocess.run(['/Users/kuangda_gao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','-I','-c',code],
            cwd=root,capture_output=True,text=True,timeout=90,env=dict(os.environ,
                PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
        assert result.returncode==0,result.stderr[-9000:]
        assert result.stdout.strip()=='P1_REPAIR_ISOLATED28_PASS'
    return dict(status='EXACT_ISOLATED_P1_PUBLICATION_RPC_LOCAL_CPU28_PASS',tests_run=28,
        payload_sha256=files,stdout=result.stdout,stderr=result.stderr,interpreter_isolated=True,
        original_parent_ended=True,checkout_on_import_path=False,actual_Linux_identity_not_used_on_mac=True,
        Linux_only_original_guardian_controls_pending=5,
        actual_GPU_or_Docker_dispatched=False,old_experiments_replayed=False,real_metric_pairs_computed=0,
        GPU_submissions=0,ledger_written=False)


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        sys.argv.pop(1)
        proof=json.loads((ROOT/PREFLIGHT).read_bytes())
        assert proof['tests_run']==28 and proof['payload_sha256']==mapping()
        transfer.main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,
            transfer_label='cara-P1-publication-RPC-repair-R2',connect_timeout=60,probe_peer=True,
            inherited_capture_ref=INHERITED,inherited_host_parent=True,work_seconds=1200,exit_seconds=60)
    else:
        capture(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',connect_timeout=60)
