"""Whole24 source/contract controls; synthetic profile intervals, no real quote."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import torch

from wcomr import drop1_window24_production_r1 as production
from wcomr.drop1_window24_entry_adapter_r1 import adapt

ROOT = Path(__file__).resolve().parents[1]


def contract():
    old = json.loads((ROOT / production.FIXED_REFERENCES['original_config']).read_text())
    c = dict(old, card=production.CARD, run_id=production.RUN, namespace='DROP1_WINDOW24',
        methods=list(production.METHODS), scope_counts=production.COUNTS,
        CPU_scope=production.CPU_COUNTS, plans={k: list(v) for k, v in production.plans().items()},
        budget_origin_used_GPUh=79.99637737158223, continued_A_actual_updates=[21, 22, 23],
        forecast_complete_GPUh=2., billed_limit_GPUh=2.5)
    refs = {k: dict(ref=v, sha256='a'*64) for k, v in production.FIXED_REFERENCES.items()}
    refs.update({k: dict(ref='tests/synthetic-'+k+'.json', sha256='b'*64)
                 for k in ('N09_capture', 'N09_acceptance', 'cost')})
    c['references'] = refs
    return c


def price_fixture():
    old = json.loads(gzip.decompress((ROOT / production.FIXED_REFERENCES['old_capture']).read_bytes()))
    scope = json.loads((ROOT / 'manifests/wc_paper_N09_runtime_profile40_scope_r1_20261016.json').read_text())
    rows, scalars = [], {}
    for planned in scope['complete_matrix']:
        row = copy.deepcopy(planned)
        row['component_profile_audit'] = 'PASS'
        if row['method'] == 'A_NO_P' and row['component_profile']:
            path = '/SYNTHETIC_UNIT_ONLY/' + row['id']
            row['component_profile_artifact'] = dict(path=path, sha256='c'*64)
            spans = [dict(id=i, component=k, outcome='RETURNED', CPU_seconds=.01*(i+1), CUDA_elapsed_ms=20.*(i+1))
                     for i, k in enumerate(('output_head', 'correction_warp', 'correction_to_velocity'))]
            scalars[path] = dict(sha256='c'*64, matches_original_row_identity=True,
                                 data=dict(intervals=spans))
        rows.append(row)
    return old, dict(final=dict(rows=rows), profile_scalar_originals=scalars), dict(
        full_runtime_profile_scope_accepted=True, action_unit_prices_measured=False)


class Whole24ProductionPreparation(unittest.TestCase):
    def test_complete_scope_contract_and_all_mutations(self):
        c = contract(); production.validate_contract(c)
        mutations = dict(scope_counts={**production.COUNTS, 'formal_paths':15},
            methods=c['methods'][:-1], A_method='W1_ONE_PHASE', P_enabled=True,
            online_teachers=True, training=True, autonomy_exclusive_upper_GPUh=8,
            cumulative_cap_GPUh=113, billed_limit_GPUh=0., continued_A_actual_updates=[21],
            plans={**c['plans'], 'S25-A3': c['plans']['S25-A1']})
        for key, value in mutations.items():
            bad = copy.deepcopy(c); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): production.validate_contract(bad)

    def test_unpriced_scope_does_not_become_a_production_config(self):
        c = contract(); c['forecast_complete_GPUh'] = None; c['billed_limit_GPUh'] = None
        with self.assertRaises(ValueError): production.validate_contract(c)

    def test_complete_quote_accounts_all24_and_twelve_additional_A(self):
        old, n09, accepted = price_fixture(); before = copy.deepcopy(n09)
        q = production.estimate_whole24(old, n09, accepted, [r['name'] for r in contract()['requests']])
        self.assertEqual(n09, before)
        self.assertEqual((len(q['positions']), q['full_warmups'], q['formal_paths'], q['loads']), (24, 8, 16, 1))
        self.assertEqual(sum(p['additional_A_readouts'] for p in q['positions']), 12)
        self.assertEqual(len(q['N09_source_rows']), 4)
        self.assertEqual(q['per_extra_A_planning_proxy_seconds'], 1.24)
        self.assertGreater(q['billed_limit_GPUh'], q['forecast_complete_GPUh'])
        self.assertFalse(q['whole_card_selected']); self.assertFalse(q['action_unit_prices_measured'])
        self.assertFalse(q['inclusive_components_are_additive_total_latency'])

    def test_unknown_or_nonfinite_readout_price_is_not_zero(self):
        for case in ('no_N09', 'missing_component', 'missing_mode', 'nonfinite', 'rejection_source'):
            old, n09, accepted = price_fixture()
            if case == 'no_N09': accepted['full_runtime_profile_scope_accepted'] = False
            elif case == 'missing_component':
                for value in n09['profile_scalar_originals'].values(): value['data']['intervals'].pop()
            elif case == 'missing_mode':
                next(r for r in n09['final']['rows'] if r.get('component_profile_artifact'))['component_profile_audit'] = 'FAILED'
            elif case == 'nonfinite': next(iter(n09['profile_scalar_originals'].values()))['data']['intervals'][0]['CPU_seconds'] = float('nan')
            else: old['runner']['runs'][0]['status'] = 'TEXT_REJECTED'
            with self.subTest(case=case), self.assertRaises(ValueError):
                production.estimate_whole24(old, n09, accepted, [r['name'] for r in contract()['requests']])

    def test_full_quote_crossing12_retains_full_card(self):
        old, n09, accepted = price_fixture(); old['runner']['load_seconds'] += 12*3600
        old['billing']['wall_seconds'] += 12*3600; old['billing']['actual_GPUh'] = old['billing']['wall_seconds']/3600
        q = production.estimate_whole24(old, n09, accepted, [r['name'] for r in contract()['requests']])
        self.assertTrue(q['specific_whole_card_confirmation_required']); self.assertEqual(len(q['positions']), 24)

    def test_original_execution_and_CPU_guards_recover_exactly(self):
        for kind, path in [('runner', 'scripts/run_wc_drop1_full18_r1.py'), ('post', 'scripts/postprocess_wc_drop1_full18_r1.py')]:
            source = (ROOT / path).read_text(); changed = adapt(source, kind)
            self.assertIn('wcomr.drop1_window24_production_r1', changed)
            self.assertIn('score_pair' if kind == 'post' else 'torch.cuda._lazy_init=forbidden', changed)
            with self.assertRaises(ValueError): adapt(source+'\n', kind)
        post = adapt((ROOT / 'scripts/postprocess_wc_drop1_full18_r1.py').read_text(), 'post')
        self.assertIn('len(scored)==16', post); self.assertIn('len(baseline_controls)==12', post)
        self.assertIn('len(prefix_controls)==2', post)

    def test_A1_A3_prefix_checks_first21_and_preserves_missing(self):
        data = {f'warm_{r}_{m}': [torch.full((2,3), float(i)) for i in range(36)]
                for r in (1,2) for m in ('S25-A1','S25-A3')}
        data['warm_1_S25-A3'][21] += 1
        controls = production.common_prefix_controls(data)
        self.assertTrue(all(r['status'].startswith('PASS') for r in controls))
        data['warm_2_S25-A3'][20] += 1
        with self.assertRaises(ValueError): production.common_prefix_controls(data)
        data.pop('warm_2_S25-A3')
        self.assertEqual(production.common_prefix_controls(data)[1]['status'], 'MISSING_FULL36_RETAINED')

    def test_all12_old_endpoint_controls_and_changed_history(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder); asset = stage/'old.bin'; asset.write_bytes(b'SYNTHETIC_UNIT_ONLY')
            artifact = dict(path=str(asset), sha256=production.sha(asset), bytes=asset.stat().st_size)
            bindings, rows = [], []
            for scene in ('s0','s1','s2','s3'):
                for method in ('S26-C','S25-C','S25-A1'):
                    row = dict(scene=scene,method=method,section='TIMED',endpoint_audit='PASS',
                        final_latent_sha256='d'*64,actions=['DD']*36,A_history=list(range(36)),
                        decoded_video=dict(RGB_sha256='e'*64),final_artifact=artifact,video_artifact=artifact)
                    rows.append(copy.deepcopy(row));bindings.append(dict(scene=scene,window_method=method,original_row=row))
            path=stage/'controls.json';path.write_text(json.dumps(dict(rows=bindings)))
            c=dict(references=dict(old_controls=dict(ref='controls.json',sha256=production.sha(path))))
            self.assertTrue(all(x['status'].startswith('PASS') for x in production.old_endpoint_controls(rows,c,stage)))
            rows[-1]['A_history'][20] = -1
            with self.assertRaises(ValueError): production.old_endpoint_controls(rows,c,stage)
            rows.pop()
            got=production.old_endpoint_controls(rows,c,stage)
            self.assertEqual(len(got),12);self.assertEqual(sum(x['status']=='MISSING_OR_REJECTED_RETAINED' for x in got),1)


if __name__ == '__main__':
    unittest.main()
