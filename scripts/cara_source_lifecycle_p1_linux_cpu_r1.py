"""Fresh bounded P1 algorithm CPU; never replay any old P0/scalar process."""
from pathlib import Path
import subprocess
import sys

import cara_source_lifecycle_p0_cpu_chunk_transport_r1 as transfer
from cara_s_initialization_selector_cpu_r1 import main as capture
from cara_source_lifecycle_scalar_linux_cpu_r3 import OVERLAY as ORIGINAL, REMOTE as OLD_REMOTE

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'cara-source-lifecycle-V1-P1-algorithm-CPU-a6000-r1-20261102'
OVERLAY = tuple(dict.fromkeys(ORIGINAL+(
    'src/wcomr/cara_source_lifecycle_search_r1.py',
    'src/wcomr/cara_source_lifecycle_fit_scores_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_plan_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_requests_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_collection_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_clock_r1.py',
    'src/wcomr/cara_source_lifecycle_p1_runner_r1.py',
    'scripts/score_cara_source_lifecycle_fit_r1.py',
    'tests/test_cara_source_lifecycle_search_r1.py',
    'tests/test_cara_source_lifecycle_fit_scores_r1.py',
    'tests/test_cara_source_lifecycle_p1_collection_r1.py',
    'tests/test_cara_source_lifecycle_p1_clock_r1.py',
    'tests/check_cara_source_lifecycle_p1_loaded_cpu_r1.py',
    'scripts/check_cara_source_lifecycle_p1_linux_cpu_r1.py',
    'scripts/cara_source_lifecycle_p1_linux_cpu_r1.py',
    'reports/cara_v1_frozen_UniPC_current_input_scale_r1_20261102.json',
    'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_MANIFEST_R1.json',
    'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_INTERNAL_FIT_AND_FAIR_SEARCH_R1.json',
)))
assert OLD_REMOTE.count('check_cara_source_lifecycle_scalar_linux_cpu_r1.py') == 1
REMOTE = OLD_REMOTE.replace('check_cara_source_lifecycle_scalar_linux_cpu_r1.py',
                           'check_cara_source_lifecycle_p1_linux_cpu_r1.py')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'prepare':
        sys.argv.pop(1)
        transfer.main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE,
            transfer_label='cara-V1-P1-algorithm-CPU-transfer', connect_timeout=60, probe_peer=True,
            inherited_capture_ref='reports/cara_v1_scalar_Linux_CPU_capture_r3_20261102.json',
            work_seconds=1800, exit_seconds=60)
    else:
        subprocess.run(['/Applications/Tailscale.app/Contents/MacOS/Tailscale', 'ping',
            '--until-direct=false', '--c', '1', '--timeout', '5s', '100.103.229.16'],
            capture_output=True, text=True, timeout=12)
        capture(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=1800, exit_seconds=60,
            ssh_config=ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.p0_qos_none.private',
            connect_timeout=60)
