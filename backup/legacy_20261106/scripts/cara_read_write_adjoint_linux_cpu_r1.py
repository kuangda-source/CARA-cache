"""One isolated CPU adjoint check; retain every earlier original run."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE


STAGE = 'cara-read-write-adjoint-CPU-a6000-r1-20261101'
OVERLAY = (
    'src/wcomr/cara_read_write_adjoint_r1.py',
    'src/wcomr/cara_read_write_transition_r1.py',
    'src/wcomr/cara_read_write_state_r1.py',
    'tests/test_cara_read_write_adjoint_r1.py',
    'tests/test_cara_read_write_transition_r1.py',
    'scripts/check_cara_read_write_transition_linux_cpu_r1.py',
    'scripts/check_cara_read_write_adjoint_linux_cpu_r1.py',
    'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json',
)
REMOTE = REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py',
                        'check_cara_read_write_adjoint_linux_cpu_r1.py')


if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
