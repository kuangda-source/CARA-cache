"""Corrected CPU restoration run; retain the original R1 terminal unchanged."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_read_write_linux_cpu_r1 import OVERLAY, REMOTE

STAGE = 'cara-read-write-M0M1-CPU-a6000-r2-20261101'

if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
