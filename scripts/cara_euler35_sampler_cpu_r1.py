"""One bounded two-card CPU compatibility run; existing handle recovery only."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
STAGE='cara-euler35-sampler-CPU-a6000-r1-20261101'
OVERLAY=(
 'src/wcomr/cara_euler_protocol_r1.py','src/wcomr/cara_euler_sampler_r1.py',
 'tests/check_cara_euler_sampler_r1.py','tests/test_cara_euler_sampler_r1.py',
 'scripts/check_cara_euler35_sampler_cpu_r1.py',
 'plans/cara_next_stage_20261101/euler/sigma_grid_and_call_contract.json',
)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_euler35_sampler_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=300,exit_seconds=60)
