#!/usr/bin/env python3
"""Original complete-card launch with the separately validated R2 stage."""
import launch_wc_paper_N05_core66_r1 as original

if __name__=='__main__':
    original.STAGE='.sync/wc-paper-n05-core66-production-cpu-r2-20261016'
    original.main()
