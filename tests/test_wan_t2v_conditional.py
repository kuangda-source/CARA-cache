"""Execute full pinned native T2V body with CPU model/T5/VAE/scheduler spies."""
import ast
from contextlib import contextmanager
import gc
import hashlib
import inspect
import math
import os
from pathlib import Path
import random
import types
import warnings

import pytest
import torch
from wcomr.wan_t2v_conditional import conditional_t2v_scope, build_conditional_t2v, WAN_TI2V_SOURCE_SHA256


@pytest.fixture
def fixture(monkeypatch):
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '')
    path = Path(os.environ.get('L0_WAN_TI2V_SOURCE', '.sync/l0_interface_sources_20261001/Wan-Video--Wan2.2/wan/textimage2video.py')).resolve()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == WAN_TI2V_SOURCE_SHA256
    source = ast.parse(path.read_text());klass = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'WanTI2V')
    schedulers = []
    class Scheduler:
        def __init__(self, **kwargs): self.flows = []; schedulers.append(self)
        def set_timesteps(self, steps, device, shift): self.timesteps = torch.linspace(999, 100, steps, device=device)
        def step(self, flow, timestep, latent, **kwargs): self.flows.append(flow.clone()); return (latent - flow.float() * .001,)
    class Model:
        def __init__(self): self.calls = []; self.cond = 1.0078125; self.negative = 1000.; self.dtype = torch.float32
        def __call__(self, latent, **kwargs):
            role = float(kwargs['context'][0][0]);self.calls.append((role, latent[0].clone(), kwargs['t'].clone()))
            return [torch.full_like(latent[0], self.cond if role == 1 else self.negative, dtype=self.dtype)]
        def to(self, *args, **kwargs): return self
    class Text:
        def __init__(self): self.calls = []
        def __call__(self, prompts, device): self.calls.extend(prompts); return [torch.tensor([1. if prompts[0] == 'positive' else 0.], device=device)]
    class VAE:
        model = types.SimpleNamespace(z_dim=48)
        def decode(self, x): return x
    namespace = {'__name__': '_cpu_wan_fixture', 'torch': torch, 'math': math, 'random': random, 'contextmanager': contextmanager,
                 'gc': gc, 'dist': types.SimpleNamespace(is_initialized=lambda: False),
                 'FlowUniPCMultistepScheduler': Scheduler, 'tqdm': lambda x: x,
                 'masks_like': lambda noise, zero: ([torch.ones_like(noise[0])], [torch.ones_like(noise[0])])}
    exec(compile(ast.Module(body=[klass], type_ignores=[]), str(path), 'exec'), namespace)
    native = namespace['WanTI2V']
    def make():
        obj = object.__new__(native);obj.vae = VAE();obj.model = Model();obj.text_encoder = Text()
        obj.vae_stride = (4, 16, 16);obj.patch_size = (1, 2, 2);obj.sp_size = 1;obj.t5_cpu = True
        obj.sample_neg_prompt = 'negative';obj.device = torch.device('cpu');obj.param_dtype = torch.bfloat16
        obj.num_train_timesteps = 1000;obj.init_on_cpu = False;obj.rank = 0
        return obj
    return path, native, make, schedulers


def generate(obj, guide):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return obj.t2v('positive', size=(32, 32), frame_num=5, sampling_steps=4,
                       guide_scale=guide, seed=0, offload_model=False)


def test_native_guide5_bit_equal_full_body_inputs_and_output(fixture):
    path, klass, make, schedulers = fixture;one = make();before = generate(one, 5.)
    original, i2v = klass.t2v, klass.i2v
    with conditional_t2v_scope(klass, path):
        two = make();after = generate(two, 5.)
        assert klass.i2v is i2v and inspect.signature(klass.t2v) == inspect.signature(original)
    assert torch.equal(before, after) and klass.t2v is original
    assert len(one.model.calls) == len(two.model.calls) == 8
    assert all(a[0] == b[0] and torch.equal(a[1], b[1]) and torch.equal(a[2], b[2])
               for a, b in zip(one.model.calls, two.model.calls))
    assert one.text_encoder.calls == two.text_encoder.calls == ['positive', 'negative']
    assert not torch.cuda.is_initialized()


def test_guide1_only_conditional_forward_preserves_initial_seeded_noise(fixture):
    path, klass, make, schedulers = fixture;reference = make();generate(reference, 1.)
    with conditional_t2v_scope(klass, path):
        obj = make();generate(obj, 1.)
    assert len(reference.model.calls) == 8 and len(obj.model.calls) == 4
    assert all(role == 1 for role, *_ in obj.model.calls)
    assert torch.equal(reference.model.calls[0][1], obj.model.calls[0][1])
    assert all(torch.equal(flow, torch.full_like(flow, obj.model.cond)) for flow in schedulers[-1].flows)
    assert obj.text_encoder.calls == ['positive', 'negative']


def test_bf16_guide1_is_intentionally_conditional_not_stock_cancellation(fixture):
    path, klass, make, schedulers = fixture;reference = make();reference.model.dtype = torch.bfloat16
    generate(reference, 1.);old_flow = schedulers[-1].flows[0]
    with conditional_t2v_scope(klass, path):
        obj = make();obj.model.dtype = torch.bfloat16;generate(obj, 1.)
    new_flow = schedulers[-1].flows[0]
    assert new_flow.dtype == torch.bfloat16 and not torch.equal(old_flow, new_flow)
    assert torch.equal(new_flow, torch.full_like(new_flow, obj.model.cond))


def test_scope_restores_on_exception(fixture):
    path, klass, make, schedulers = fixture;original = klass.t2v
    with pytest.raises(RuntimeError, match='test interruption'):
        with conditional_t2v_scope(klass, path): raise RuntimeError('test interruption')
    assert klass.t2v is original


def test_nested_adaptation_refused_without_losing_outer_restore(fixture):
    path, klass, make, schedulers = fixture;original = klass.t2v
    with conditional_t2v_scope(klass, path):
        with pytest.raises(ValueError):
            with conditional_t2v_scope(klass, path): pass
    assert klass.t2v is original


def test_wrong_source_digest_refused(fixture, tmp_path):
    path, klass, make, schedulers = fixture;bad = tmp_path / 'wrong.py';bad.write_text(path.read_text() + '\n')
    with pytest.raises(ValueError, match='source differs'): build_conditional_t2v(klass.t2v, bad)


def test_wrong_import_origin_refused(fixture):
    path, klass, make, schedulers = fixture
    def wrong(*args, **kwargs): raise AssertionError('must not execute')
    with pytest.raises(ValueError, match='not from the verified source'): build_conditional_t2v(wrong, path)
