"""New bounded CPU stage after retained R3 outer-fixture cleanup failure."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_s_endpoint_runner_cpu_r1 import OVERLAY,REMOTE
STAGE='cara-S-endpoint-runner-CPU-a6000-r4-20261031'
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60)
