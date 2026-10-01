"""Scope integrity tests; no imports of Torch or CUDA and no GPU job."""
import importlib.util
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('s1_real_supervisor', ROOT / 'scripts/supervise_wc_s1_crossed_qkv.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_current_balance_accepts_one_frozen_scope_without_expansion():
    module.scope_gate({'cap_gpu_hours': 4, 'used_gpu_hours': 3.8958064096647362}, 120)


def test_inflight_exhausted_or_expanded_scope_refused():
    for budget, seconds in [({'cap_gpu_hours': 4, 'used_gpu_hours': 3.99}, 120),
                            ({'cap_gpu_hours': 8, 'used_gpu_hours': 3.65}, 120),
                            ({'cap_gpu_hours': 4, 'used_gpu_hours': 3.65}, 300),
                            ({'cap_gpu_hours': 4, 'used_gpu_hours': 3.878, 'wc_s1_inflight': {'run_id': 'original'}}, 120),
                            ({'cap_gpu_hours': 4, 'used_gpu_hours': 3.878, 'wc_s0_inflight': {}}, 120),
                            ({'cap_gpu_hours': 4, 'used_gpu_hours': 3.878, 'wc_s1_crossed_inflight': {}}, 120)]:
        with TestCase().assertRaises(ValueError):
            module.scope_gate(budget, seconds)
