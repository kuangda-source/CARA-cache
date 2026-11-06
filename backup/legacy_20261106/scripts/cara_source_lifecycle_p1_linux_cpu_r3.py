"""Fresh CPU for the caller-forward fix; original R1/R2 terminals preserved."""
from pathlib import Path
import subprocess
import sys

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture
from cara_source_lifecycle_p1_linux_cpu_r2 import OVERLAY as ORIGINAL, REMOTE as OLD_REMOTE

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-source-lifecycle-V1-P1-algorithm-CPU-a6000-r3-20261102'
OVERLAY = ORIGINAL+('scripts/check_cara_source_lifecycle_p1_linux_cpu_r3.py',
                    'scripts/cara_source_lifecycle_p1_linux_cpu_r3.py')
assert OLD_REMOTE.count('check_cara_source_lifecycle_p1_linux_cpu_r1.py') == 1
REMOTE = OLD_REMOTE.replace('check_cara_source_lifecycle_p1_linux_cpu_r1.py',
                           'check_cara_source_lifecycle_p1_linux_cpu_r3.py')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'prepare':
        sys.argv.pop(1)
        transfer.main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE,
            transfer_label='cara-V1-P1-algorithm-R3-CPU-transfer', connect_timeout=60, probe_peer=True,
            inherited_capture_ref='reports/cara_v1_P1_algorithm_Linux_CPU_capture_r7_20261102.json',
            work_seconds=3600, exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale', 'ping',
            '--until-direct=false', '--c', '1', '--timeout', '5s', '100.103.229.16'],
            capture_output=True, text=True, timeout=12)
        capture(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=3600, exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
            connect_timeout=60)
