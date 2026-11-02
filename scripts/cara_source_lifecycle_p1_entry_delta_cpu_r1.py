"""One new exact-source Linux CPU delta; preserve all ended original experiments."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture,BASE_CAPTURE
from cara_source_lifecycle_p1_post_host_cpu_r1 import OVERLAY as PREVIOUS,REMOTE as HOST_REMOTE,STAGE as OLD_STAGE

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-source-lifecycle-P1-entry-delta-CPU-host-r1-20261102'
NEW=('src/wcomr/cara_source_lifecycle_p1_report_r1.py',
    'scripts/analyze_cara_source_lifecycle_p1_complete_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_figures_r1.py',
    'scripts/render_cara_source_lifecycle_p1_figures_r1.py',
    'scripts/cara_source_lifecycle_p1_control_r1.py',
    'tests/test_cara_source_lifecycle_p1_report_r1.py','tests/test_cara_source_lifecycle_p1_figures_r1.py',
    'tests/test_cara_source_lifecycle_p1_settlement_r1.py','tests/test_cara_source_lifecycle_p1_control_r1.py',
    'tests/test_cara_source_lifecycle_p1_container_r1.py','tests/test_cara_source_lifecycle_p1_supervisor_worker_r1.py',
    'scripts/check_cara_source_lifecycle_p1_entry_delta_cpu_r1.py',
    'scripts/cara_source_lifecycle_p1_entry_delta_cpu_r1.py')
OVERLAY=tuple(dict.fromkeys(PREVIOUS+NEW))
REMOTE=HOST_REMOTE.replace(OLD_STAGE,STAGE).replace('check_cara_source_lifecycle_p1_post_host_cpu_r1.py',
    'check_cara_source_lifecycle_p1_entry_delta_cpu_r1.py').replace('P1_POST_SCORE','P1_ENTRY_DELTA')
REMOTE=REMOTE.replace(" stage.mkdir(mode=0o700)"," import importlib.util\n assert importlib.util.find_spec('matplotlib') is not None,'Matplotlib CPU dependency absent before launch'\n stage.mkdir(mode=0o700)",1)
REMOTE=REMOTE.replace(" terminal=json.loads((stage/'host-terminal.json').read_bytes())",
    " previews={n:dict(sha256=sha(stage/'figure-preview'/n),base64=base64.b64encode((stage/'figure-preview'/n).read_bytes()).decode()) for n in ('quality-latency.png','complete93-curves.png')} if raw else {}\n terminal=json.loads((stage/'host-terminal.json').read_bytes())")
REMOTE=REMOTE.replace("CPU_proof=json.loads(raw) if raw else None,", "figure_preview=previews,CPU_proof=json.loads(raw) if raw else None,")
PREFLIGHT='reports/cara_v1_P1_entry_delta_packaged_local_CPU_r1_20261102.json'


def mapping():
    result=json.loads((ROOT/BASE_CAPTURE).read_bytes())['result']['registration']['payload_sha256'].copy()
    result.update({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in OVERLAY})
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in result.items())
    return result


def packaged_local_check():
    files=mapping()
    with tempfile.TemporaryDirectory(prefix='cara-P1-entry-delta-package-') as temporary:
        root=Path(temporary)
        for name in files:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
        code="""import importlib,pathlib,sys,unittest
root=pathlib.Path.cwd();sys.path[:0]=[str(root/'src'),str(root/'scripts'),str(root/'tests')]
driver=importlib.import_module('check_cara_source_lifecycle_p1_entry_delta_cpu_r1')
result=unittest.TextTestRunner(verbosity=1).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in driver.TESTS))
assert result.testsRun==26 and result.wasSuccessful() and not result.skipped
print('P1_ENTRY_DELTA_ISOLATED26_PASS')
"""
        run=subprocess.run([str(ROOT/'.sync/cara-p0-plot-python/bin/python'),'-I','-c',code],cwd=root,
            capture_output=True,text=True,timeout=90,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
        assert run.returncode==0,run.stderr[-7000:]
        assert run.stdout.strip()=='P1_ENTRY_DELTA_ISOLATED26_PASS'
    return dict(status='EXACT_REGISTERED_P1_ENTRY_DELTA_PAYLOAD_ISOLATED_LOCAL26_PASS',
        payload_sha256=files,tests_run=26,checkout_on_import_path=False,interpreter_isolated=True,stderr=run.stderr,
        source_bound_Linux_CPU_accepted=False,old_component_experiments_replayed=False,
        P1_GPU_authorized=False,GPU_submissions=0,real_four_card_accessed=False,ledger_written=False)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        sys.argv.pop(1);proof=json.loads((ROOT/PREFLIGHT).read_bytes())
        assert proof['status']=='EXACT_REGISTERED_P1_ENTRY_DELTA_PAYLOAD_ISOLATED_LOCAL26_PASS' and proof['payload_sha256']==mapping()
        transfer.main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,
            transfer_label='cara-V1-P1-entry-delta-R1-CPU-transfer',connect_timeout=60,probe_peer=True,
            inherited_capture_ref='reports/cara_v1_P1_post_host_CPU_capture_r1_20261102.json',work_seconds=1200,exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale','ping','--until-direct=false','--c','1',
            '--timeout','5s','100.103.229.16'],capture_output=True,text=True,timeout=12)
        capture(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',connect_timeout=60)
