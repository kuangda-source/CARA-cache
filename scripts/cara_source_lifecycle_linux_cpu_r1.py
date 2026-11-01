"""One isolated V1 source/DP/point20 CPU stage; recover originals after intent."""
from cara_s_initialization_selector_cpu_r1 import main, REMOTE
from cara_read_write_linux_cpu_r1 import OVERLAY as READ_WRITE


STAGE = 'cara-source-lifecycle-V1-CPU-a6000-r1-20261101'
OVERLAY = tuple(dict.fromkeys(READ_WRITE+(
    'src/wcomr/cara_read_write_provenance_r1.py', 'src/wcomr/cara_read_write_transition_r1.py',
    'src/wcomr/cara_read_write_adjoint_r1.py', 'src/wcomr/cara_read_write_step_r1.py',
    'src/wcomr/cara_source_lifecycle_planner_r1.py', 'src/wcomr/cara_source_lifecycle_weights_r1.py',
    'src/wcomr/cara_source_lifecycle_design_r1.py', 'src/wcomr/cara_source_lifecycle_trace_r1.py',
    'tests/test_cara_read_write_transition_r1.py', 'tests/test_cara_read_write_provenance_r1.py',
    'tests/test_cara_source_lifecycle_planner_r1.py', 'tests/test_cara_source_lifecycle_design_r1.py',
    'scripts/audit_cara_source_lifecycle_coverage_r1.py', 'scripts/check_cara_source_lifecycle_linux_cpu_r1.py',
    'reports/cara_v1_S108_original_metadata_read_r1_20261101.json',
    'reports/cara_sq_s_A6000_complete_frozen_risk_result_r1_20261030.json',
    'reports/cara_read_write_final_collection_original_r1_20261101.json',
)))
REMOTE = REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py',
                        'check_cara_source_lifecycle_linux_cpu_r1.py')


if __name__ == '__main__':
    main(stage=STAGE, overlay=OVERLAY, remote_code=REMOTE, work_seconds=600, exit_seconds=60)
