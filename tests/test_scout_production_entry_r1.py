"""Scope and immutable model-entry controls; no model weights or synthetic scores."""
import ast
import copy
import json
from pathlib import Path
import unittest

from wcomr import scout_production_entry_r1 as e
from wcomr.scout_production_entry_adapter_r1 import adapt

ROOT=Path(__file__).resolve().parents[1]


class EntryScope(unittest.TestCase):
    def test_actual_selected_complete_config(self):
        c=json.loads((ROOT/e.CONFIG).read_text());e.validate_contract(c)
        rows=e.matrix([r['name'] for r in c['requests']])
        self.assertEqual(len(rows),e.COUNTS['total_paths'])
        self.assertEqual(sum(r['section']=='WARMUP' for r in rows),e.COUNTS['full_warmup_paths'])
        self.assertTrue(all(r['observer']==(r['round']==2 and r['method']!='NATIVE35') for r in rows if r['section']=='WARMUP'))

    def test_changed_full_scope_and_unpaid_diagnostics_refused(self):
        c=json.loads((ROOT/e.CONFIG).read_text())
        changes=dict(kind='OTHER',requests=c['requests'][:-1],methods=c['methods'][:-1],
            scope_counts={**c['scope_counts'],'total_paths':1},plans={},timing_claim='CLEAN_LATENCY',
            training=True,P_enabled=True,online_teachers=True,F_B_enabled=True,
            billed_limit_GPUh=12.,GPU_lifecycle_accepted=True)
        for k,v in changes.items():
            with self.subTest(k=k):
                changed=copy.deepcopy(c);changed[k]=v
                with self.assertRaises(ValueError):e.validate_contract(changed)

    def test_exact_real_runner_reversible(self):
        raw=(ROOT/'scripts/run_wc_drop1_full18_r1.py').read_text();new=adapt(raw)
        ast.parse(new)
        self.assertIn("observer=planned['observer']",new)
        self.assertIn('scout_vectors_artifact',new)
        self.assertIn('Ordinary guardrails required',new)
        with self.assertRaises(ValueError):adapt(raw+'\n# changed\n')

    def test_all_fixed_masks_have_guarded_age_support(self):
        for name,plan in e.plans().items():
            self.assertEqual(len(plan),36);self.assertEqual(plan[-1],'D')
            self.assertTrue(all(a=='D' for a in plan[:7]))
            anchor=0
            for n,a in enumerate(plan,1):
                if a=='D':anchor=n
                else:self.assertLessEqual(n-anchor,6)


if __name__=='__main__':unittest.main()
