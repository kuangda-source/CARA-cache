import ast
import __future__
import copy
import hashlib
import os
import random
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Optional
from unittest.mock import patch

import numpy as np
import pytest
import torch

from wcomr.prepared_input import PreparedInputReplay, RNGState, input_signatures
from wcomr.mid_parity_scope import validate_parity_scope


def test_replay_preserves_rng_transition_and_isolated_batch_and_refuses_changed_inputs():
    def prepare(video, prompt):
        return {'video': video.clone(), 'fps': torch.randint(16, 32, (1,)).float(),
                'metadata': prompt, 'numpy': float(np.random.rand()), 'python': random.random()}
    rng = RNGState(); initial = rng.signatures()
    replay = PreparedInputReplay(prepare)
    a = replay(torch.ones(2), 'same'); post = RNGState().signatures()
    a['video'].zero_()
    rng.restore(); b = replay(torch.ones(2), 'same')
    assert torch.equal(b['video'], torch.ones(2)) and RNGState().signatures() == post
    assert replay.calls[0]['prepared'] == replay.calls[1]['prepared']
    rng.restore()
    with pytest.raises(ValueError): replay(torch.ones(2), 'changed')
    torch.rand(1)
    with pytest.raises(ValueError): replay(torch.ones(2), 'same')
    rng.restore(); assert rng.signatures() == initial


def test_named_signatures_detect_each_input_and_non_tensor_condition_change():
    args = (torch.ones(2),)
    kwargs = {'fps': torch.tensor([16.]), 'data_type': 'video', 'padding': None}
    a = input_signatures(args, kwargs)
    assert a == input_signatures(args, dict(reversed(list(kwargs.items()))))
    for key, value in [('fps', torch.tensor([17.])), ('data_type', 'image'), ('padding', torch.zeros(1))]:
        b = input_signatures(args, dict(kwargs, **{key: value}))
        assert a != b and a['kwargs'][key] != b['kwargs'][key]


def official_prepare_cpu_control(path):
    """Execute actual pinned official function; emulate GPU transfer/text encoder only."""
    source = Path(path).read_text()
    expected = '59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95'
    assert hashlib.sha256(source.encode()).hexdigest() == expected
    cls = next(x for x in ast.parse(source).body if isinstance(x, ast.ClassDef)
               and x.name == 'Video2WorldInference')
    fn = copy.deepcopy(next(x for x in cls.body if isinstance(x, ast.FunctionDef)
                            and x.name == '_get_data_batch_input'))
    namespace = {'torch': torch, 'Dict': Dict, 'Optional': Optional,
                 '_DEFAULT_NEGATIVE_PROMPT': 'cpu-negative'}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 str(path), 'exec', flags=__future__.annotations.compiler_flag), namespace)
    encoder = SimpleNamespace(compute_text_embeddings_online=lambda **k: torch.ones(1, 3, 4))
    owner = SimpleNamespace(batch_size=1, model=SimpleNamespace(text_encoder=encoder))
    original = lambda **kw: namespace['_get_data_batch_input'](owner, **kw)
    saved = RNGState()
    with patch.object(torch.Tensor, 'cuda', lambda tensor, *a, **kw: tensor):
        replay = PreparedInputReplay(original)
        shared = RNGState()
        outputs = []
        for observed in [False, True]:
            shared.restore()
            batch = replay(video=torch.ones(1, 3, 4, 4, 4), prompt='cpu-control',
                           num_conditional_frames=1, negative_prompt='cpu-negative')
            if observed:
                shadow = RNGState()
                torch.rand(2); np.random.rand(); random.random()
                shadow.restore()
            outputs.append({'inputs': input_signatures((), batch), 'rng': RNGState().signatures()})
        assert outputs[0] == outputs[1]
        assert len(replay.calls) == 2 and replay.calls[0]['source'] != replay.calls[1]['source']
    saved.restore()
    assert not torch.cuda.is_initialized()
    return {'official_source_sha256': expected, 'observer_off_on_equal': True,
            'prepared_calls': replay.calls, 'cuda_initialized': False,
            'limits': 'Actual official preparation body with CPU mock GPU-transfer and fixed text-encoder output; not model/GPU preparation acceptance.'}


def test_actual_official_preparation_cpu_off_on_when_source_available():
    source = os.environ.get('WC_LIFECYCLE_SOURCE')
    if not source:
        pytest.skip('Pinned runtime source checked in actual deployment CPU environment')
    official_prepare_cpu_control(source)


def test_r3_scope_refuses_r4_and_resampling_all_middle_points():
    config = {'card': 'WC-INPUT-STATE-PARITY-R3-20261003-A', 'max_gpu_wall_seconds': 1200,
              'capture_calls': [25, 26], 'capture_layers': [2], 'stop_after_solver_steps': 13,
              'state_steps': [13], 'phases': ['baseline_prefix', 'observed_prefix'],
              'policy': {'sim': .1, 'cdf': .98}, 'warmups': 1, 'repeats': 3,
              'pv_skipping': False, 'deployment_sparse': False}
    assert validate_parity_scope(config) == {(25, 2), (26, 2)}
    for key, value in [('card', 'R4'), ('capture_calls', [25, 26, 35, 36]),
                       ('capture_layers', list(range(2, 28))), ('stop_after_solver_steps', 18),
                       ('deployment_sparse', True), ('max_gpu_wall_seconds', 1201)]:
        with pytest.raises(ValueError): validate_parity_scope(dict(config, **{key: value}))
