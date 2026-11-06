"""Synthetic original production CPU captures; no platform CPU job is run."""
import copy
import importlib.util
from pathlib import Path
import unittest

from wcomr.frozen_shared_cpu_acceptance_r1 import accept, CPU_ACCEPTED_STATUS
from wcomr.frozen_shared_production_r1 import sampling_source_closure


def fixture():
    path = Path(__file__).with_name('test_frozen_shared_acceptance_r1.py')
    spec = importlib.util.spec_from_file_location('synthetic_CPU_capture_fixture', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    original, gpu_launch = module.fixture()
    proof = original['production_CPU']; bound = original['bound_inputs']
    proof.update(GPU_submissions=0, ledger_written=False)
    proof['bound_input_fingerprint'] = gpu_launch['bound_input_fingerprint']
    proof['scope_counts'] = original['config']['scope_counts']
    native = [m for m in bound['method_ids'] if m.startswith('NATIVE')]
    proof['guardrail_checks'] = [dict(case_id=c['id'], seed=c['seed'], method=m, unguarded_execution_refused=True)
                                for c in bound['cases'][:2] for m in native]
    proof['native_forward_identity'] = dict(qualified_name=
        'cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward',
        path='/SYNTHETIC_NOT_A_REAL_NATIVE_IMPORT', sha256='a' * 64)
    sources = sampling_source_closure(Path(__file__).resolve().parents[1])
    proof['unchanged_numeric_CPU_reuse'] = dict(status='ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED',
        checked_source_files=len(sources), source_sha256=sources)
    registration = original['registration']; registration['payload_sha256'].update(sources)
    launch = dict(source_revision=gpu_launch['source_revision'], registration_sha256=gpu_launch['registration_sha256'],
        first_collection_not_before_unix=1000., identity=dict(pid=2001, start_ticks=20010))
    return dict(status='N07_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE', launch=launch, observed_unix=2000.,
        registration=registration, registration_sha256=gpu_launch['registration_sha256'],
        payload_verified={n: True for n in registration['payload_sha256']},
        process=dict(pid=2001, state=None, start_ticks=None), GPU_submissions=0, ledger_written=False,
        files={k: dict(exists=True, sha256=original[sha], data=original[data]) for k, sha, data in (
            ('config', 'config_sha256', 'config'), ('proof', 'production_CPU_sha256', 'production_CPU'),
            ('bound_inputs', 'bound_inputs_sha256', 'bound_inputs'))}
        | {'bundle': dict(exists=True, sha256='b' * 64, data=module.synthetic_CPU_bundle(launch['source_revision']))})


class ProductionCPUAcceptanceControls(unittest.TestCase):
    def test_complete6_command_160_types_full180_and99_dependencies(self):
        value = fixture(); result = accept(value)
        self.assertEqual(result['status'], CPU_ACCEPTED_STATUS)
        self.assertEqual(result['CPU_commands'], 6)
        self.assertEqual(result['actual_sample_argument_variants'], 160)
        self.assertEqual(result['scope_counts']['total_paths'], 180)
        self.assertFalse(result['real_video_or_speed_result'])

    def test_live_handle_wait_and_reused_PID_is_not_the_original_CPU_job(self):
        value = fixture(); value['process'].update(state='R', start_ticks=20010)
        self.assertFalse(accept(value)['CPU_accepted'])
        value['process']['start_ticks'] = 99999
        self.assertTrue(accept(value)['CPU_accepted'])

    def test_missing_and_failed_original_results_preserve_failure(self):
        value = fixture(); value['files']['proof']['exists'] = False
        self.assertFalse(accept(value)['CPU_accepted'])
        value['files']['bundle']['data'].update(status='N07_SHARED180_ACTUAL_PRODUCTION_CPU_FAILED_NOT_GPU', exit_code=1)
        result = accept(value)
        self.assertIn('FAILED_RESULT_RETAINED', result['status'])
        self.assertTrue(result['no_GPU_launch_authorized'])

    def test_short_commands_wrong_source_scope_weights_or_numeric_field_rejected(self):
        original = fixture()
        for kind in ('commands', 'source', 'scope', 'weights', 'numeric', 'guard'):
            value = copy.deepcopy(original); bundle = value['files']['bundle']['data']; proof = value['files']['proof']['data']
            if kind == 'commands': bundle['commands'].pop()
            elif kind == 'source': proof['source_revision'] = 'OTHER'
            elif kind == 'scope': proof['scope_counts'] = {**proof['scope_counts'], 'total_paths': 179}
            elif kind == 'weights': proof['model_weights_loaded'] = 1
            elif kind == 'numeric': proof['unchanged_numeric_CPU_reuse']['source_sha256'][
                next(iter(proof['unchanged_numeric_CPU_reuse']['source_sha256']))] = '0' * 64
            else: proof['guardrail_checks'].pop()
            with self.assertRaises(ValueError): accept(value)

    def test_pre_ETA_or_foreign_payload_capture_rejected(self):
        value = fixture(); value['observed_unix'] = 999.
        with self.assertRaises(ValueError): accept(value)
        value['observed_unix'] = 2000.; value['payload_verified'][next(iter(value['payload_verified']))] = False
        with self.assertRaises(ValueError): accept(value)


if __name__ == '__main__': unittest.main()
