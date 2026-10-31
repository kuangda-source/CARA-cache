"""One bounded GPU-hidden real-video validation on two-card."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE

STAGE='cara-S-endpoint-artifact-CPU-a6000-r1-20261031'
OVERLAY=(
    'src/wcomr/cara_s_endpoint_lifecycle_r1.py','src/wcomr/cara_s_endpoint_release_r1.py',
    'src/wcomr/cara_s_uniform_endpoint_plan_r1.py','src/wcomr/cara_s_uniform_endpoint_binding_r1.py',
    'src/wcomr/cara_s_uniform_endpoint_execution_r1.py','src/wcomr/cara_s_endpoint_artifacts_r1.py',
    'src/wcomr/cara_s_endpoint_scoring_manifest_r1.py',
    'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json',
    'reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json',
    'tests/test_cara_s_endpoint_release_r1.py','tests/check_cara_s_endpoint_artifact_fixture_r1.py',
    'tests/test_cara_s_endpoint_artifacts_r1.py','tests/check_cara_s_endpoint_real_video_r1.py',
    'scripts/check_cara_s_endpoint_artifact_cpu_r1.py',
)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_artifact_cpu_r1.py')

if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=900,exit_seconds=60)
