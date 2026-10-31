"""One bounded actual tiny collection-to-score CPU integration on two-card."""
from cara_s_initialization_selector_cpu_r1 import main,REMOTE
from cara_s_endpoint_dispatch_cpu_r1 import OVERLAY as DISPATCH
from cara_s_endpoint_collection_cpu_r2 import OVERLAY as COLLECTION

STAGE='cara-S-endpoint-pipeline-CPU-a6000-r1-20261031'
OVERLAY=tuple(dict.fromkeys(DISPATCH+COLLECTION+(
    'src/wcomr/cara_s_endpoint_pipeline_r1.py',
    'tests/check_cara_s_endpoint_pipeline_fixture_r1.py',
    'tests/check_cara_s_endpoint_pipeline_routes_r1.py',
    'tests/check_cara_s_endpoint_pipeline_process_r1.py',
    'scripts/check_cara_s_endpoint_pipeline_cpu_r1.py',
)))
REMOTE=REMOTE.replace('check_cara_s_initialization_selector_cpu_r1.py','check_cara_s_endpoint_pipeline_cpu_r1.py')

if __name__=='__main__':main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=1200,exit_seconds=60)
