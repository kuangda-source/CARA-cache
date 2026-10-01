"""Frozen S0 scope from existing balance; fail closed on any in-flight job."""
import importlib.util
from pathlib import Path
from unittest import TestCase

spec = importlib.util.spec_from_file_location('s0_supervisor', Path(__file__).resolve().parents[1] / 'scripts/supervise_wc_s0_profile.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_balance_and_scope_refuse_expansion_or_any_inflight():
    base = {'cap_gpu_hours': 4, 'used_gpu_hours': 3.6545041399802236}
    module.scope_gate(base, 750)
    for changes, seconds in [({'used_gpu_hours': 3.99}, 750), ({'cap_gpu_hours': 8}, 750),
                             ({}, 900), ({'wc_s1_inflight': {}}, 750), ({'wc_s0_inflight': {}}, 750)]:
        with TestCase().assertRaises(ValueError):
            module.scope_gate(dict(base, **changes), seconds)
