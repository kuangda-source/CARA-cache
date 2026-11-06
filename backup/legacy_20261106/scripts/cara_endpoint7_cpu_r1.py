"""Unique bounded two-card CPU composition; capture-only after first intent."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE
STAGE='cara-endpoint7-CPU-a6000-r1-20261101'
CONTRACT='plans/cara_next_stage_20261101/e1/ENDPOINT7_CPU_CONTRACT_R1.json'
OVERLAY=(
 'src/wcomr/cara_endpoint7_plan_r1.py',
 'src/wcomr/cara_s_uniform_endpoint_plan_r1.py',
 'src/wcomr/cara_s_uniform_endpoint_binding_r1.py',
 'src/wcomr/cara_s_uniform_endpoint_execution_r1.py',
 'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json',
 'scripts/check_cara_endpoint7_cpu_r1.py',
 'tests/check_cara_endpoint7_routes_r1.py',CONTRACT)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_endpoint7_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60)
