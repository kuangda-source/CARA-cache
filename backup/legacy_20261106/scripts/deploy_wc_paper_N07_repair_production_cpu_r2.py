#!/usr/bin/env python3
"""Git-bound fresh repair CPU stage; the original failed stage stays unchanged."""
from pathlib import Path
import sys

if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.frozen_repair_cpu_staging_r2 import execute_entry
    execute_entry(Path(__file__),'deploy')
