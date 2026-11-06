"""Read the new original CPU only; preserve the missing-import R1 terminal."""
from accept_cara_source_lifecycle_p1_guardian_cpu_r1 import main
from cara_source_lifecycle_p1_guardian_cpu_r2 import STAGE,OVERLAY


if __name__=='__main__':main(expected_stage=STAGE,overlay=OVERLAY)
