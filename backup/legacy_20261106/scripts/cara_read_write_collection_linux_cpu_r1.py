"""One isolated full14 Linux CPU collection; never replay the component runs."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_read_write_linux_cpu_r1 import OVERLAY, REMOTE

STAGE = 'cara-read-write-full14-CPU-a6000-r1-20261101'
OVERLAY = OVERLAY + (
    'src/wcomr/cara_read_write_plan_r1.py', 'src/wcomr/cara_read_write_collection_r1.py',
    'tests/check_cara_read_write_collection_cpu_r1.py',
    'scripts/check_cara_read_write_collection_linux_cpu_r1.py',
    'plans/cara_next_stage_20261101/read_write/M1_FULL14_MANIFEST_R2.json',
)
REMOTE = REMOTE.replace('check_cara_read_write_linux_cpu_r1.py',
                        'check_cara_read_write_collection_linux_cpu_r1.py')

if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
