"""Fresh bounded CPU package after the original R1 missing-module terminal."""
from cara_s_initialization_selector_cpu_r1 import main
from cara_source_lifecycle_linux_cpu_r1 import OVERLAY as ORIGINAL, REMOTE


STAGE='cara-source-lifecycle-V1-CPU-a6000-r2-20261101'
OVERLAY=ORIGINAL+('src/wcomr/sq_s_sources_r1.py',)


if __name__=='__main__':
    main(stage=STAGE,overlay=OVERLAY,remote_code=REMOTE,work_seconds=600,exit_seconds=60)
