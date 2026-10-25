import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from cara_cal66_a6000_profile_r1 import adapt, QUOTE, RUN


class ProfileTests(unittest.TestCase):
    def module(self, name):
        text, _ = adapt(name, (ROOT/name).read_text())
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        p = Path(d.name)/'adapted.py'; p.write_text(text)
        s = importlib.util.spec_from_file_location('sm86_budget_test', p)
        m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
        return m

    def test_liability_stays_reserved_but_is_not_device_ownership(self):
        m = self.module('src/wcomr/gpu_budget_pool_v2.py')
        pool = dict(schema=m.SCHEMA, cap_gpu_hours=226, origin_used_gpu_hours=156,
                    origin_gpu_jobs_launched=1, jobs={
                        'old': dict(status='RESERVED_OR_RUNNING', billed_limit_GPUh=12,
                                    gpu_uuid='GPU-same', confirmed_GPU_submission=False),
                        RUN: dict(status='RESERVED_OR_RUNNING', billed_limit_GPUh=8,
                                  gpu_uuid='GPU-same')})
        v = m.BudgetPool.accounting(pool)
        self.assertEqual(v['reserved_gpu_hours'], 20)
        self.assertEqual(v['available_gpu_hours'], 50)
        pool['jobs']['old']['confirmed_GPU_submission'] = True
        with self.assertRaises(ValueError): m.BudgetPool.accounting(pool)

    def test_missing_envelope_refuses_reservation(self):
        m = self.module('src/wcomr/gpu_budget_pool_v2.py')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                m.BudgetPool(d).reserve({'job_id': RUN}, {})

    def test_wrong_run_refuses_before_budget_write(self):
        m = self.module('src/wcomr/gpu_budget_pool_v2.py')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'reports'; p.mkdir()
            (p/'cal66-migration-envelope.json').write_text('{}')
            with self.assertRaises(ValueError):
                m.BudgetPool(d).reserve({'job_id': 'not-authorized'}, {})
            self.assertFalse((p/'gpu-budget-v2.json').exists())

    def test_whole_quote_preserves_scope(self):
        q = json.loads((ROOT/QUOTE).read_text())
        card = json.loads((ROOT/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json').read_text())
        self.assertEqual(q['scope'], card['scope'])
        generation = sum(q['arm_seconds'][r['role']] for r in card['matrix'])/3600
        self.assertAlmostEqual(generation, q['components']['all66_generation_GPUh'])
        self.assertAlmostEqual((generation+.85)*1.15, q['forecast_GPUh'])
        self.assertLessEqual(q['forecast_GPUh'], 8)
        self.assertEqual(q['deployment_absolute_seconds'], 257.7712338712067)

    def test_scope_and_alpha_manifest_remain_pinned(self):
        original = (ROOT/'src/wcomr/policy_generator_r1/shared66_card.py').read_text()
        generated, _ = adapt('src/wcomr/policy_generator_r1/shared66_card.py', original)
        for line in original.splitlines():
            if line.startswith(('FROZEN_SHA=', 'COUNTS=', 'MANIFEST=')):
                self.assertIn(line, generated)

    def test_wrong_source_cannot_be_silently_adapted(self):
        with self.assertRaises(ValueError):
            adapt('scripts/run_cara_shared66_r1.py', '# unexpected')

    def test_actual_cpu_dynamic_sampler_dependencies_and_fresh_output(self):
        sys.path.insert(0,str(ROOT/'src'))
        from wc_two_card_cara_cal66_cpu_r1 import cpu_source_names,PREPARE
        names=cpu_source_names()
        for name in ('check_cara_pg_production_sampling_cpu_r1','check_partial_mlp_guided_sampling_cpu_r1','check_rv0_video_actions_cpu','check_full_sampling'):
            self.assertIn('tests/'+name+'.py',names)
        self.assertIn("names.difference_update({'shared66-recovery-CPU.json','pg-independent-CPU-acceptance.json'})",PREPARE)


if __name__ == '__main__': unittest.main()
