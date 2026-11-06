"""Prepare once or recover one GPU-hidden real-Alex input-VJP CPU check."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE


STAGE = 'cara-read-write-terminal-CPU-a6000-r1-20261101'
OVERLAY = (
    'src/wcomr/cara_read_write_terminal_r1.py',
    'scripts/check_cara_read_write_terminal_linux_cpu_r1.py',
)
REMOTE = REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py',
                        'check_cara_read_write_terminal_linux_cpu_r1.py')


if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
