"""Pinned Wan decode bodies with tiny declared CPU causal-convolution weights."""
import ast
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys
import time
import types
import unittest

import torch

from wcomr.cara_read_write_vae_r1 import FunctionalWan21Decode, WAN_PATH
from wcomr.mid_coverage import tree_digest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('CARA_READ_WRITE_VAE_RUNTIME', ROOT/'.sync/read-write-vae-source-r2'))
METRICS = {}


def fixture():
    module = types.ModuleType('read_write_Wan21_declared_CPU')
    module.__file__ = str(RUNTIME/WAN_PATH)
    sys.modules[module.__name__] = module
    vars(module).update(torch=torch, nn=torch.nn, F=torch.nn.functional, time=time,
        VideoTokenizerInterface=object, BenchmarkTimes=object, CACHE_T=2,
        log=types.SimpleNamespace(warning=lambda *args: None))
    nodes = [n for n in ast.parse((RUNTIME/WAN_PATH).read_bytes()).body
             if (isinstance(n, ast.ClassDef) and n.name in
                 ('CausalConv3d', 'WanVAE_', 'WanVAE', 'Wan2pt1VAEInterface'))
             or (isinstance(n, ast.FunctionDef) and n.name == 'count_conv3d')]
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future]+nodes, type_ignores=[])),
                 str(RUNTIME/WAN_PATH), 'exec'), vars(module))

    class TinyCausalDecoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = module.CausalConv3d(16, 3, 3, padding=1, bias=False).double()
            with torch.no_grad():
                self.conv.weight.fill_(.007)

        def forward(self, x, *, feat_cache, feat_idx):
            index = feat_idx[0];previous = feat_cache[index]
            value = self.conv(x, previous)
            joined = x if previous is None else torch.cat([previous, x], dim=2)
            feat_cache[index] = joined[:, :, -2:].clone()
            feat_idx[0] += 1
            if previous is not None:
                value = value.repeat_interleave(4, dim=2)
            return value.repeat_interleave(8, dim=3).repeat_interleave(8, dim=4)

    codec = module.WanVAE_.__new__(module.WanVAE_)
    torch.nn.Module.__init__(codec)
    codec.z_dim = 16
    codec.conv2 = torch.nn.Conv3d(16, 16, 1, bias=False).double()
    codec.decoder = TinyCausalDecoder()
    codec.encoder = module.CausalConv3d(16, 16, 1, bias=False).double()
    with torch.no_grad():
        codec.conv2.weight.fill_(.03)
    codec.eval().requires_grad_(False)
    codec.clear_cache()
    backend = module.WanVAE.__new__(module.WanVAE)
    backend.model, backend.is_parallel, backend.benchmark = codec, False, False
    backend.dtype, backend.is_amp, backend.context = torch.float64, False, nullcontext()
    backend.scale = [torch.linspace(-.02, .03, 16, dtype=torch.float64),
                     torch.linspace(.8, 1.2, 16, dtype=torch.float64)]
    backend.img_mean = torch.linspace(-.1, .1, 16, dtype=torch.float64).reshape(1, 16, 1, 1, 1)
    backend.img_std = torch.linspace(.7, 1.1, 16, dtype=torch.float64).reshape(1, 16, 1, 1, 1)
    backend.video_mean = torch.linspace(-.1, .1, 384, dtype=torch.float64).reshape(1, 16, 24, 1, 1)
    backend.video_std = torch.linspace(.7, 1.1, 384, dtype=torch.float64).reshape(1, 16, 24, 1, 1)
    tokenizer = module.Wan2pt1VAEInterface.__new__(module.Wan2pt1VAEInterface)
    tokenizer.model = backend
    return tokenizer


class VAECalibration(unittest.TestCase):
    def test_source_exact_image_and_full93_hard_forward_without_caller_mutation(self):
        for frames in (1, 24):
            tokenizer = fixture()
            adapter = FunctionalWan21Decode(tokenizer, runtime=RUNTIME)
            latent = torch.linspace(-.3, .4, 16*frames*2*3, dtype=torch.float64).reshape(1, 16, frames, 2, 3)
            tokenizer.model.model._feat_map[0] = torch.ones(1, 16, 2, 2, 3)
            before = tree_digest(tokenizer.model.model._feat_map)
            observed = adapter.decode(latent.requires_grad_())
            self.assertEqual(tree_digest(tokenizer.model.model._feat_map), before)
            expected = fixture().decode(latent)
            self.assertFalse(expected.requires_grad)
            self.assertTrue(observed.requires_grad)
            self.assertTrue(torch.equal(observed, expected))
            METRICS['hard_forward_'+str(frames)] = dict(full_frames=observed.shape[2], bitwise_equal=True,
                caller_cache_unchanged=True, original_no_grad_reference=True, calibration_graph_retained=True)

    def test_last_frame_VJP_preserves_previous_latent_chunk_dependency(self):
        tokenizer = fixture()
        adapter = FunctionalWan21Decode(tokenizer, runtime=RUNTIME)
        latent = torch.linspace(-.3, .4, 16*24*2*3, dtype=torch.float64).reshape(1, 16, 24, 2, 3).requires_grad_()
        def loss(value):
            return adapter.decode(value)[:, :, -1].square().mean()
        gradient = torch.autograd.grad(loss(latent), latent)[0]
        direction = torch.zeros_like(latent);direction[:, :, -2] = .02
        predicted = float((gradient*direction).sum())
        epsilon = 1e-4
        with torch.no_grad():
            numerical = float((loss(latent+epsilon*direction)-loss(latent-epsilon*direction))/(2*epsilon))
        self.assertGreater(abs(predicted), 1e-5)
        self.assertAlmostEqual(predicted, numerical, delta=1e-8)
        METRICS['cross_chunk_last_frame_VJP'] = dict(predicted=predicted, central_FD=numerical,
            absolute_error=abs(predicted-numerical), epsilon=epsilon,
            previous_chunk_gradient_nonzero=True, actual_pretrained_weights=False)

    def test_unverified_parallel_benchmark_trainable_or_inference_modes_refused(self):
        for field in ('is_parallel', 'benchmark'):
            tokenizer = fixture();setattr(tokenizer.model, field, True)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'nonparallel'):
                FunctionalWan21Decode(tokenizer, runtime=RUNTIME)
        tokenizer = fixture();next(tokenizer.model.model.parameters()).requires_grad_()
        with self.assertRaisesRegex(ValueError, 'Frozen eval'):
            FunctionalWan21Decode(tokenizer, runtime=RUNTIME)
        tokenizer = fixture();adapter = FunctionalWan21Decode(tokenizer, runtime=RUNTIME)
        with torch.inference_mode(), self.assertRaisesRegex(ValueError, 'Non-inference'):
            adapter.decode(torch.ones(1, 16, 24, 2, 3))


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main()
