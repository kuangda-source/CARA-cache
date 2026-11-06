"""Local contracts/delegation and old-data format controls, not numerical88."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wcomr import drop1_correction_window24_r1 as P

ROOT = Path(__file__).resolve().parents[1]


def old_rows_in_new_format():
    value = json.loads(gzip.decompress((ROOT / 'reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz').read_bytes()))
    rows = copy.deepcopy(value['final']['rows'])
    for row in rows:
        if row['method'] == 'S25-A':
            row['method'] = 'S25-A1'
            row['id'] = row['id'].replace('S25-A', 'S25-A1')
    return rows


class CorrectionWindowControls(unittest.TestCase):
    def setUp(self):
        self.c = json.loads((ROOT / 'manifests/wc_drop1_correction_window_full24_static_scope_20261018.json').read_text())
        self.old = json.loads((ROOT / P.original.CONFIG).read_text())
        self.scenes = [r['name'] for r in self.c['requests']]

    def test_CPU88_scope_adapter_reversibly_preserves_original_import_guards(self):
        path = ROOT / 'scripts/check_wc_drop1_correction_window88_cpu_r1.py'
        spec = importlib.util.spec_from_file_location('window_CPU_scope_template_control', path)
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        source = (ROOT / 'scripts/check_wc_drop1_full18_cpu_r1.py').read_text()
        changed = module.adapted_main_source(source)
        self.assertIn("value['actual_CPU_paths']==88", changed)
        self.assertIn("c['complete_CPU_paths']==44", changed)
        self.assertIn('torch.cuda._lazy_init = forbidden', changed)
        self.assertIn('torch.load=forbidden', changed)
        self.assertIn('original_helpers_and_current_device_restored', changed)
        with self.assertRaises(ValueError): module.adapted_main_source(source + '\n# CHANGED_SOURCE\n')

    def test_complete_frozen_registry_and_unchanged_original_plans(self):
        before = copy.deepcopy(P.original.plans())
        P.validate_static_manifest(self.c, self.old)
        p = P.plans()
        self.assertEqual([n for n, (a, b) in enumerate(zip(p['S25-A1'], p['S25-A3']), 1) if a != b], [22, 23])
        self.assertEqual(p['S25-A3'][20:24], ('A', 'A', 'A', 'D'))
        self.assertEqual(P.original.plans(), before)
        self.assertEqual([p[m].count('A') for m in P.METHODS], [0, 0, 1, 3])
        self.assertEqual([p[m].count('D') for m in P.METHODS], [26, 25, 25, 25])

    def test_partial_changed_input_or_fake_production_acceptance_refused(self):
        for change in ('quota', 'window', 'CPU_scope', 'input', 'paid_source', 'fake_CPU', 'fake_quote'):
            with self.subTest(change=change):
                c = copy.deepcopy(self.c)
                if change == 'quota': c['scope_counts']['formal_paths'] = 12
                elif change == 'window': c['plans']['S25-A3'][23] = 'A'
                elif change == 'CPU_scope': c['CPU_scope']['total_paths'] = 64
                elif change == 'input': c['requests'][0]['seed'] = 1
                elif change == 'paid_source': c['A_rule']['trusted_D_write'] = True
                elif change == 'fake_CPU': c['actual_CPU_accepted'] = True
                else: c['forecast_complete_GPUh'] = 1.
                with self.assertRaises(ValueError): P.validate_static_manifest(c, self.old)

    def test_old18_real_metadata_audit_compatible_with_three_old_arms(self):
        expected = {r['id']: r for r in P.matrix(self.scenes)}
        rows = old_rows_in_new_format()
        for row in rows: P.audit_row(row, expected[row['id']])
        self.assertEqual(len(rows), 18)

    def test_actual_old_scores_recomputed_and_unrun_new_arm_stays_missing(self):
        rows = P.full_rows(old_rows_in_new_format(), self.scenes)
        out = P.summaries(rows, self.scenes)
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(r['section'] == 'WARMUP' for r in rows), 8)
        methods = {r['method']: r for r in out['methods']}
        self.assertEqual(methods['S25-A3']['scored_scenes'], 0)
        self.assertIsNone(methods['S25-A3']['complete_four_scene_mean_LPIPS'])
        previous = json.loads((ROOT / 'reports/wc_drop1_complete_results_analysis_20261018.json').read_text())
        for method, old in P.OLD_METHODS.items():
            self.assertEqual(methods[method]['scored_scenes'], 4)
            self.assertEqual(methods[method]['complete_four_scene_mean_LPIPS'], previous['aggregates'][old]['mean_LPIPS'])
        self.assertTrue(all(r['scored_scenes'] == 0 for r in out['contrasts'][:3]))
        bad = copy.deepcopy(rows);bad[0]['scene'] = 'FOREIGN'
        with self.assertRaises(ValueError): P.full_rows(bad, self.scenes)
        with self.assertRaises(ValueError): P.full_rows([rows[0], rows[0]], self.scenes)

    def test_new_window_metadata_guard_catches_paid_readout_and_source_errors(self):
        # Synthetic new-arm trace schema only: no A3 physical prediction claimed.
        row = next(r for r in old_rows_in_new_format() if r['method'] == 'S25-A1' and r['section'] == 'TIMED')
        row['method'] = 'S25-A3';row['id'] = row['id'].replace('S25-A1', 'S25-A3')
        plan = P.plans()['S25-A3'];row['semantic_plan'] = list(plan);row['mask_sha256'] = P.mask_fingerprint(plan)
        for i in (21, 22):
            row['source_history'][i]['A_readout'].update(readout_action='A', shared_alpha=1)
        planned = next(r for r in P.matrix(self.scenes) if r['id'] == row['id'])
        P.audit_row(row, planned)
        for mode in ('alpha', 'teacher', 'trusted_D', 'deep', 'lean_copy', 'action'):
            with self.subTest(mode=mode):
                bad = copy.deepcopy(row)
                if mode == 'alpha': bad['source_history'][21]['A_readout']['shared_alpha'] = 2
                elif mode == 'teacher': bad['source_history'][21]['A_readout']['teacher_calls'] = 1
                elif mode == 'trusted_D': bad['source_history'][21]['true_D_after'] = {'FORGED': True}
                elif mode == 'deep': bad['source_history'][21]['A_readout']['extra_deep_blocks'] = 1
                elif mode == 'lean_copy': bad['in_timing_guided_copies'] = 36
                else: bad['actions'][21] = 'DD'
                with self.assertRaises(ValueError): P.audit_row(bad, planned)

    def test_raw_score_reference_pts_and_quota_corruption_not_hidden_by_summary(self):
        for mode in ('NaN', 'reference', 'PTS', 'counts'):
            with self.subTest(mode=mode):
                rows = P.full_rows(old_rows_in_new_format(), self.scenes)
                row = next(r for r in rows if r['section'] == 'TIMED' and r['method'] == 'S25-C')
                if mode == 'NaN': row['LPIPS']['frame_distances'][0] = float('nan')
                elif mode == 'reference': row['LPIPS']['reference_sha256'] = '0' * 64
                elif mode == 'PTS': row['LPIPS']['pts'][0][0] += 1
                else: row['counts']['A'] += 1
                with self.assertRaises(ValueError): P.summaries(rows, self.scenes)

    def test_adapter_restores_install_and_request_cleanup_success_error_and_leak(self):
        class Owner: pass
        for mode in ('success', 'error', 'leak'):
            with self.subTest(mode=mode):
                held = []
                def install(*a, **kw): return None, Owner()
                def execute(*a, **kw):
                    self.assertEqual(kw['replay_plan'][20:24], ('A', 'A', 'A', 'D'))
                    self.assertEqual(kw['table_parameters'], {'SYNTHETIC': True})
                    _, owner = P.original.clean.install()
                    if mode == 'leak': held.append(owner)
                    if mode == 'error': raise RuntimeError('SYNTHETIC_EXECUTION_ERROR')
                    return dict(method='FROZEN_MASK_CONTROL')
                with patch.object(P.original.base, 'collect_boundary', return_value={}) as cleanup, \
                        patch.object(P.original.clean, 'install', install), patch.object(P, 'execute_fixed', execute):
                    if mode == 'success':
                        r = P.execute(None, SimpleNamespace(seed=0), 'S25-A3', table_parameters={'SOURCE_PHASE': {'SYNTHETIC': True}}, previous_parameters={})
                        self.assertEqual(r['request_memory_lifecycle']['observed_owners'], 1)
                        self.assertEqual(r['request_memory_lifecycle']['owners_alive_after'], 0)
                    else:
                        with self.assertRaises((RuntimeError, ValueError)):
                            P.execute(None, SimpleNamespace(seed=0), 'S25-A3', table_parameters={'SOURCE_PHASE': {'SYNTHETIC': True}}, previous_parameters={})
                    self.assertIs(P.original.clean.install, install)
                    self.assertEqual(cleanup.call_count, 2)
                held.clear()


if __name__ == '__main__':
    unittest.main()
