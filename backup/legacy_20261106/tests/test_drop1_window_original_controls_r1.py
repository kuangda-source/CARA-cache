"""Guard the real twelve-endpoint cohort and its future four-arm use."""
import copy
import gzip
import json
from pathlib import Path
import unittest

from wcomr.drop1_window_original_controls_r1 import bind, fingerprint, verify

ROOT = Path(__file__).resolve().parents[1]


class OriginalTwelveControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bound = json.loads((ROOT / 'manifests/wc_drop1_window24_all12_original_controls_20261018.json').read_text())
        data = {}
        for k, info in cls.bound['evidence'].items():
            if k == 'original_acceptor':
                continue
            raw = (ROOT / info['ref']).read_bytes()
            data[k] = json.loads(gzip.decompress(raw) if info['ref'].endswith('.gz') else raw)
        cls.args = (data['original_capture'], data['original_acceptance'], data['original_config'],
                    data['new_static_scope'], data['original_native_bindings'], cls.bound['evidence'])

    def resigned(self, value):
        value.pop('fingerprint', None); value['fingerprint'] = fingerprint(value)
        return value

    def test_all_real_twelve_and_full24_are_bound(self):
        proof = verify(self.bound, *self.args)
        self.assertEqual(proof['original_controls'], 12)
        self.assertEqual({r['window_method'] for r in self.bound['rows']}, {'S26-C', 'S25-C', 'S25-A1'})
        self.assertFalse(proof['actual_production_CPU_accepted'])

    def test_refingerprinted_omission_cannot_shrink_controls(self):
        value = copy.deepcopy(self.bound); value['rows'].pop()
        with self.assertRaises(ValueError): verify(self.resigned(value), *self.args)

    def test_old_A1_control_cannot_be_relabelled_A3(self):
        value = copy.deepcopy(self.bound)
        next(r for r in value['rows'] if r['window_method'] == 'S25-A1')['window_method'] = 'S25-A3'
        with self.assertRaises(ValueError): verify(self.resigned(value), *self.args)

    def test_refingerprinted_video_swap_is_rejected(self):
        value = copy.deepcopy(self.bound); row = value['rows'][0]
        row['original_row']['video_artifact']['sha256'] = '0' * 64
        row['original_row_fingerprint'] = fingerprint(row['original_row'])
        with self.assertRaises(ValueError): verify(self.resigned(value), *self.args)

    def test_preparation_cannot_be_promoted_to_remote_or_production_acceptance(self):
        for key in ('fresh_remote_artifacts_reaudited', 'actual_production_CPU_accepted'):
            value = copy.deepcopy(self.bound); value[key] = True
            with self.assertRaises(ValueError): verify(self.resigned(value), *self.args)

    def test_missing_original_path_or_frame_is_not_filled(self):
        for mode in ('path', 'frame'):
            args = copy.deepcopy(self.args)
            if mode == 'path': args[0]['final']['rows'].pop()
            else: next(r for r in args[0]['final']['rows'] if r['section'] == 'TIMED')['LPIPS']['frame_distances'].pop()
            with self.assertRaises(ValueError): bind(*args)

    def test_static_A3_scope_cannot_be_shortened(self):
        args = copy.deepcopy(self.args); args[3]['plans']['S25-A3'][22] = 'C'
        with self.assertRaises(ValueError): bind(*args)

    def test_changed_native_reference_or_dense_history_is_rejected(self):
        for mode in ('reference', 'anchor'):
            args = copy.deepcopy(self.args)
            row = next(r for r in args[0]['final']['rows'] if r['section'] == 'TIMED' and r['method'] == 'S25-A')
            if mode == 'reference': row['LPIPS']['reference_sha256'] = '0' * 64
            else: row['source_history'][20]['true_D_after'] = 'FOREIGN_D_ANCHOR'
            with self.assertRaises(ValueError): bind(*args)


if __name__ == '__main__':
    unittest.main()
