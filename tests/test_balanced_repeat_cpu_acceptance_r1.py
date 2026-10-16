"""Synthetic original CPU receipts, never a server production-CPU acceptance."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest

from wcomr import balanced_repeat_cpu_acceptance_r1 as cpu
from wcomr.balanced_repeat_production_r1 import CPU_STATUS
from wcomr.frozen_shared_production_r1 import fingerprint

SPEC = importlib.util.spec_from_file_location('N08_CPU_fixture_only',
    Path(__file__).with_name('test_balanced_repeat_production_r1.py'))
FIXTURE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(FIXTURE)


def bundle(revision):
    commands = [dict(command=['python', '-m', 'unittest', 'discover', '-s', '/SYNTHETIC/tests', '-p', name, '-v'], exit_code=0)
                for name in cpu.PATTERNS]
    commands.append(dict(command=['python', '/SYNTHETIC/scripts/run_wc_paper_N08_balanced_full40_r1.py', '--cpu-check'], exit_code=0))
    return dict(status=cpu.BUNDLE_STATUS, source_revision=revision, exit_code=0, commands=commands, wall_seconds=1.,
        GPU_submissions=0, model_weights_loaded=0, ledger_written=False, shared_runtime_written=False, original_base_stage_written=False)


def fixture():
    config, protocol, shared, freeze, bound, _ = FIXTURE.fixture()
    refs = {name: dict(ref='SYNTHETIC/' + name + '.json', sha256=fingerprint(value))
            for name, value in [('timing_protocol', protocol), ('method_freeze', freeze)]}
    shared['references'] = dict(method_freeze=refs['method_freeze'])
    refs['shared_config'] = dict(ref='SYNTHETIC/shared_config.json', sha256=fingerprint(shared))
    config['references'] = refs
    numeric = {'src/SYNTHETIC_NUMERIC_' + str(i) + '.py': hashlib.sha256(str(i).encode()).hexdigest() for i in range(99)}
    runner = 'scripts/run_wc_paper_N08_balanced_full40_r1.py'
    registration = dict(source_revision='SYNTHETIC_NOT_DEPLOYED', payload_sha256={**numeric, runner: 'a' * 64})
    proof = dict(status=CPU_STATUS, exit_code=0, source_revision=registration['source_revision'],
        registration_sha256=fingerprint(registration), config_sha256=fingerprint(config),
        bound_timing_fingerprint=fingerprint(bound), scope_counts=config['scope_counts'], matrix=bound['execution_plan'],
        actual_sample_argument_variants=10, runner_source_sha256='a' * 64,
        CUDA_initialized=False, GPU_submissions=0, model_weights_loaded=0, ledger_written=False,
        native_forward_identity=dict(qualified_name='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward', sha256='b' * 64),
        guardrail_checks=[dict(scene=r['name'], seed=0, method='NATIVE35', unguarded_execution_refused=True) for r in bound['requests']],
        unchanged_numeric_CPU_reuse=dict(status='ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED', checked_source_files=99, source_sha256=numeric))
    files = {name: dict(exists=True, data=value, sha256=fingerprint(value)) for name, value in [
        ('bundle', bundle(registration['source_revision'])), ('proof', proof), ('config', config),
        ('timing_protocol', protocol), ('shared_config', shared), ('method_freeze', freeze)]}
    launch = dict(source_revision=registration['source_revision'], registration_sha256=fingerprint(registration),
        first_collection_not_before_unix=10., identity=dict(pid=9001, start_ticks=90010))
    return dict(status='N08_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE', launch=launch, registration=registration,
        registration_sha256=fingerprint(registration), observed_unix=20., payload_verified={n: True for n in registration['payload_sha256']},
        process=dict(pid=9001, state=None, start_ticks=None), files=files, GPU_submissions=0, ledger_written=False)


class CPUAcceptanceControls(unittest.TestCase):
    def test_complete_original_nine_commands_accept_no_GPU_or_speed(self):
        value = fixture(); original = copy.deepcopy(value); result = cpu.accept(value)
        self.assertEqual(value, original)
        self.assertTrue(result['CPU_accepted'])
        self.assertEqual(result['CPU_commands'], 9)
        self.assertEqual(result['actual_sample_argument_variants'], 10)
        self.assertFalse(result['whole_GPU_card_selected']); self.assertFalse(result['real_video_or_speed_result'])

    def test_live_original_is_wait_and_pid_reuse_is_not_the_original(self):
        value = fixture(); value['process'].update(state='R', start_ticks=90010)
        self.assertFalse(cpu.accept(value)['CPU_accepted'])
        self.assertIn('STILL_RUNNING', cpu.accept(value)['status'])
        value['process']['start_ticks'] = 90011
        self.assertTrue(cpu.accept(value)['CPU_accepted'])

    def test_failed_or_missing_original_result_never_authorizes_GPU(self):
        value = fixture(); value['files']['bundle']['data'].update(status='FAILED', exit_code=1)
        result = cpu.accept(value)
        self.assertFalse(result['CPU_accepted']); self.assertTrue(result['no_GPU_launch_authorized'])
        value = fixture(); value['files']['proof']['exists'] = False
        self.assertIn('MISSING_RESULTS', cpu.accept(value)['status'])

    def test_early_source_payload_and_reference_changes_refused(self):
        for kind in ('early', 'source', 'payload', 'reference'):
            value = fixture()
            if kind == 'early': value['observed_unix'] = 9.
            elif kind == 'source': value['registration']['source_revision'] = 'OTHER_SOURCE'
            elif kind == 'payload': value['payload_verified'].pop(next(iter(value['payload_verified'])))
            else: value['files']['method_freeze']['sha256'] = '0' * 64
            with self.subTest(kind=kind), self.assertRaises(ValueError): cpu.accept(value)

    def test_typed_scope_native_guard_numeric_dependencies_and_GPU_initialization_refused(self):
        for kind in ('typed', 'scope', 'guard', 'native', 'numeric', 'GPU'):
            value = fixture(); proof = value['files']['proof']['data']
            if kind == 'typed': proof['actual_sample_argument_variants'] = 9
            elif kind == 'scope': proof['matrix'].pop()
            elif kind == 'guard': proof['guardrail_checks'][0]['unguarded_execution_refused'] = False
            elif kind == 'native': proof['native_forward_identity']['qualified_name'] = 'SYNTHETIC_OTHER_CLASS'
            elif kind == 'numeric': proof['unchanged_numeric_CPU_reuse']['source_sha256']['src/EXTRA.py'] = '0' * 64
            else: proof['CUDA_initialized'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError): cpu.accept(value)

    def test_bundle_cannot_skip_actual_entry_or_keep_only_a_small_passing_check(self):
        for kind in ('short', 'wrong_entry', 'failed', 'weights'):
            value = fixture(); b = value['files']['bundle']['data']
            if kind == 'short': b['commands'].pop()
            elif kind == 'wrong_entry': b['commands'][-1]['command'][1] = '/SYNTHETIC/scripts/run_wc_paper_N07_frozen_shared180_r1.py'
            elif kind == 'failed': b['commands'][0]['exit_code'] = 1
            else: b['model_weights_loaded'] = 1
            with self.subTest(kind=kind), self.assertRaises(ValueError): cpu.accept(value)


if __name__ == '__main__': unittest.main()
