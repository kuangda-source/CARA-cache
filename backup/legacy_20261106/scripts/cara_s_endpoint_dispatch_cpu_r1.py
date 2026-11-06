"""One GPU-hidden proof of endpoint CPU once-dispatch and recovery."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_capture_cpu_r2 import OVERLAY as CAPTURE_OVERLAY

STAGE='cara-S-endpoint-dispatch-CPU-a6000-r1-20261031'
OVERLAY=CAPTURE_OVERLAY+(
    'src/wcomr/cara_s_endpoint_score_dispatch_r1.py','scripts/cara_s_endpoint_score_bootstrap_r1.py',
    'tests/test_cara_s_endpoint_score_dispatch_r1.py','tests/check_cara_s_endpoint_score_dispatch_process_r1.py',
    'scripts/check_cara_s_endpoint_dispatch_cpu_r1.py',
)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_dispatch_cpu_r1.py')

if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=300,exit_seconds=30)
