"""One GPU-hidden CPU validation and original completed asset readback."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_gpu_dispatch_cpu_r1 import OVERLAY as DISPATCH
STAGE='cara-S-endpoint-reuse-admission-CPU-a6000-r1-20261031'
OVERLAY=DISPATCH+('src/wcomr/cara_s_endpoint_reuse_admission_r1.py',
    'tests/test_cara_s_endpoint_reuse_admission_r1.py','scripts/check_cara_s_endpoint_reuse_cpu_r1.py')
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_reuse_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=180,exit_seconds=30)
