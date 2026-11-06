"""Fresh scalar CPU stage after the preserved R1 scheduler-fixture failure."""
from pathlib import Path
import subprocess
import sys

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture
from cara_source_lifecycle_scalar_linux_cpu_r1 import OVERLAY, REMOTE

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-source-lifecycle-V1-scalar-CPU-a6000-r2-20261102'


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'prepare':
        sys.argv.pop(1)
        transfer.main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE,
                      transfer_label='cara-V1-scalar-R2-CPU-transfer', connect_timeout=60, probe_peer=True,
                      inherited_capture_ref='reports/cara_v1_scalar_Linux_CPU_capture_r1_20261102.json')
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale', 'ping',
                        '--until-direct=false', '--c', '1', '--timeout', '5s', '100.103.229.16'],
                       capture_output=True, text=True, timeout=12)
        capture(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60,
                ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
                connect_timeout=60)
