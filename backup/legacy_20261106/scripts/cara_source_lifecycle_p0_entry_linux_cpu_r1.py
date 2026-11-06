"""One new point20 entry Linux CPU; preserve all original M1/V1 CPU terminals."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_read_write_entry_linux_cpu_r1 import OVERLAY as ORIGINAL, REMOTE as ORIGINAL_REMOTE
from wcomr.cara_read_write_runner_binding_r1 import required_for
from wcomr.cara_read_write_identity_r1 import P0

STAGE = 'cara-source-lifecycle-P0-point20-entry-CPU-a6000-r1-20261101'
OVERLAY = tuple(dict.fromkeys(ORIGINAL + required_for(P0) + (
    'tests/test_cara_source_lifecycle_p0_entry_r1.py',
    'scripts/check_cara_source_lifecycle_p0_entry_linux_cpu_r1.py',
    'scripts/cara_source_lifecycle_p0_entry_linux_cpu_r1.py',
    'scripts/accept_cara_source_lifecycle_p0_entry_linux_cpu_r1.py',
    'scripts/cara_read_write_control_r1.py', 'scripts/cara_source_lifecycle_p0_control_r1.py',
    'scripts/cara_read_write_source_r1.py', 'scripts/cara_source_lifecycle_p0_source_r1.py',
    'scripts/cara_read_write_storage_transport_r1.py', 'scripts/cara_source_lifecycle_p0_storage_r1.py',
    'scripts/provision_cara_read_write_storage_r1.py',
    'scripts/cara_read_write_accept_transport_r1.py', 'scripts/cara_source_lifecycle_p0_accept_transport_r1.py',
)))
REMOTE = ORIGINAL_REMOTE.replace('check_cara_read_write_entry_linux_cpu_r1.py',
                                'check_cara_source_lifecycle_p0_entry_linux_cpu_r1.py')


if __name__ == '__main__':
    main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=600,exit_seconds=60)
