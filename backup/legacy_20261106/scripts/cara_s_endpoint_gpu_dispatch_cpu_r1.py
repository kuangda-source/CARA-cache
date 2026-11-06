"""One bounded CPU-only validation of the prospective endpoint GPU dispatch."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_runner_cpu_r1 import OVERLAY as RUNNER
from cara_s_endpoint_guardian_cpu_r2 import OVERLAY as GUARDIAN
STAGE='cara-S-endpoint-GPU-dispatch-CPU-a6000-r1-20261031'
OVERLAY=tuple(dict.fromkeys(RUNNER+GUARDIAN+(
    'src/wcomr/cara_s_endpoint_gpu_dispatch_r1.py','scripts/cara_s_endpoint_gpu_dispatch_r1.py',
    'scripts/cara_s_endpoint_container_r1.py','scripts/cara_s_endpoint_host_entry_r1.py',
    'scripts/cara_s_endpoint_supervisor_worker_r1.py','tests/test_cara_s_endpoint_gpu_dispatch_r1.py',
    'tests/test_cara_s_endpoint_container_r1.py','tests/test_cara_s_endpoint_gpu_dispatch_child_r1.py',
    'tests/check_cara_s_endpoint_gpu_dispatch_child_fixture_r1.py','scripts/check_cara_s_endpoint_gpu_dispatch_cpu_r1.py',
)))
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_gpu_dispatch_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=180,exit_seconds=30)
