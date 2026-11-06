import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.policy_asset_price_review_r1 import analyze_prices, exclusive_gate
from wcomr.policy_interval_assets_r1 import cells, matrix, rounds_for
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_wc_policy_asset_prices_r1 import review, IMAGE
from wcomr.policy_interval_assets_r1 import sha


def fixture():
    rows = [{**p, 'status': 'COMPLETE'} for p in matrix()]
    for row in rows:
        if row['section'] == 'FORMAL' and row['mode'] == 'COLLECT':
            row['interval_cells'] = [dict(source=s, target=t, price_trials=[
                dict(round=r, action=a, seconds=1000. if r == 'WARMUP' else
                     dict(C=1., A_HALF=2., A_ONE=3.)[a],
                     shared_prefix_included=False, restore_copy_hash_write_included=False)
                for r, order in rounds_for(s, t) for a in order]) for s, t in cells()]
    return rows


class PriceReview(unittest.TestCase):
    def test_repeats_are_not_invented_and_warmup_is_excluded(self):
        r = analyze_prices(fixture())
        self.assertEqual((r['formal_cells'], r['triply_measured_cells'], r['singly_measured_cells']),
                         (1624, 112, 1512))
        self.assertEqual(r['same_cell_action_ratios']['A_ONE_over_C']['median'], 3.)
        self.assertEqual(r['repeated_action_summary']['C']['sample_CV']['maximum'], 0.)
        self.assertFalse(r['clean_action_prices_accepted'])  # Stable contention is still contamination.
        self.assertFalse(r['PG_P1_dispatch_ready'])

    def test_full_denominator_and_registered_trial_order_are_required(self):
        rows = fixture()
        with self.assertRaises(ValueError): analyze_prices(rows[:-1])
        rows[-1]['interval_cells'].pop()
        with self.assertRaises(ValueError): analyze_prices(rows)
        rows = fixture()
        rows[-1]['interval_cells'][0]['price_trials'].reverse()
        with self.assertRaises(ValueError): analyze_prices(rows)

    def test_reject_bad_or_partial_prices(self):
        for value in (0., float('inf'), float('nan'), -1.):
            rows = fixture(); rows[-1]['interval_cells'][0]['price_trials'][0]['seconds'] = value
            with self.assertRaises(ValueError): analyze_prices(rows)
        rows = fixture(); rows[-1]['status'] = 'RUNNING'
        with self.assertRaises(ValueError): analyze_prices(rows)

    def test_round_drift_is_visible(self):
        rows = fixture()
        for row in rows:
            for point in row.get('interval_cells', []):
                for trial in point['price_trials']:
                    if trial['round'] == 'FORMAL_3': trial['seconds'] *= 2
        r = analyze_prices(rows)
        self.assertEqual(r['repeated_action_summary']['A_ONE']['round3_over_round1']['median'], 2.)


class ExclusiveGate(unittest.TestCase):
    def setUp(self):
        self.s = dict(gpu_uuid='GPU-example', compute_mode='Exclusive_Process',
                      compute_apps=[], mps_processes=[], observed_unix=100.)
        self.runner = dict(pid=12, start_ticks=345, uid=1000)

    def check(self, s=None, phase='idle', now=101.):
        return exclusive_gate(self.s if s is None else s, gpu_uuid='GPU-example',
                              phase=phase, runner=self.runner, now=now)

    def test_default_busy_stale_and_mps_fail_closed(self):
        self.assertTrue(self.check()['observation_passed'])
        for key, val in [('compute_mode', 'Default'), ('compute_apps', [self.runner]),
                         ('mps_processes', [99]), ('mps_processes', None), ('gpu_uuid', 'GPU-other')]:
            s = copy.deepcopy(self.s); s[key] = val
            self.assertFalse(self.check(s)['observation_passed'])
        self.assertFalse(self.check(now=111.)['observation_passed'])
        self.assertFalse(self.check(now=99.)['observation_passed'])

    def test_active_requires_exact_sole_context_and_start_identity(self):
        self.assertFalse(self.check(phase='active')['observation_passed'])
        self.s['compute_apps'] = [self.runner.copy()]
        self.assertTrue(self.check(phase='active')['observation_passed'])
        self.s['compute_apps'][0]['start_ticks'] += 1
        self.assertFalse(self.check(phase='active')['observation_passed'])
        self.s['compute_apps'] = [self.runner.copy(), dict(pid=44)]
        self.assertFalse(self.check(phase='active')['observation_passed'])


class PriceReviewBinding(unittest.TestCase):
    def test_sidecar_requires_original_capture_hash_and_same_launch_contention(self):
        with tempfile.TemporaryDirectory() as d:
            paths = [Path(d) / name for name in ('capture.json', 'accepted.json', 'launch.json', 'contention.json')]
            cap_path, acc_path, launch_path, con_path = paths
            launch = dict(launch_id='original', gpu_uuid='GPU-example', started_unix=10., registration_sha256='reg')
            original = dict(full_protocol_accepted=True, generator_input_ready=True)
            cap = dict(launch=launch, observed_unix=30., runner=dict(runs=fixture()),
                container_binding=dict(image=IMAGE, readonly_root=True, pid_mode='host', registration_sha256='reg',
                                       state=dict(Running=False, ExitCode=0)))
            contention = dict(launch_id='original', gpu_uuid='GPU-example', observed_unix=20.,
                own_UUID_apps=[dict(gpu_uuid='GPU-example', is_registered_runner=False)])
            for path, value in ((cap_path, cap), (launch_path, launch), (con_path, contention)):
                path.write_text(json.dumps(value))
            accepted = dict(original, capture_sha256=sha(cap_path), container_binding_accepted=True)
            acc_path.write_text(json.dumps(accepted))
            # The original acceptor is mocked only in this unit fixture; the CLI recomputes it.
            with patch('audit_wc_policy_asset_prices_r1.accept_terminal', return_value=original):
                result = review(*paths)
                self.assertTrue(result['original_artifacts_accepted'])
                self.assertFalse(result['clean_action_prices_accepted'])
                con_path.write_text(json.dumps(dict(contention, launch_id='different')))
                with self.assertRaises(ValueError): review(*paths)
                con_path.write_text(json.dumps(contention))
                acc_path.write_text(json.dumps(dict(accepted, capture_sha256='changed')))
                with self.assertRaises(ValueError): review(*paths)


if __name__ == '__main__': unittest.main()
