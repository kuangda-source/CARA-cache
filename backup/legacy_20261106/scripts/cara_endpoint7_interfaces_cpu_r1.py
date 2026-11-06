"""One affected-interface CPU validation, without rerunning the accepted46 route test."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_runner_cpu_r1 import OVERLAY as RUNNER
from cara_s_endpoint_score_cpu_r1 import OVERLAY as SCORE
STAGE='cara-endpoint7-interfaces-CPU-a6000-r1-20261101'
OVERLAY=tuple(dict.fromkeys(RUNNER+SCORE+(
 'src/wcomr/cara_endpoint7_binding_r1.py','src/wcomr/cara_endpoint7_plan_r1.py',
 'src/wcomr/cara_s_endpoint_score_capture_r1.py','src/wcomr/cara_s_endpoint_score_dispatch_r1.py',
 'scripts/cara_s_endpoint_score_bootstrap_r1.py','scripts/check_cara_endpoint7_interfaces_cpu_r1.py',
 'tests/test_cara_endpoint7_interfaces_r1.py','tests/test_cara_s_endpoint_score_capture_r1.py',
 'tests/test_cara_s_endpoint_score_dispatch_r1.py',
 'configs/cara_endpoint_proposal.json','configs/cara_endpoint_frozen_binding.json',
 'configs/cara_endpoint_request_card.json','configs/cara_endpoint_container_profile.json',
 'configs/cara_endpoint_original_B36_scores.json',
)))
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_endpoint7_interfaces_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60)
