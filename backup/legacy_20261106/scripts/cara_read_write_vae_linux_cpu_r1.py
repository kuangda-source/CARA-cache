"""Prepare once or recover one isolated CPU VAE-source check on two-card."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE


STAGE = 'cara-read-write-vae-CPU-a6000-r1-20261101'
OVERLAY = (
    'src/wcomr/cara_read_write_vae_r1.py',
    'tests/test_cara_read_write_vae_r1.py',
    'scripts/check_cara_read_write_transition_linux_cpu_r1.py',
    'scripts/check_cara_read_write_vae_linux_cpu_r1.py',
)
REMOTE = REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py',
                        'check_cara_read_write_vae_linux_cpu_r1.py')


if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
