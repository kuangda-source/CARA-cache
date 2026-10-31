"""One bounded endpoint guardian CPU allocation on the two-card host."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE

STAGE='cara-S-endpoint-guardian-CPU-a6000-r2-20261031'
OVERLAY=(
    'src/wcomr/cara_s_endpoint_lifecycle_r1.py',
    'src/wcomr/cara_s_endpoint_host_guardian_r1.py',
    'src/wcomr/cara_s_endpoint_guardian_journal_r1.py',
    'src/wcomr/cara_s_endpoint_supervisor_r1.py',
    'src/wcomr/cara_s_endpoint_lifecycle_capture_r1.py',
    'tests/test_cara_s_endpoint_guardian_binding_r1.py',
    'tests/test_cara_s_endpoint_host_guardian_r2.py',
    'tests/check_cara_s_endpoint_allocation_fixture_r1.py',
    'scripts/check_cara_s_endpoint_guardian_cpu_r2.py',
)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_guardian_cpu_r2.py')

if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=900,exit_seconds=60)
