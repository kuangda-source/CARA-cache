"""Exercise the complete scheduler with declared scalar fake inference results."""
import copy
import importlib.util
from pathlib import Path
import unittest

from wcomr.frozen_shared_execution_r1 import point
from wcomr.frozen_shared_production_r1 import (
    audit_row, full_rows, prepare_samples, run_registered_batch, validate_contract,
)
from wcomr.simple26d_r1 import plans


def fixture():
    path = Path(__file__).with_name('test_frozen_shared_production_r1.py')
    spec = importlib.util.spec_from_file_location('synthetic_contract_batch_only', path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    config, bound = module.fixture()
    class FakeArguments:
        def __init__(self, **kwargs): self.values = kwargs
        def model_dump(self, mode): return self.values
    return config, bound, prepare_samples(bound, FakeArguments)


def fake_result(planned, sample):
    p = point(planned['method']);n = p['actual_updates'];warm = planned['section'] == 'WARMUP'
    result = dict(method=planned['method'], status='COMPLETE', frozen_execution_point=p,
        solver_steps=n, guided_pairs=n, scheduler_timesteps=list(range(n)),
        in_timing_guided_copies=n if warm else 0, in_timing_hashes=0, research_checkpoints=0,
        audit=warm, write_deferred_after_main_timer=True, core_seconds=1.,
        frozen_request_cleanup=dict(components_alive_after=0),
        frozen_input_identity=dict(name=sample.values['name'], actual_sample_seed=sample.values['seed'],
            requested_steps=sample.values['num_steps'],
            installed_contexts=[['SYNTHETIC', 'SYNTHETIC', 'frozen-input-seed' + str(sample.values['seed'])]]),
        actions=None if p['family'] == 'NATIVE' else ['DD'] * 36)
    if warm: result['warm_guided_outputs'] = n
    if p['family'] == 'NATIVE':
        result.update(native_block_CFG_counts={'first_block_CFG': 2 * n, 'last_block_CFG': 2 * n},
                      native_count_adaptation=dict(inverse_bytes_and_AST_equal=True))
    elif p['family'] in ('WC', 'RA'):
        result['installed_thresholds'] = [dict(net_WC_threshold=p['threshold'], controller_RA_threshold=p['threshold'])]
    if p['family'] == 'FIXED26':
        semantic = list(plans()[planned['method']]);result['semantic_plan'] = semantic
        result['actions'] = ['DD' if a == 'D' else 'CC' for a in semantic]
    else:
        semantic = ['D'] * 36
    if planned['method'] == 'TABLE_PHASE_H1' or p['family'] == 'FIXED26':
        result['source_history'] = [dict(action=a, teacher_calls=0,
            P_updates_true_D_or_zero_risk_RA_anchor=False, true_D_before='SYNTHETIC_ANCHOR',
            true_D_after='SYNTHETIC_ANCHOR', A_readout=dict(readout_action=s))
            for a, s in zip(result['actions'], semantic)]
    return result


class SharedBatchControls(unittest.TestCase):
    def test_complete180_all_points_and_both_seeds_once(self):
        config, bound, samples = fixture();calls = [];snapshots = []
        def run(planned, sample):
            calls.append((planned['id'], sample.values['seed'], sample.values['num_steps']))
            return fake_result(planned, sample)
        state = run_registered_batch(config, bound, samples, run, save=lambda s: snapshots.append(copy.deepcopy(s)))
        self.assertEqual(len(calls), 180)
        self.assertEqual(len(state['runs']), 180)
        self.assertEqual({seed for _, seed, _ in calls}, {17, 43})
        self.assertEqual({steps for _, _, steps in calls}, {18, 26, 35})
        self.assertEqual(sum(r['section'] == 'WARMUP' for r in state['runs']), 20)
        self.assertTrue(state['status'].endswith('CPU_AUDIT_PENDING'))

    def test_text_rejection_retains_position_and_continues(self):
        config, bound, samples = fixture();plan = validate_contract(config, bound)
        target = plan[25]['id']
        def run(planned, sample):
            if planned['id'] == target: return dict(status='TEXT_REJECTED', solver_steps=0, guided_pairs=0)
            return fake_result(planned, sample)
        state = run_registered_batch(config, bound, samples, run)
        self.assertEqual(len(state['runs']), 180)
        self.assertEqual(state['runs'][25]['status'], 'TEXT_REJECTED')
        self.assertEqual(sum(r['status'] == 'TEXT_REJECTED' for r in state['runs']), 1)

    def test_failure_stops_original_prefix_and_preserves_all180_denominator(self):
        config, bound, samples = fixture();saved = [];count = 0
        def run(planned, sample):
            nonlocal count
            count += 1
            if count == 4: raise RuntimeError('SYNTHETIC_INFERENCE_FAILURE')
            return fake_result(planned, sample)
        with self.assertRaisesRegex(RuntimeError, 'SYNTHETIC_INFERENCE_FAILURE'):
            run_registered_batch(config, bound, samples, run, save=lambda s: saved.append(copy.deepcopy(s)))
        self.assertEqual(count, 4)
        rows = full_rows(saved[-1]['runs'], validate_contract(config, bound))
        self.assertEqual(len(rows), 180)
        self.assertEqual([r['status'] for r in rows[:4]], ['COMPLETE'] * 3 + ['TECH_FAILED'])
        self.assertEqual(sum(r['status'] == 'NOT_REACHED' for r in rows), 176)
        bad = copy.deepcopy(saved[-1]['runs']);bad[0]['case_id'] = 'FOREIGN'
        with self.assertRaises(ValueError): full_rows(bad, validate_contract(config, bound))

    def test_wrong_warm_counts_seed_native_and_fixed_actions_rejected(self):
        config, bound, samples = fixture();plan = validate_contract(config, bound)
        native = next(p for p in plan if p['method'] == 'NATIVE18')
        correct = fake_result(native, samples[(native['case_id'], native['method'])])
        for field, value in [('warm_guided_outputs', 36), ('guided_pairs', 36)]:
            row = {**native, **copy.deepcopy(correct)};row[field] = value
            with self.assertRaises(ValueError): audit_row(row, native, bound)
        row = {**native, **copy.deepcopy(correct)};row['frozen_input_identity']['actual_sample_seed'] = 0
        with self.assertRaises(ValueError): audit_row(row, native, bound)
        fixed = next(p for p in plan if p['method'] == 'FRONT_DENSE_A')
        row = {**fixed, **fake_result(fixed, samples[(fixed['case_id'], fixed['method'])])}
        row['source_history'][0]['A_readout']['readout_action'] = 'C'
        with self.assertRaises(ValueError): audit_row(row, fixed, bound)

    def test_native_metadata_matches_all72_original_accepted_numeric_receipts(self):
        import json
        path = Path(__file__).resolve().parents[1] / 'reports/wc_paper_shared_registry952_local_CPU_R3_result_20261016.json'
        actual = json.loads(path.read_text())
        config, bound, samples = fixture(); plan = validate_contract(config, bound); checked = 0
        for flow in actual['checks']:
            for prior in flow['audit_lean_checks']:
                if not prior['method'].startswith('NATIVE'): continue
                planned = next(p for p in plan if p['method'] == prior['method'])
                row = {**planned, **fake_result(planned, samples[(planned['case_id'], planned['method'])])}
                # Reuse original observed count fields only. Other final-case
                # fields remain an explicit synthetic fixture, not new inference.
                row['native_block_CFG_counts'] = copy.deepcopy(prior['native_block_CFG_counts'])
                audit_row(row, planned, bound); checked += 1
                row['native_block_CFG_counts']['last_block_CFG'] -= 1
                with self.assertRaises(ValueError): audit_row(row, planned, bound)
        self.assertEqual(checked, 72)


if __name__ == '__main__':
    unittest.main()
