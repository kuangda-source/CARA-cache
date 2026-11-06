"""One new bounded source-scalar CPU stage; original P0 GPU stays untouched."""
from pathlib import Path
import subprocess
import sys

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture
from cara_source_lifecycle_p0_entry_linux_cpu_r1 import OVERLAY as P0, REMOTE as P0_REMOTE
from cara_source_lifecycle_linux_cpu_r2 import OVERLAY as V1

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-source-lifecycle-V1-scalar-CPU-a6000-r1-20261102'
OVERLAY = tuple(dict.fromkeys(P0+V1+(
    'src/wcomr/cara_source_lifecycle_estimation_r1.py',
    'src/wcomr/cara_source_lifecycle_scalar_collection_r1.py',
    'scripts/fit_cara_source_lifecycle_v1_r1.py',
    'tests/test_cara_source_lifecycle_estimation_r1.py',
    'tests/check_cara_source_lifecycle_scalar_cpu_r1.py',
    'scripts/check_cara_source_lifecycle_scalar_linux_cpu_r1.py',
    'plans/cara_next_stage_20261101/source_lifecycle/V1_CALIBRATION64_DESIGN_R1.json',
    'plans/cara_next_stage_20261101/source_lifecycle/V1_PROTOCOL_R1.json',
    'plans/cara_next_stage_20261101/source_lifecycle/V1_FIXED_ESTIMATION_COMPONENT_CONTRACT_R1.json',
)))
assert P0_REMOTE.count('check_cara_source_lifecycle_p0_entry_linux_cpu_r1.py') == 1
REMOTE = P0_REMOTE.replace('check_cara_source_lifecycle_p0_entry_linux_cpu_r1.py',
                           'check_cara_source_lifecycle_scalar_linux_cpu_r1.py')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'prepare':
        sys.argv.pop(1)
        transfer.main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE,
                      transfer_label='cara-V1-scalar-CPU-transfer', connect_timeout=60, probe_peer=True)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale', 'ping',
                        '--until-direct=false', '--c', '1', '--timeout', '5s', '100.103.229.16'],
                       capture_output=True, text=True, timeout=12)
        capture(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60,
                ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
                connect_timeout=60)
