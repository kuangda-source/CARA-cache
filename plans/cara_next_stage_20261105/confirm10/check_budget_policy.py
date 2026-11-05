"""Exercise the real central transaction on disposable local ledger copies."""
import contextlib
import copy
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.argv = [__file__, '--manifest', str(HERE / 'manifest.json')]
ops = runpy.run_path(str(ROOT / 'plans/cara_next_stage_20261104/sensitivity/ops.py'))
original = json.loads((ROOT / 'reports/cara_avslc_minitest_r1_20261105/central_settlement.json').read_text())['central_after']
auth = copy.deepcopy(original['jobs']['cara-avslc-minitest-r1-20261105'])
auth.update(run_id=ops['RUN'], launch_id='local-policy-fixture', billed_limit_GPUh=ops['LIMIT'],
    execution_authorized=True, direct_user_authorization=True, user_quote=ops['CONFIG']['authority']['user_quote'],
    cumulative_budget_policy='RUNNING_TOTAL_NO_CUMULATIVE_CAP', authorization_date='2026-11-05',
    reservation_event=ops['CONFIG']['reservation_event'])


def exercise(root, authority):
    source = ops['CENTRAL'].replace("root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')", f'root=pathlib.Path({str(root)!r})')
    packet = dict(arguments=dict(action='reserve', admission=dict(authorization=authority,
        registration_sha256='cpu-fixture', authorization_sha256='cpu-fixture',
        forecast_GPUh=ops['CONFIG']['quote']['forecast_GPUh'], observed_unix=time.time())))
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(source, '<local-central-test>', 'exec'), dict(packet=packet))
    return json.loads((root / 'reports/gpu-budget-v2.json').read_text())


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='cara-confirm10-budget-') as directory:
        root = Path(directory)
        (root / 'reports').mkdir()
        (root / 'reports/gpu-budget-v2.json').write_text(json.dumps(original))
        after = exercise(root, auth)
        assert after['used_gpu_hours'] == original['used_gpu_hours'] and after['cap_gpu_hours'] == original['cap_gpu_hours']
        assert after['available_gpu_hours'] < 0 and after['reserved_gpu_hours'] == 16.5 + ops['LIMIT']
        assert all(after['jobs'][k] == v for k, v in original['jobs'].items())
        assert exercise(root, auth) == after  # Same receipt, no second reservation/event.
    with tempfile.TemporaryDirectory(prefix='cara-confirm10-legacy-') as directory:
        root = Path(directory)
        (root / 'reports').mkdir()
        (root / 'reports/gpu-budget-v2.json').write_text(json.dumps(original))
        legacy = dict(auth)
        legacy.pop('cumulative_budget_policy')
        with unittest.TestCase().assertRaises(AssertionError):
            exercise(root, legacy)
    print('PASS: cumulative-only reserve, same-transaction recovery, legacy cap retained; no remote ledger touched')
