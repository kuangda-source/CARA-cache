"""One bounded endpoint scoring CPU stage; original GPU work is never read."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_artifact_cpu_r1 import OVERLAY as ARTIFACT_OVERLAY

STAGE='cara-S-endpoint-score-CPU-a6000-r1-20261031'
OVERLAY=ARTIFACT_OVERLAY+(
    'src/wcomr/cara_s_endpoint_scores_r1.py','scripts/score_cara_s_endpoint_fidelity_r1.py',
    'tests/check_cara_s_endpoint_artifact_fixture_r2.py','tests/test_cara_s_endpoint_scores_r1.py',
    'tests/check_cara_s_endpoint_scoring_cli_r1.py','scripts/check_cara_s_endpoint_score_cpu_r1.py',
)
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_score_cpu_r1.py')

if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=900,exit_seconds=60)
