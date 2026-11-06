"""Real full960 source metadata, no scores/models/GPU; preserve unknown rates."""
import copy
import json
from pathlib import Path
import unittest

from wcomr.automatic_quality_quote_r1 import quote,validate_selected,VERSION

ROOT=Path(__file__).resolve().parents[1]


class WholeQualityBudgetControls(unittest.TestCase):
    def scope(self):return json.loads((ROOT/'manifests/wc_paper_N10_unpriced_full960_production_scope_20261018.json').read_text())

    def test_every_original_dimension_and_full_model_cost_included(self):
        s=self.scope();before=copy.deepcopy(s);q=quote(s)
        self.assertEqual(s,before);self.assertEqual(len(q['positions']),6)
        self.assertEqual(sum(p['registered_positions'] for p in q['positions']),960)
        self.assertEqual(sum(p['ready_video_metric_invocations'] for p in q['positions']),645)
        self.assertEqual(q['full_model_contexts'],5);self.assertAlmostEqual(q['forecast_GPUh'],4.915)
        self.assertEqual(q['billed_limit_GPUh'],6.25)
        self.assertIsNone(q['measured_GPU_model_rates']);self.assertFalse(q['CPU_wall_used_as_GPU_rate'])

    def test_deleted_model_changed_scope_or_filled_in_rate_refused(self):
        for mode in ('model','scope','rate'):
            with self.subTest(mode=mode):
                s=self.scope()
                if mode=='model':s['dimension_workload'][1]['ready_video_invocations']=0
                elif mode=='scope':s['original_input_status_counts']['READY_TO_SCORE']=640
                else:s['actual_whole_card_quote_GPUh']=1.
                with self.assertRaises(ValueError):quote(s)

    def test_config_and_whole_budget_cannot_silently_diverge(self):
        s=self.scope();q=quote(s);c=copy.deepcopy(s['unpriced_config_template'])
        c.update(forecast_GPUh=q['forecast_GPUh'],billed_limit_GPUh=q['billed_limit_GPUh'],engineering_cost_policy=VERSION)
        self.assertEqual(len(validate_selected(c,s,q)),64)
        for mode in ('price','role','origin'):
            with self.subTest(mode=mode):
                config,cost=copy.deepcopy(c),copy.deepcopy(q)
                if mode=='price':config['billed_limit_GPUh']=1.
                elif mode=='role':cost['positions'].pop()
                else:config['budget_origin_used_GPUh']=0.
                with self.assertRaises(ValueError):validate_selected(config,s,cost)


if __name__=='__main__':unittest.main()
