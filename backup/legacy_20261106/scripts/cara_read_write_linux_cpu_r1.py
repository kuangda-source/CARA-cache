"""One affected-path two-card CPU run; capture the same handle after intent."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE

STAGE = 'cara-read-write-M0M1-CPU-a6000-r1-20261101'
OVERLAY = (
    'src/wcomr/cara_read_write_state_r1.py', 'src/wcomr/cara_read_write_proposals_r1.py',
    'src/wcomr/cara_read_write_suffix_r1.py', 'src/wcomr/cara_read_write_point_r1.py',
    'src/wcomr/cpu_owned_state_snapshot.py', 'src/wcomr/policy_generator_r1/production_sampling.py',
    'src/wcomr/cara_fast_spec_r1.py',
    'tests/test_cara_read_write_m0_r1.py', 'tests/check_cara_read_write_suffix_cpu_r1.py',
    'tests/check_cara_read_write_point_cpu_r1.py', 'tests/check_cara_read_write_linux_routes_r1.py',
    'scripts/check_cara_read_write_linux_cpu_r1.py',
    'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json',
)
REMOTE = REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py',
                        'check_cara_read_write_linux_cpu_r1.py')

if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
