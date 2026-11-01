"""New CPU after preserving R1's missing test-fixture import terminal."""
import ast
import json
from pathlib import Path
import subprocess
import sys

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture, BASE_CAPTURE
from cara_source_lifecycle_p1_guardian_cpu_r1 import OVERLAY as ORIGINAL, REMOTE

ROOT=Path(__file__).resolve().parents[1]
STAGE='cara-source-lifecycle-P1-FIT-guardian-CPU-a6000-r2-20261102'
OVERLAY=ORIGINAL+(
    'tests/test_cara_s_endpoint_host_guardian_r1.py',
    'tests/check_cara_s_endpoint_allocation_fixture_r1.py',
    'scripts/cara_source_lifecycle_p1_guardian_cpu_r2.py',
)


def verify_test_import_closure():
    """Catch missing local test helpers before source publication or dispatch."""
    names=set(json.loads((ROOT/BASE_CAPTURE).read_bytes())['result']['registration']['payload_sha256'])|set(OVERLAY)
    pending=[n for n in OVERLAY if n.startswith('tests/') and n.endswith('.py')]
    visited=set()
    while pending:
        name=pending.pop()
        if name in visited:continue
        visited.add(name)
        assert name in names,'Test helper not registered: '+name
        for node in ast.walk(ast.parse((ROOT/name).read_bytes())):
            imports=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.module else []
            for module in imports:
                helper='tests/'+module.replace('.','/')+'.py'
                if (ROOT/helper).is_file():
                    assert helper in names,'Imported test helper missing from payload: '+helper
                    pending.append(helper)
    return sorted(visited)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='prepare':
        sys.argv.pop(1)
        verify_test_import_closure()
        transfer.main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,
            transfer_label='cara-V1-P1-FIT-guardian-R2-CPU-transfer',connect_timeout=60,probe_peer=True,
            inherited_capture_ref='reports/cara_v1_P1_guardian_FIT_Linux_CPU_capture_r1_20261102.json',
            work_seconds=600,exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale','ping',
            '--until-direct=false','--c','1','--timeout','5s','100.103.229.16'],
            capture_output=True,text=True,timeout=12)
        capture(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=600,exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
            connect_timeout=60)
