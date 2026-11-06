"""One bounded CPU proof of original score-container recovery, no GPU access."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_score_cpu_r1 import OVERLAY as SCORE_OVERLAY

STAGE='cara-S-endpoint-capture-CPU-a6000-r1-20261031'
OVERLAY=SCORE_OVERLAY+(
    'src/wcomr/cara_s_endpoint_score_capture_r1.py','tests/test_cara_s_endpoint_score_capture_r1.py',
    'tests/check_cara_s_endpoint_capture_process_r1.py','scripts/check_cara_s_endpoint_capture_cpu_r1.py',
)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_capture_cpu_r1.py')

if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=180,exit_seconds=30)
