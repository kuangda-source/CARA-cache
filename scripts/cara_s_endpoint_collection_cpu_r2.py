"""One original bounded full endpoint collection CPU stage on two-card."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE

STAGE = 'cara-S-endpoint-collection-CPU-a6000-r2-20261031'
CONTRACT = 'plans/cara_next_stage_20261028/mainline/r2/S_ENDPOINT_COLLECTION_CPU_R2_20261031.json'
OVERLAY = (
    'src/wcomr/cara_s_uniform_endpoint_plan_r1.py',
    'src/wcomr/cara_s_uniform_endpoint_binding_r1.py',
    'src/wcomr/cara_s_uniform_endpoint_execution_r1.py',
    'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json',
    'reports/cara_s_uniform_endpoint_binding_CPU_r1_20261031.json',
    CONTRACT,
    'scripts/check_cara_s_endpoint_collection_cpu_r2.py',
    'tests/check_cara_s_endpoint_collection_routes_r2.py',
)
REMOTE = REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py',
                        'check_cara_s_endpoint_collection_cpu_r2.py')

if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=1200, exit_seconds=60)
