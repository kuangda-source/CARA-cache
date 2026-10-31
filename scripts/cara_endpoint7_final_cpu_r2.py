"""Fixed isolated source closure after retained R1 import failure; no numeric/scorer replay."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_endpoint7_final_cpu_r1 import OVERLAY as ORIGINAL,REMOTE
STAGE='cara-endpoint7-final-CPU-a6000-r2-20261101'
OVERLAY=tuple(dict.fromkeys(ORIGINAL+(
 'src/wcomr/cara_s_endpoint_reuse_admission_r1.py',
 'src/wcomr/cara_fast_b36_analysis_r1.py',
)))
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=300,exit_seconds=60)
