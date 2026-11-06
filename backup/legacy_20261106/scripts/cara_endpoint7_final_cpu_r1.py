"""Final affected dispatch/storage/analysis CPU composition; no numerical or metric replay."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_endpoint7_interfaces_cpu_r1 import OVERLAY as INTERFACES
from cara_s_endpoint_gpu_dispatch_cpu_r1 import OVERLAY as DISPATCH
STAGE='cara-endpoint7-final-CPU-a6000-r1-20261101'
OVERLAY=tuple(dict.fromkeys(INTERFACES+DISPATCH+(
 'src/wcomr/cara_endpoint7_analysis_r1.py','src/wcomr/cara_endpoint7_figures_r1.py',
 'scripts/analyze_cara_endpoint7_complete_r1.py','tests/test_cara_endpoint7_analysis_r1.py',
 'tests/test_cara_endpoint7_figures_r1.py','tests/test_cara_endpoint7_final_binding_r1.py',
 'scripts/check_cara_endpoint7_final_cpu_r1.py','configs/cara_endpoint_whole_quote.json',
)))
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_endpoint7_final_cpu_r1.py')
if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=300,exit_seconds=60)
