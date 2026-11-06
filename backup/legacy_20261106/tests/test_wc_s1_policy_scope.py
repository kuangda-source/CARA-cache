import importlib.util
import json
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('s1_real', ROOT / 'scripts/run_wc_s1_real_qkv.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_crossed_factorial_axes_and_cost_scope_are_locked():
    for name in ['wc_s1_real_qkv.json', 'wc_s1_crossed_qkv.json']:
        c = json.loads((ROOT / 'configs' / name).read_text())
        m.validate_scope(c)
        for key, value in [('max_gpu_wall_seconds', 240), ('repeats', 10), ('pv_skipping', True), ('policy_set', 'unknown'), ('arms', ['dense'])]:
            with TestCase().assertRaises(ValueError):
                m.validate_scope(dict(c, **{key: value}))
        altered = json.loads(json.dumps(c)); altered['policies'][0]['cdf'] = .5
        with TestCase().assertRaises(ValueError):
            m.validate_scope(altered)
