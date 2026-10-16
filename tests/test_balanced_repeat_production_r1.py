"""Whole40 contracts and tiny real CPU artifacts; never Cosmos inference."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import balanced_repeat_production_r1 as production
from wcomr import balanced_repeat_execution_r1 as execution
from wcomr.frozen_shared_production_r1 import fingerprint, sha

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('synthetic_N08_contract_inputs',
    Path(__file__).with_name('test_balanced_repeat_execution_r1.py'))
FIXTURE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(FIXTURE)


def fixture():
    protocol, bindings, shared, bound, samples = FIXTURE.fixture()
    shared_config = dict(method_ids=shared, cumulative_cap_GPUh=104.97136333301378,
                         budget_origin_used_GPUh=79.99637737158223)
    freeze = dict(parameters_frozen_from='DEVELOPMENT_ONLY', final_test_outputs_seen=False,
                  method_ids=shared, repeat_timing_bindings=bindings)
    config = dict(card=production.CARD, run_id=production.RUN, scope_counts=execution.COUNTS.copy(),
        strategy=production.STRATEGY, main_timing=production.TIMING, memory_policy='REQUEST_BOUNDARY_GC_ONLY',
        reference_method='NATIVE35', warm_trace_policy='ALL10_FULL36_GUIDED_TRACE',
        clean_resource_requirement='NO_CONCURRENT_WORLD_CACHE_GPU_OR_CPU_METRICS',
        autonomy_exclusive_upper_GPUh=12, guardrails_enabled=True, resource_boundary_audit=True,
        same_round_native_reference=True, bindings=bindings, bound_timing_fingerprint=fingerprint(bound),
        forecast_complete_GPUh=2., billed_limit_GPUh=3., cumulative_cap_GPUh=104.97136333301378,
        budget_origin_used_GPUh=79.99637737158223,
        **{k: False for k in ('training', 'online_teachers', 'F_B_enabled', 'P_ACR', 'T1', 'head_elision', 'deployment_profiling')})
    return config, protocol, shared_config, freeze, bound, samples


class ProductionControls(unittest.TestCase):
    def test_complete_contract_reuses_exact_protocol_and_frozen_roles(self):
        config, protocol, shared, freeze, expected, _ = fixture()
        original = copy.deepcopy((config, protocol, shared, freeze))
        self.assertEqual(production.validate_contract(config, protocol, shared, freeze), expected)
        self.assertEqual((config, protocol, shared, freeze), original)
        self.assertEqual(len(expected['execution_plan']), 40)

    def test_changed_scope_teacher_clock_budget_or_binding_rejected(self):
        for kind in ('scope', 'clock', 'warm', 'profiling', 'budget', 'cost', 'matrix', 'fingerprint'):
            config, protocol, shared, freeze, _, _ = fixture()
            if kind == 'scope': config['scope_counts']['scientific_paths'] = 29
            elif kind == 'clock': config['main_timing'] = 'DENOISE_ONLY'
            elif kind == 'warm': config['warm_trace_policy'] = 'FIRST_ONLY'
            elif kind == 'profiling': config['deployment_profiling'] = True
            elif kind == 'budget': config['budget_origin_used_GPUh'] = 0
            elif kind == 'cost': config['forecast_complete_GPUh'] = float('nan')
            elif kind == 'matrix': protocol['complete_matrix'].pop()
            else: config['bound_timing_fingerprint'] = 'a' * 64
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                production.validate_contract(config, protocol, shared, freeze)

    def test_cannot_select_timing_roles_after_final_outputs_or_from_another_freeze(self):
        for kind in ('seen_test', 'no_binding', 'changed_binding', 'changed_shared_ids'):
            config, protocol, shared, freeze, _, _ = fixture()
            if kind == 'seen_test': freeze['final_test_outputs_seen'] = True
            elif kind == 'no_binding': freeze['repeat_timing_bindings'] = None
            elif kind == 'changed_binding':
                freeze['repeat_timing_bindings'] = {**freeze['repeat_timing_bindings'], 'WORLD_CACHE': 'WC_DEFAULT'}
            else: shared['method_ids'] = list(reversed(shared['method_ids']))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                production.validate_contract(config, protocol, shared, freeze)

    def test_stage_local_reference_hash_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root / 'ref.json'; path.write_text('{"synthetic":true}')
            self.assertEqual(production.read_reference(root, dict(ref='ref.json', sha256=sha(path))), {'synthetic': True})
            for binding in (dict(ref='../ref.json', sha256=sha(path)), dict(ref='ref.json', sha256='0' * 64)):
                with self.assertRaises(ValueError): production.read_reference(root, binding)

    def test_separate_launch_authority_cannot_borrow_N07_or_under12_for_large_card(self):
        config, _, _, _, bound, _ = fixture()
        registration = dict(source_revision='a' * 40)
        proof = dict(source_revision='a' * 40, status=production.CPU_STATUS, exit_code=0,
            registration_sha256='1' * 64, config_sha256='2' * 64,
            bound_timing_fingerprint=fingerprint(bound), scope_counts=execution.COUNTS.copy())
        authority = dict(source_revision='a' * 40, config_sha256='2' * 64, production_CPU_sha256='3' * 64,
            bound_timing_fingerprint=fingerprint(bound), scope_counts=execution.COUNTS.copy(),
            whole_card_run=production.RUN, gpu_uuid='GPU-SYNTHETIC', forecast_complete_GPUh=2.,
            billed_limit_GPUh=3., cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
            budget_origin_used_GPUh=config['budget_origin_used_GPUh'], direct_user_authorization=True,
            user_reply_quote='SYNTHETIC_TEST_ONLY_NOT_APPROVAL', launch_id='SYNTHETIC', kind='STANDING_STRICT_UNDER12')
        kwargs = dict(revision='a' * 40, gpu_uuid='GPU-SYNTHETIC', config_sha256='2' * 64,
                      proof_sha256='3' * 64, registration_sha256='1' * 64)
        production.validate_launch_authority(config, bound, registration, proof, authority, **kwargs)
        authority['whole_card_run'] = 'wc-paper-n07-frozen-shared180-r1'
        with self.assertRaises(ValueError): production.validate_launch_authority(config, bound, registration, proof, authority, **kwargs)
        authority['whole_card_run'] = production.RUN
        config['billed_limit_GPUh'] = authority['billed_limit_GPUh'] = 12.
        with self.assertRaises(ValueError): production.validate_launch_authority(config, bound, registration, proof, authority, **kwargs)
        authority['kind'] = 'SPECIFIC_WHOLE_CARD_APPROVAL'
        production.validate_launch_authority(config, bound, registration, proof, authority, **kwargs)

    def test_other_registered_GPU_job_is_not_clean_capacity(self):
        pool = dict(jobs={'own': dict(status='RESERVED_OR_RUNNING'), 'other': dict(status='SETTLED')})
        value = production.clean_registered_jobs(pool, 'own')
        self.assertTrue(value['observation_only_not_entire_interval_cleanliness'])
        pool['jobs']['other']['status'] = 'RESERVED_OR_RUNNING'
        with self.assertRaises(ValueError): production.clean_registered_jobs(pool, 'own')

    def test_archive_tiny_actual_CPU_warm_tensors_and_formal_without_guided_copy(self):
        import torch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); tiny = torch.tensor([[1., 2.]])
            raw = dict(status='COMPLETE', final_latent=tiny, guided=[tiny.clone() for _ in range(36)])
            warm = production.archive_output(raw, dict(section='WARMUP'), root / 'warm', root, expected_shape=(1, 2))
            self.assertEqual(warm['warm_guided_outputs'], 36)
            artifact = warm['warm_guided_artifact']; self.assertEqual(sha(artifact['path']), artifact['sha256'])
            self.assertEqual(len(torch.load(artifact['path'], map_location='cpu', weights_only=True)['guided']), 36)
            self.assertIn('guided', raw)
            formal = production.archive_output(dict(status='COMPLETE', final_latent=tiny),
                dict(section='TIMED'), root / 'formal', root, expected_shape=(1, 2))
            self.assertNotIn('warm_guided_artifact', formal)
            with self.assertRaises(FileExistsError): production.archive_output(dict(status='COMPLETE', final_latent=tiny),
                dict(section='TIMED'), root / 'formal', root, expected_shape=(1, 2))

    def test_incomplete_warm_formal_copy_nonfinite_or_foreign_output_refused(self):
        import torch
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); tiny = torch.tensor([[1., 2.]])
            variants = [dict(section='WARMUP', data=dict(status='COMPLETE', final_latent=tiny, guided=[tiny] * 35)),
                dict(section='TIMED', data=dict(status='COMPLETE', final_latent=tiny, guided=[tiny] * 36)),
                dict(section='TIMED', data=dict(status='COMPLETE', final_latent=tiny * float('nan'))),
                dict(section='TIMED', data=dict(status='TEXT_REJECTED', final_latent=tiny))]
            for i, variant in enumerate(variants):
                with self.subTest(i=i), self.assertRaises(ValueError):
                    production.archive_output(variant['data'], variant, root / str(i), root, expected_shape=(1, 2))
            with self.assertRaises(ValueError): production.archive_output(dict(status='COMPLETE', final_latent=tiny),
                dict(section='TIMED'), root.parent / 'foreign', root, expected_shape=(1, 2))

    def test_actual_executor_shaped_warm_result_needs_no_preinvented_count(self):
        import torch
        _, _, _, _, bound, samples = fixture()
        planned = bound['execution_plan'][0]; sample = samples[(planned['scene'], planned['slot'])]
        raw = FIXTURE.response(planned, sample)
        # Accepted executor returns the actual guided list. Its count metadata
        # is added by the production archive, not by the sampling function.
        raw.pop('warm_guided_outputs')
        raw['guided'] = [torch.ones(1, 2) for _ in range(36)]
        with patch.object(execution, 'execute', return_value=raw):
            row = execution.execute_one(object(), sample, planned, bound, restore_request_state=lambda: dict(
                original_state_sha256='1' * 64, restored_state_sha256='1' * 64, shared_eval_verified=True))
        self.assertEqual(row['warm_guided_outputs'], 36)

    def test_incomplete_actual_warm_list_and_formal_guided_copy_fail_before_archive(self):
        _, _, _, _, bound, samples = fixture()
        for planned in (bound['execution_plan'][0], bound['execution_plan'][5]):
            sample = samples[(planned['scene'], planned['slot'])]
            raw = FIXTURE.response(planned, sample)
            raw['guided'] = [None] * 35
            with patch.object(execution, 'execute', return_value=raw), self.assertRaises(ValueError):
                execution.execute_one(object(), sample, planned, bound, restore_request_state=lambda: dict(
                    original_state_sha256='1' * 64, restored_state_sha256='1' * 64, shared_eval_verified=True))

    def test_metric_process_observation_is_bounded_and_does_not_stop_another_owner(self):
        spec = importlib.util.spec_from_file_location('N08_script_without_main',
            ROOT / 'scripts/run_wc_paper_N08_balanced_full40_r1.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        fake = ('101 python /home/gaokuangda/data/gkd/worldcache_omr/.sync/stage/scripts/postprocess_wc_test.py\n'
                '102 python /different/project/scripts/postprocess_wc_test.py\n'
                '103 python /home/gaokuangda/data/gkd/worldcache_omr/.sync/stage/scripts/run_wc_test.py\n')
        with patch.object(module.subprocess, 'check_output', return_value=fake) as command:
            value = module.metric_processes(Path('/home/gaokuangda/data/gkd/worldcache_omr'), own_pid=103)
        self.assertEqual(value, [dict(pid=101, kind='PROJECT_METRIC_ENTRYPOINT')])
        self.assertEqual(command.call_args.args[0], ['ps', '-eo', 'pid=,args='])


if __name__ == '__main__': unittest.main()
