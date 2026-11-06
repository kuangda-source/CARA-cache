"""Once-only final Linux CPU delta; inherit only the accepted ended host source."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture,BASE_CAPTURE
from cara_source_lifecycle_p1_entry_delta_cpu_r1 import OVERLAY as PREVIOUS,REMOTE as HOST_REMOTE,STAGE as OLD_STAGE

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-source-lifecycle-P1-final-entry-CPU-host-r1-20261102'
NEW=('src/wcomr/cara_source_lifecycle_p1_result_bundle_r1.py',
    'src/wcomr/cara_cpu_source_parent_r1.py',
    'scripts/cara_source_lifecycle_p1_result_bundle_r1.py',
    'tests/test_cara_source_lifecycle_p1_result_bundle_r1.py',
    'tests/test_cara_source_lifecycle_p1_profile_quote_r1.py',
    'tests/test_cara_source_lifecycle_source_parent_r1.py',
    'tests/test_cara_source_lifecycle_p1_entry_r1.py',
    'scripts/cara_source_lifecycle_p0_cpu_chunk_transport_r1.py',
    'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_CONTAINER_PROFILE_R1.json',
    'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json',
    'scripts/provision_cara_source_lifecycle_p1_storage_r1.py',
    'scripts/cara_source_lifecycle_p1_storage_r1.py','scripts/accept_cara_source_lifecycle_p1_storage_r1.py',
    'scripts/check_cara_source_lifecycle_p1_final_cpu_r1.py','scripts/cara_source_lifecycle_p1_final_cpu_r1.py')
OVERLAY=tuple(dict.fromkeys(PREVIOUS+NEW))
REMOTE=HOST_REMOTE.replace(OLD_STAGE,STAGE).replace('check_cara_source_lifecycle_p1_entry_delta_cpu_r1.py',
    'check_cara_source_lifecycle_p1_final_cpu_r1.py').replace('P1_ENTRY_DELTA','P1_FINAL_BINDING')
REMOTE=REMOTE.replace(" terminal=json.loads((stage/'host-terminal.json').read_bytes())",
    " portable=dict(sha256=sha(stage/'portable-result-bundle.json'),raw_base64=base64.b64encode((stage/'portable-result-bundle.json').read_bytes()).decode()) if raw else None\n terminal=json.loads((stage/'host-terminal.json').read_bytes())")
REMOTE=REMOTE.replace("CPU_proof=json.loads(raw) if raw else None,", "portable_result_bundle=portable,CPU_proof=json.loads(raw) if raw else None,")
PREFLIGHT='reports/cara_v1_P1_final_packaged_local_CPU_r1_20261102.json'
INHERITED='reports/cara_v1_P1_entry_delta_CPU_capture_r2_20261102.json'


def mapping():
    files=json.loads((ROOT/BASE_CAPTURE).read_bytes())['result']['registration']['payload_sha256'].copy()
    files.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in OVERLAY})
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in files.items())
    return files


def packaged_local_check():
    files=mapping();base=json.loads((ROOT/INHERITED).read_bytes())['result']
    transfer.require_ended_source_parent(base,host_parent=True)
    with tempfile.TemporaryDirectory(prefix='cara-P1-final-package-') as temporary:
        root=Path(temporary)
        for name in files:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
        code="""import pathlib,sys,unittest
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'src'),str(root/'scripts'),str(root/'tests')]
names=('test_cara_source_lifecycle_p1_result_bundle_r1','test_cara_source_lifecycle_p1_profile_quote_r1',
'test_cara_source_lifecycle_source_parent_r1',
'test_cara_source_lifecycle_p1_entry_r1.P1ProductionEntryTests.test_published_unset_hard_limit_cannot_pass_admission')
result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names))
assert result.testsRun==14 and result.wasSuccessful() and not result.skipped
print('P1_FINAL_ISOLATED14_PASS')
"""
        run=subprocess.run([str(ROOT/'.sync/cara-p0-plot-python/bin/python'),'-I','-c',code],cwd=root,
            capture_output=True,text=True,timeout=90,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
        assert run.returncode==0,run.stderr[-7000:]
        assert run.stdout.strip()=='P1_FINAL_ISOLATED14_PASS'
    return dict(status='EXACT_REGISTERED_P1_FINAL_PAYLOAD_ISOLATED_LOCAL14_PASS',payload_sha256=files,
        tests_run=14,checkout_on_import_path=False,interpreter_isolated=True,stderr=run.stderr,
        prior_component_experiments_replayed=False,whole_P1_CPU_accepted=False,P1_GPU_authorized=False,
        real_four_card_accessed=False,GPU_submissions=0,ledger_written=False)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        sys.argv.pop(1);proof=json.loads((ROOT/PREFLIGHT).read_bytes())
        assert proof['status']=='EXACT_REGISTERED_P1_FINAL_PAYLOAD_ISOLATED_LOCAL14_PASS' and proof['payload_sha256']==mapping()
        transfer.main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,
            transfer_label='cara-V1-P1-final-R1-CPU-transfer',connect_timeout=60,probe_peer=True,
            inherited_capture_ref=INHERITED,inherited_host_parent=True,work_seconds=1200,exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale','ping','--until-direct=false','--c','1',
            '--timeout','5s','100.103.229.16'],capture_output=True,text=True,timeout=12)
        capture(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',connect_timeout=60)
