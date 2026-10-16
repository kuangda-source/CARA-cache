#!/usr/bin/env python3
"""Separate full180 UUID lease/actual-wall supervisor; needs new exact authority."""
from pathlib import Path
import sys

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from wcomr.frozen_repair_entry_r2 import execute_entry
    execute_entry(Path(__file__), 'supervisor')
