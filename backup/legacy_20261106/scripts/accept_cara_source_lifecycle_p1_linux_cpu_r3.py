"""Original full dual-flow CPU after the caller-forward fix; no replay."""
from accept_cara_source_lifecycle_p1_linux_cpu_r2 import main
from cara_source_lifecycle_p1_linux_cpu_r3 import STAGE, OVERLAY


if __name__ == '__main__':
    main(expected_stage=STAGE, overlay=OVERLAY, work_seconds=3600)
