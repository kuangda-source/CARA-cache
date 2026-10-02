"""CPU-only reanalysis of a sealed prefix receipt; never upgrades its status."""
import ast
import copy
import hashlib
import random
from types import SimpleNamespace

import numpy as np
import torch

from .mid_coverage import StateRoundtrip, tree_digest


def receipt_parity(receipt):
    left, right = receipt['phases']
    keys = ['input_hashes', 'output_hashes', 'trace', 'block_counts',
            'state_fingerprints', 'sampling']
    checks = {key: left[key] == right[key] for key in keys}
    mismatches = [i + 1 for i, (a, b) in enumerate(
        zip(left['input_hashes'], right['input_hashes'])) if a != b]
    return {
        'original_status': receipt['status'], 'checks': checks,
        'input_mismatch_calls': mismatches,
        'input_hash_lengths': [len(left['input_hashes']), len(right['input_hashes'])],
        'state_point_pairs': [{'baseline': a, 'observed': b} for a, b in
                              zip(left['state_fingerprints'], right['state_fingerprints'])],
        'actual_field_level_values_saved': False,
        'actual_differing_state_fields': 'UNKNOWN_AGGREGATE_HASHES_ONLY',
        'coverage_gate_accepted': False,
    }


def state_components(snapshot):
    """Diagnostic inventory of every component already in the full fingerprint."""
    values = {
        **{'net.' + k: getattr(snapshot.net, k) for k in snapshot.keys},
        **{'solver.' + k: v for k, v in vars(snapshot.scheduler).items()
           if not callable(v)},
        'output': snapshot.output, 'python_rng': random.getstate(),
        'numpy_rng': np.random.get_state(), 'cpu_rng': torch.random.get_rng_state(),
        'cuda_rng': torch.cuda.get_rng_state_all() if snapshot.cuda_rng else [],
        'explicit_generators': [g.get_state() for g, _ in snapshot.generators],
    }
    return {key: tree_digest(value) for key, value in values.items()}


def fps_expression(source):
    tree = ast.parse(source)
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef)
               and x.name == 'Video2WorldInference')
    fn = next(x for x in cls.body if isinstance(x, ast.FunctionDef)
              and x.name == '_get_data_batch_input')
    for node in ast.walk(fn):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == 'fps':
                    expected = 'torch.randint(16, 32, (self.batch_size,)).float()'
                    if ast.dump(value) != ast.dump(ast.parse(expected, mode='eval').body):
                        raise ValueError('Pinned FPS expression changed')
                    return ast.Expression(body=copy.deepcopy(value))
    raise ValueError('Official input FPS expression absent')


def cpu_rng_gap_control(source):
    """Reproduce an identified harness gap, not the unsaved GPU field difference."""
    if torch.cuda.is_initialized():
        raise ValueError('CPU-only diagnosis requires uninitialized CUDA')
    expression = compile(ast.fix_missing_locations(fps_expression(source)),
                         '<pinned-official-fps-expression>', 'eval')
    initial = torch.random.get_rng_state().clone()
    py_state, np_state = random.getstate(), np.random.get_state()
    try:
        torch.manual_seed(0)
        common_cpu = torch.random.get_rng_state().clone()

        def one_phase():
            random.setstate(py_state); np.random.set_state(np_state)
            fps = eval(expression, {'torch': torch, 'self': SimpleNamespace(batch_size=1)})
            net = SimpleNamespace(cnt=26, residual_cache=[torch.ones(2), torch.ones(2)])
            solver = SimpleNamespace(_step_index=13, model_outputs=[torch.ones(2)])
            generator = torch.Generator().manual_seed(0)
            saved = StateRoundtrip(net, solver, torch.ones(2), generators=[generator])
            return {'fps': fps.tolist(), 'input_hash': tree_digest({'fps': fps}),
                    'full_state_hash': saved.fingerprint(),
                    'component_hashes': state_components(saved),
                    'output_hash': tree_digest(torch.ones(2))}

        first, second = one_phase(), one_phase()
        torch.random.set_rng_state(common_cpu); fixed_first = one_phase()
        torch.random.set_rng_state(common_cpu); fixed_second = one_phase()
        differing = [key for key in first['component_hashes']
                     if first['component_hashes'][key] != second['component_hashes'][key]]
        assert first['fps'] != second['fps'] and differing == ['cpu_rng']
        assert first['full_state_hash'] != second['full_state_hash']
        assert first['output_hash'] == second['output_hash']
        assert fixed_first == fixed_second
        return {'status': 'CPU_OFFICIAL_FPS_RNG_GAP_REPRODUCED_NOT_GPU_ROOT_CAUSE',
                'unmatched_phases': [first, second], 'differing_cpu_demo_state_fields': differing,
                'reset_cpu_control_exact': True, 'all_state_gate_removed_fields': [],
                'torch_version': torch.__version__, 'cuda_initialized': torch.cuda.is_initialized(),
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                'limitation': 'Actual r2 FPS/RNG/component values were not saved; this proves a harness gap only.'}
    finally:
        torch.random.set_rng_state(initial)
        random.setstate(py_state); np.random.set_state(np_state)
