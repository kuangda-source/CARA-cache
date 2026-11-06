#!/usr/bin/env python3
"""New immutable source stage after the original fixture namespace failure."""
import launch_wc_shared_registry952_local_cpu_r2 as original

if __name__ == '__main__':
    original.STAGE = '.sync/wc-paper-shared-registry952-local-cpu-r3-20261016'
    original.GENERATION = 'R3'
    original.main()
