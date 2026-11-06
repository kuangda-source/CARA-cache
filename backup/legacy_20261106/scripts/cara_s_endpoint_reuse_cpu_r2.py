"""New bounded stage after original R1 absence; includes entry failure cleanup."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_s_endpoint_reuse_cpu_r1 import OVERLAY as REUSE,REMOTE
STAGE='cara-S-endpoint-reuse-admission-CPU-a6000-r2-20261031'
OVERLAY=REUSE+('tests/test_cara_s_endpoint_entry_r1.py',)
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=180,exit_seconds=30)
