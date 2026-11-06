"""Complete-scope, price-authority and argument checks with synthetic fixtures."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

from wcomr.frozen_shared_inputs_r1 import bind_selected
from wcomr.frozen_shared_production_r1 import (
    CARD, RUN, STRATEGY, TIMING, PRODUCTION_CPU_STATUS, fingerprint,
    prepare_samples, sampling_source_closure, validate_contract, validate_launch_authority,
)


def fixture():
    path = Path(__file__).with_name('test_frozen_shared_inputs_r1.py')
    spec = importlib.util.spec_from_file_location('synthetic_input_fixture_only', path)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    selected, raw = module.fixture()
    bound = bind_selected(selected, raw)
    config = dict(card=CARD, run_id=RUN, strategy=STRATEGY, main_timing=TIMING,
        memory_policy='REQUEST_BOUNDARY_GC_ONLY', autonomy_exclusive_upper_GPUh=12,
        reference_method='NATIVE35', method_ids=bound['method_ids'],
        bound_input_fingerprint=fingerprint(bound), scope_counts=copy.deepcopy(bound['planned_scope_counts']),
        warm_trace_policy='ALL20_FULL_TRACE_BOTH_REPEATS', guardrails_enabled=True, neighbor_gap_retained=True,
        forecast_complete_GPUh=9., billed_limit_GPUh=10., cumulative_cap_GPUh=104.97136333301378,
        budget_origin_used_GPUh=79.99637737158223,
        **{k: False for k in ('training', 'online_teachers', 'F_B_enabled', 'P_ACR', 'T1',
                             'head_elision', 'deployment_profiling')})
    return config, bound


def authority_fixture(config, bound):
    arguments = dict(revision='SYNTHETIC_REVISION_NOT_A_LAUNCH', gpu_uuid='GPU-SYNTHETIC',
        config_sha256='1' * 64, proof_sha256='2' * 64, registration_sha256='3' * 64)
    registration = dict(source_revision=arguments['revision'])
    proof = dict(source_revision=arguments['revision'], status=PRODUCTION_CPU_STATUS,
        exit_code=0, config_sha256=arguments['config_sha256'], registration_sha256=arguments['registration_sha256'])
    authority = dict(source_revision=arguments['revision'], config_sha256=arguments['config_sha256'],
        production_CPU_sha256=arguments['proof_sha256'], bound_input_fingerprint=fingerprint(bound),
        scope_counts=copy.deepcopy(config['scope_counts']), whole_card_run=RUN,
        gpu_uuid=arguments['gpu_uuid'], forecast_complete_GPUh=config['forecast_complete_GPUh'],
        billed_limit_GPUh=config['billed_limit_GPUh'], cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
        budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
        direct_user_authorization=True, user_reply_quote='SYNTHETIC CONTROL ONLY, NO HUMAN APPROVAL ISSUED',
        launch_id='SYNTHETIC_NOT_DISPATCHED', kind='STANDING_STRICT_UNDER12')
    return registration, proof, authority, arguments


class SharedProductionControls(unittest.TestCase):
    def test_complete180_and_no_false_under12_contract_gate(self):
        config, bound = fixture()
        self.assertEqual(len(validate_contract(config, bound)), 180)
        # CPU preparation can validate a whole >=12 card before asking for its
        # concrete review; permission is enforced at launch, not by shrinking.
        config.update(forecast_complete_GPUh=13., billed_limit_GPUh=14.)
        self.assertEqual(len(validate_contract(config, bound)), 180)

    def test_scope_price_and_algorithm_changes_rejected(self):
        original, bound = fixture()
        for key, value in [('training', True), ('T1', True), ('head_elision', True),
                           ('guardrails_enabled', False), ('forecast_complete_GPUh', None),
                           ('billed_limit_GPUh', 8.), ('bound_input_fingerprint', '0' * 64)]:
            config = copy.deepcopy(original);config[key] = value
            with self.assertRaises(ValueError): validate_contract(config, bound)
        config = copy.deepcopy(original);config['scope_counts']['total_paths'] = 179
        with self.assertRaises(ValueError): validate_contract(config, bound)

    def test_all_typed_argument_variants_and_changed_seed(self):
        _, bound = fixture()
        class DeclaredFakeArguments:
            def __init__(self, **kwargs): self.value = kwargs
            def model_dump(self, mode):
                assert mode == 'json'
                return self.value
        values = prepare_samples(bound, DeclaredFakeArguments)
        self.assertEqual(len(values), 160)
        class WrongArguments(DeclaredFakeArguments):
            def model_dump(self, mode): return {**self.value, 'seed': 0}
        with self.assertRaises(ValueError): prepare_samples(bound, WrongArguments)

    def test_static_dependency_closure_includes_nested_local_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);folder = root/'src/wcomr';folder.mkdir(parents=True)
            (folder/'frozen_shared_execution_r1.py').write_text('from . import alpha\ndef run():\n from .beta import value\n')
            (folder/'alpha.py').write_text('from .beta import value\n')
            (folder/'beta.py').write_text('value = 1\n')
            found = sampling_source_closure(root)
            self.assertEqual(len(found), 3)
            first = found['src/wcomr/beta.py']
            (folder/'beta.py').write_text('value = 2\n')
            self.assertNotEqual(first, sampling_source_closure(root)['src/wcomr/beta.py'])

    def test_under12_permission_bound_to_whole_scope_and_source(self):
        config, bound = fixture()
        registration, proof, authority, arguments = authority_fixture(config, bound)
        validate_launch_authority(config, bound, registration, proof, authority, **arguments)
        for key, bad in [('production_CPU_sha256', '0' * 64), ('launch_id', ''),
                         ('source_revision', 'other'), ('gpu_uuid', 'GPU-OTHER')]:
            changed = copy.deepcopy(authority);changed[key] = bad
            with self.assertRaises(ValueError):
                validate_launch_authority(config, bound, registration, proof, changed, **arguments)
        changed = copy.deepcopy(authority);changed['scope_counts']['total_paths'] = 179
        with self.assertRaises(ValueError):
            validate_launch_authority(config, bound, registration, proof, changed, **arguments)

    def test_at12_specific_whole_card_reply_required(self):
        config, bound = fixture();config.update(forecast_complete_GPUh=11.9, billed_limit_GPUh=12.)
        registration, proof, authority, arguments = authority_fixture(config, bound)
        with self.assertRaisesRegex(ValueError, 'specific complete-card'):
            validate_launch_authority(config, bound, registration, proof, authority, **arguments)
        authority['kind'] = 'SPECIFIC_WHOLE_CARD_APPROVAL'
        validate_launch_authority(config, bound, registration, proof, authority, **arguments)


if __name__ == '__main__':
    unittest.main()
