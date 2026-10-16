"""N08 finite binding and execution glue; explicit fake inference responses."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from wcomr import balanced_repeat_execution_r1 as timing
from wcomr.balanced_repeat_timing_r1 import matrix, SCENES, SLOTS

ROOT = Path(__file__).resolve().parents[1]


class FakeArguments:
    def __init__(self, **values): self.values = values; self.__dict__.update(values)
    def model_dump(self, mode): return self.values


def fixture():
    protocol = json.loads((ROOT / 'manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json').read_text())
    bindings = dict(zip(SLOTS, ('NATIVE35', 'WC_HALF', 'RA_DOUBLE', 'A_NO_P', 'TABLE_PHASE_H1')))
    # Example method identities only, not the final N07/N08 selection.
    shared = list(bindings.values()) + ['FRONT_DENSE_C', 'FRONT_DENSE_A', 'NATIVE26', 'NATIVE18', 'FIXED_PLAIN']
    bound = timing.bind(protocol, bindings, shared)
    return protocol, bindings, shared, bound, timing.prepare_samples(bound, FakeArguments)


def response(planned, sample):
    path = Path(__file__).with_name('test_frozen_shared_batch_r1.py')
    spec = importlib.util.spec_from_file_location('synthetic_N08_execution_response', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    row = module.fake_result(planned, sample)
    row['frozen_input_identity']['installed_contexts'][0][2] = 'fixed-seed0-request'
    row.update(method_install_seconds=.1, guarded_pipeline_without_write_seconds=1.2,
        method_cleanup_seconds=.2, video_write_seconds=.3,
        request_memory_lifecycle=dict(before=dict(seconds=.01), after=dict(seconds=.02)))
    row['frozen_request_cleanup']['collection'] = dict(seconds=.03)
    return row


class TimingExecutionControls(unittest.TestCase):
    def test_full40_binding_preserves_registered_order_and_input_bytes(self):
        protocol, bindings, _, bound, samples = fixture()
        self.assertIsNone(protocol['actual_frozen_method_bindings'])
        self.assertEqual(len(samples), 10)
        self.assertEqual(len(bound['execution_plan']), 40)
        self.assertEqual(bound['scope_counts']['ordinary_pairs'], 1440)
        self.assertEqual(bound['requests'], protocol['requests'])
        self.assertEqual([{k: v for k, v in p.items() if k != 'method'} for p in bound['execution_plan']], matrix())
        self.assertEqual({p['method'] for p in bound['execution_plan']}, set(bindings.values()))

    def test_changed_roles_unshared_point_wrong_seed_or_short_scope_refused(self):
        protocol, bindings, shared, _, _ = fixture()
        for kind in ('role', 'shared', 'seed', 'short'):
            p, b, methods = copy.deepcopy(protocol), dict(bindings), list(shared)
            if kind == 'role': b['GCR_EFFICIENT'] = 'TABLE_PHASE_H1'
            elif kind == 'shared': methods[methods.index('WC_HALF')] = 'WC_DEFAULT'
            elif kind == 'seed': p['requests'][0]['seed'] = 17
            else: p['complete_matrix'].pop()
            with self.assertRaises(ValueError): timing.bind(p, b, methods)

    def test_complete_batch_and_observed_intervals_never_replace_main_clock(self):
        _, _, _, bound, samples = fixture()
        state = timing.run_registered_batch(bound, samples, response)
        self.assertEqual(len(state['runs']), 40)
        self.assertEqual(sum(r['section'] == 'TIMED' for r in state['runs']), 30)
        for row in state['runs']:
            clock = row['timing_intervals']
            self.assertEqual(row['core_seconds'], 1.)
            self.assertEqual(clock['core_text_denoise_VAE_seconds'], 1.)
            self.assertEqual(clock['request_boundary_GC_intervals_seconds'], [.01, .02, .03])
            self.assertFalse(clock['timings_subtracted_to_create_core'])

    def test_seed0_context_actual_threshold_and_formal_copy_or_bad_timer_refused(self):
        _, _, _, bound, samples = fixture()
        planned = next(p for p in bound['execution_plan'] if p['section'] == 'TIMED' and p['slot'] == 'WORLD_CACHE')
        for kind in ('context', 'threshold', 'copy', 'timer'):
            row = {**planned, **response(planned, samples[(planned['scene'], planned['slot'])])}
            if kind == 'context': row['frozen_input_identity']['installed_contexts'][0][2] = 'frozen-input-seed17'
            elif kind == 'threshold': row['installed_thresholds'][0]['net_WC_threshold'] = .12
            elif kind == 'copy': row['in_timing_guided_copies'] = 1
            else: row['guarded_pipeline_without_write_seconds'] = .5
            with self.assertRaises(ValueError): timing.audit_row(row, planned, bound)

    def test_rejection_continues_but_failure_keeps_all40_without_retry(self):
        _, _, _, bound, samples = fixture()
        reject = bound['execution_plan'][26]['id']
        def run(planned, sample):
            if planned['id'] == reject: return dict(status='TEXT_REJECTED', solver_steps=0, guided_pairs=0)
            return response(planned, sample)
        value = timing.run_registered_batch(bound, samples, run)
        self.assertEqual(len(value['runs']), 40)
        self.assertEqual(value['runs'][26]['status'], 'TEXT_REJECTED')
        saved = []; count = 0
        def failed(planned, sample):
            nonlocal count
            count += 1
            if count == 9: raise RuntimeError('SYNTHETIC_FAILURE_NO_RETRY')
            return response(planned, sample)
        with self.assertRaisesRegex(RuntimeError, 'SYNTHETIC_FAILURE'):
            timing.run_registered_batch(bound, samples, failed, save=lambda v: saved.append(copy.deepcopy(v)))
        full = timing.full_rows(saved[-1]['runs'], bound)
        self.assertEqual(len(full), 40)
        self.assertEqual(sum(r['status'] == 'TECH_FAILED' for r in full), 1)
        self.assertEqual(sum(r['status'] == 'NOT_REACHED' for r in full), 31)
        self.assertEqual(count, 9)

    def test_delegate_uses_actual_method_and_registered_warm_mode(self):
        _, _, _, bound, samples = fixture()
        for planned in (bound['execution_plan'][0], bound['execution_plan'][5]):
            sample = samples[(planned['scene'], planned['slot'])]
            events = []
            def reset():
                events.append('RESTORED')
                return dict(original_state_sha256='1' * 64, restored_state_sha256='1' * 64, shared_eval_verified=True)
            with patch.object(timing, 'execute', return_value=response(planned, sample)) as delegated:
                value = timing.execute_one(object(), sample, planned, bound,
                    restore_request_state=reset, synthetic_only=True)
                self.assertEqual(events, ['RESTORED'])
                self.assertEqual(delegated.call_args.args[2], planned['method'])
                self.assertEqual(delegated.call_args.kwargs['audit'], planned['section'] == 'WARMUP')
                self.assertFalse(value['clean_resource_state_accepted_by_this_function'])
            with patch.object(timing, 'execute') as delegated:
                with self.assertRaises(ValueError):
                    timing.execute_one(object(), sample, planned, bound, restore_request_state=lambda: dict(
                        original_state_sha256='1' * 64, restored_state_sha256='2' * 64, shared_eval_verified=True))
                delegated.assert_not_called()


if __name__ == '__main__': unittest.main()
