"""One bounded affected numerical CPU stage using the accepted source transport."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE

STAGE = 'cara-S-init-numeric-CPU-a6000-r2-20261031'
CONTRACT = 'plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_NUMERIC_CPU_R2_20261031.json'
OVERLAY = (
    'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json',
    'manifests/wc_math_n2_frozen_parameters_r1_20261012.json',
    'plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_SELECTOR_CPU_R1_20261031.json',
    CONTRACT,
    'scripts/check_cara_s_initialization_numeric_cpu_r2.py',
    'tests/check_cara_s_initialization_numeric_routes_r2.py',
)
REMOTE = REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py',
                        'check_cara_s_initialization_numeric_cpu_r2.py')


if __name__ == '__main__':
    main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60)
