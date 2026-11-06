"""Accept the new original R3 only; R1/R2 failed terminals remain unchanged."""
from accept_cara_source_lifecycle_p1_release_cpu_r2 import main
from cara_source_lifecycle_p1_release_cpu_r3 import STAGE,OVERLAY


if __name__=='__main__':main(expected_stage=STAGE,overlay=OVERLAY)
