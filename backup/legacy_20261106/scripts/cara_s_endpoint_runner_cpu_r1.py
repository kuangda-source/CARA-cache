"""One bounded two-card loaded endpoint runner CPU proof; no GPU dispatch."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_pipeline_cpu_r1 import OVERLAY as PIPELINE
STAGE='cara-S-endpoint-runner-CPU-a6000-r1-20261031'
OVERLAY=PIPELINE+(
    'src/wcomr/cara_s_endpoint_runner_binding_r1.py','src/wcomr/cara_s_endpoint_runner_r1.py',
    'scripts/run_cara_s_endpoint_r1.py','tests/test_cara_s_endpoint_runner_binding_r1.py',
    'tests/check_cara_s_endpoint_runner_routes_r1.py','scripts/check_cara_s_endpoint_runner_cpu_r1.py',
)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_runner_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60)
