"""Two-card CPU-only central transaction validation on temporary ledgers."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_endpoint7_final_cpu_r2 import OVERLAY as FINAL
STAGE='cara-endpoint7-central-CPU-a6000-r1-20261101'
OVERLAY=tuple(dict.fromkeys(FINAL+(
 'src/wcomr/cara_endpoint7_central_r1.py','tests/test_cara_endpoint7_central_r1.py',
 'scripts/check_cara_endpoint7_central_cpu_r1.py',
)))
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_endpoint7_central_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=180,exit_seconds=60)
