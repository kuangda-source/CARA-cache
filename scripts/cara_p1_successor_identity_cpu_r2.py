"""One separate source-bound successor CPU delta after the ended repair probe."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture,BASE_CAPTURE
from cara_p1_publication_repair_cpu_r2 import OVERLAY as REPAIR,REMOTE as PREVIOUS,STAGE as OLD_STAGE

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-P1-successor-identity-CPU-a6000-r2-20261102'
NEW=('src/wcomr/cara_source_lifecycle_p1_identity_r1.py','src/wcomr/cara_source_lifecycle_p1_runner_binding_r1.py',
 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_CONTAINER_PROFILE_R2.json',
 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R2.json',
 'tests/test_cara_source_lifecycle_p1_profile_quote_r1.py','tests/check_cara_source_lifecycle_p1_score_fixture_r1.py',
 'tests/test_cara_p1_successor_identity_r2.py','scripts/check_cara_p1_successor_identity_cpu_r2.py',
 'scripts/cara_p1_successor_identity_cpu_r2.py','scripts/provision_cara_source_lifecycle_p1_storage_r2.py',
 'scripts/cara_p1_successor_storage_r2.py',
 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_MEMORY50_AUTHORIZATION_R2.json')
OVERLAY=tuple(dict.fromkeys(REPAIR+NEW))
REMOTE=PREVIOUS.replace(OLD_STAGE,STAGE).replace('check_cara_p1_publication_repair_cpu_r2.py',
 'check_cara_p1_successor_identity_cpu_r2.py').replace('P1_PUBLICATION_RPC_REPAIR','P1_SUCCESSOR_IDENTITY')
PREFLIGHT='reports/cara_v1_P1_successor_identity_packaged_local_CPU_r2_20261102.json'
INHERITED='reports/cara_v1_P1_publication_RPC_Linux_CPU_capture_r2_20261102.json'


def mapping():
    files=json.loads((ROOT/BASE_CAPTURE).read_bytes())['result']['registration']['payload_sha256'].copy()
    files.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in OVERLAY})
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in files.items())
    return files


def local_check():
    files=mapping();transfer.require_ended_source_parent(json.loads((ROOT/INHERITED).read_bytes())['result'],host_parent=True)
    with tempfile.TemporaryDirectory(prefix='cara-P1-successor-identity-') as temporary:
        root=Path(temporary)
        for n in files:
            p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
        code="import sys,unittest,json;sys.path[:0]=['src','scripts','tests'];from check_cara_p1_successor_identity_cpu_r2 import TESTS;names=TESTS+('test_cara_source_lifecycle_p1_result_bundle_r1.P1BundleTests.test_real_local_figures_reuse_the_export_without_remote_recovery',);r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names));assert r.testsRun==57 and r.wasSuccessful() and not r.skipped;print(json.dumps(dict(tests_run=r.testsRun)))"
        checked=subprocess.run([str(ROOT/'.sync/cara-p0-plot-python/bin/python'),'-I','-c',code],
            cwd=root,capture_output=True,text=True,timeout=90,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
        assert checked.returncode==0,checked.stderr[-14000:]
        count=json.loads(checked.stdout)['tests_run']
    return dict(status='EXACT_ISOLATED_SUCCESSOR_IDENTITY_FULL_READERS_CPU_PASS',tests_run=count,
        payload_sha256=files,stdout=checked.stdout,stderr=checked.stderr,checkout_on_import_path=False,
        interpreter_isolated=True,Linux_metadata_controls=56,local_only_plot_control=1,
        real_metric_pairs_computed=0,old_experiments_replayed=False,
        new_GPU_authorized=False,GPU_submissions=0,ledger_written=False)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        sys.argv.pop(1);proof=json.loads((ROOT/PREFLIGHT).read_bytes());assert proof['payload_sha256']==mapping()
        transfer.main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,
            transfer_label='cara-P1-successor-identity-R2',connect_timeout=60,probe_peer=True,
            inherited_capture_ref=INHERITED,inherited_host_parent=True,work_seconds=1200,exit_seconds=60)
    else:
        capture(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',connect_timeout=60)
