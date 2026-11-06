"""Current paper registration must retain the complete original acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from assemble_cara_fast_paper_results_r2 import accepted_results, write_index

MANIFEST = 'plans/cara_next_stage_20261028/mainline/PAPER_RESULTS_MANIFEST_R2.json'


class PaperResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT/MANIFEST).read_text())
        cls.result = accepted_results(ROOT/MANIFEST)
        batch = cls.manifest['accepted_batches'][0]
        cls.analysis = json.loads((ROOT/batch['analysis']['path']).read_text())

    def clone(self, folder):
        root = Path(folder)
        batch = self.manifest['accepted_batches'][0]
        sources = {MANIFEST, self.manifest['parent_manifest']['path']}
        sources.update(d['path'] for d in batch.values() if isinstance(d, dict))
        sources.update(d['path'] for d in self.analysis['input_file_sha256'].values())
        cpu = json.loads((ROOT/batch['figure_CPU_acceptance']['path']).read_text())
        sources.update(cpu['critical_source_sha256'])
        sources.update(self.result['exports'])
        for name in sources:
            target = root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, target)
        return root, copy.deepcopy(self.manifest)

    def save_manifest(self, root, manifest):
        path = root/MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest))
        return path

    def replace_analysis(self, root, manifest, mutate):
        descriptor = manifest['accepted_batches'][0]['analysis']
        path = root/descriptor['path']
        data = json.loads(path.read_text())
        mutate(data)
        path.write_text(json.dumps(data))
        descriptor['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_complete_data_scope_and_original_costs_preserved(self):
        r = self.result
        self.assertEqual(r['prompt_equal_summaries'], self.analysis['prompt_equal_summaries'])
        self.assertEqual(r['FIT_phase_A_only_sensitivity'], self.analysis['FIT_phase_A_only_sensitivity'])
        self.assertEqual(r['independent_input_clusters'], 4)
        self.assertEqual(len(r['exports']), 12)
        self.assertEqual(len(r['prompt_equal_summaries']['ALL']), 8)
        self.assertEqual(r['original_A32_plus_B36_GPUh'], 4.640259487808734)
        self.assertEqual(len(r['original_once_only_costs']), 2)
        self.assertEqual(r['frozen_baselines']['WC']['time_match'], 'UNMATCHED')
        self.assertEqual(r['frozen_baselines']['RA']['time_match'], 'UNMATCHED')
        native = r['prompt_equal_summaries']['ALL'][0]
        self.assertEqual(set(native['PSNR_per_member'].values()), {'+inf'})
        self.assertFalse(r['independent_new_inputs'])
        self.assertFalse(r['new_method_claim_accepted'])
        self.assertFalse(r['metrics_computed'])
        self.assertEqual(r['human_reviews_included'], 0)

    def test_index_uses_existing_exports_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'index'
            write_index(self.result, output)
            self.assertEqual({p.name for p in output.iterdir()}, {'FAST_RESULTS.md', 'accepted-results.json'})
            self.assertEqual(json.loads((output/'accepted-results.json').read_text()), self.result)
            body = (output/'FAST_RESULTS.md').read_text()
            self.assertIn('WC_T006 [FIT UNMATCHED]', body)
            self.assertIn('RA_T1 [FIT UNMATCHED]', body)
            self.assertIn('T_request', body)
            self.assertIn('CHECK 是旧 CAL 内部留出', body)
            self.assertIn('本索引新增 GPUh 为 0', body)
            for name in self.result['exports']:
                self.assertIn(Path(name).name, body)
            with self.assertRaisesRegex(ValueError, 'Fresh'):
                write_index(self.result, output)

    def test_existing_confidence_intervals_reused_without_bootstrap(self):
        with patch('random.Random', side_effect=AssertionError('No new bootstrap')):
            result = accepted_results(ROOT/MANIFEST)
        self.assertEqual(result['original_T_DD_speedup_CI95']['ALL']['NATIVE35'], [1., 1.])
        self.assertEqual(result['statistics']['bootstrap_samples'], 20000)
        self.assertEqual(set(result['original_T_DD_speedup_CI95']), {'ALL', 'FIT', 'CHECK'})

    def test_planned_empty_duplicate_and_wrong_registry_refused(self):
        for kind in ('planned', 'empty', 'duplicate', 'schema'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                m = copy.deepcopy(self.manifest)
                if kind == 'planned': m['state'] = 'NO_NEW_ACCEPTED_RESULTS'
                elif kind == 'empty': m['accepted_batches'] = []
                elif kind == 'duplicate': m['accepted_batches'] *= 2
                else: m['schema'] = 'CARA_FAST_PAPER_RESULTS_R1'
                path = self.save_manifest(Path(folder), m)
                with self.assertRaisesRegex(ValueError, 'One complete'):
                    accepted_results(path)

    def test_altered_aggregate_refused_even_with_updated_outer_sha(self):
        with tempfile.TemporaryDirectory() as folder:
            root, m = self.clone(folder)
            self.replace_analysis(root, m, lambda a: a['prompt_equal_summaries']['ALL'][2]['metrics'].update(Alex=0.01))
            with self.assertRaisesRegex(ValueError, 'Analysis differs'):
                accepted_results(self.save_manifest(root, m), root)

    def test_fixture_and_partial_result_refused(self):
        for kind in ('fixture', 'partial'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                root, m = self.clone(folder)
                def mutate(a):
                    if kind == 'fixture': a.update(status='CPU_METADATA_FIXTURE_ONLY', CPU_fixture_only=True)
                    else: a['per_member'].pop()
                self.replace_analysis(root, m, mutate)
                with self.assertRaises(ValueError):
                    accepted_results(self.save_manifest(root, m), root)

    def test_changed_original_export_and_figure_acceptance_refused(self):
        for kind in ('CSV', 'visual', 'source'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                root, m = self.clone(folder)
                if kind == 'CSV':
                    name = next(n for n in self.result['exports'] if n.endswith('prompt_equal.csv'))
                    (root/name).write_bytes(b'changed')
                elif kind == 'visual':
                    d = m['accepted_batches'][0]['visual_acceptance']
                    p = root/d['path']; a = json.loads(p.read_text()); a['report_sha256'] = '0'*64
                    p.write_text(json.dumps(a)); d['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
                else:
                    (root/'scripts/analyze_cara_fast_r1.py').write_text('changed')
                with self.assertRaises(ValueError):
                    accepted_results(self.save_manifest(root, m), root)

    def test_unfinished_or_failed_original_figure_CPU_refused(self):
        for kind in ('running', 'failed'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                root, m = self.clone(folder)
                d = m['accepted_batches'][0]['figure_production_acceptance']
                path = root/d['path']; value = json.loads(path.read_text())
                state = value['accepted']['container_state']
                if kind == 'running': state.update(Status='running', Running=True, Pid=1234)
                else: state['ExitCode'] = 1
                path.write_text(json.dumps(value)); d['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaisesRegex(ValueError, 'must have exited'):
                    accepted_results(self.save_manifest(root, m), root)


if __name__ == '__main__':
    unittest.main()
