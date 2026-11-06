"""Only accept the new original R3; retain both prior import failures."""
from accept_cara_source_lifecycle_p1_guardian_cpu_r1 import main
from cara_source_lifecycle_p1_guardian_cpu_r3 import STAGE,OVERLAY


if __name__=='__main__':main(expected_stage=STAGE,overlay=OVERLAY)
