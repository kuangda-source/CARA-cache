import json
from types import SimpleNamespace

import pytest
import torch

from wcomr.mid_coverage import StateRoundtrip
from wcomr.mid_prefix_audit import cpu_rng_gap_control, receipt_parity, state_components


def test_sealed_receipt_audit_keeps_failure_and_detects_previously_unreached_input_gate():
    left = {k: [] for k in ['input_hashes', 'output_hashes', 'trace', 'block_counts',
                            'state_fingerprints', 'sampling']}
    right = dict(left, input_hashes=['changed'])
    left['input_hashes'] = ['original']
    receipt = {'status': 'TECH_BLOCKED', 'phases': [left, right]}
    before = json.dumps(receipt)
    result = receipt_parity(receipt)
    assert json.dumps(receipt) == before
    assert result['input_mismatch_calls'] == [1] and not result['checks']['input_hashes']
    assert not result['coverage_gate_accepted'] and result['original_status'] == 'TECH_BLOCKED'
    assert result['actual_differing_state_fields'] == 'UNKNOWN_AGGREGATE_HASHES_ONLY'


def test_component_inventory_detects_cache_solver_and_generator_changes():
    generator = torch.Generator().manual_seed(0)
    net = SimpleNamespace(cnt=26, residual_cache=[torch.ones(2), torch.ones(2)])
    solver = SimpleNamespace(_step_index=13, model_outputs=[torch.ones(2)], step=lambda: None)
    snapshot = StateRoundtrip(net, solver, torch.ones(2), generators=[generator])
    original = state_components(snapshot)
    net.residual_cache[1].add_(1); solver.model_outputs[0].add_(1)
    torch.rand(1, generator=generator)
    changed = state_components(snapshot)
    assert {k for k in original if original[k] != changed[k]} == {
        'net.residual_cache', 'solver.model_outputs', 'explicit_generators'}
    snapshot.restore()
    assert state_components(snapshot) == original


def test_official_fps_expression_gap_and_complete_rng_reset_without_dropping_fields():
    source = '''class Video2WorldInference:
    def _get_data_batch_input(self):
        data_batch = {"fps": torch.randint(16, 32, (self.batch_size,)).float()}
'''
    before = torch.random.get_rng_state().clone()
    result = cpu_rng_gap_control(source)
    assert result['differing_cpu_demo_state_fields'] == ['cpu_rng']
    assert result['reset_cpu_control_exact'] and not result['all_state_gate_removed_fields']
    assert torch.equal(before, torch.random.get_rng_state())
    with pytest.raises(ValueError):
        cpu_rng_gap_control(source.replace('16, 32', '16, 33'))
