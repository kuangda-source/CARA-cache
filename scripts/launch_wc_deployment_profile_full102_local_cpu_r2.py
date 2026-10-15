#!/usr/bin/env python3
"""Fresh whole102 source after the static-bound-method observer repair."""
import importlib.util
from pathlib import Path

path = Path(__file__).with_name('launch_wc_deployment_profile_full102_local_cpu_r1.py')
spec = importlib.util.spec_from_file_location('full102_source_packaging', path)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.STAGE = '.sync/wc-paper-deployment-profile-full102-local-cpu-r2-20261016'
base.GENERATION = 'R2'

if __name__ == '__main__':
    base.main()
