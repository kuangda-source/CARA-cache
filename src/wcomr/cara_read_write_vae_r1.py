"""Source-bound Wan2.1 calibration decode, preserving its temporal cache.

The production decoder is not patched. One verified no_grad decorator is
removed on a private wrapper; original normalization, casts, causal decoder
and cache-clear equations remain intact. Actual-weight parity, VJP and peak
memory still require a separately admitted real-model experiment.
"""
import ast
import copy
import inspect
from pathlib import Path
import sys
import types
from types import MappingProxyType

import torch

from .cfg_paired_probe_forward import _compile
from .cfg_paired_probe_production import _bindings, _origin


WAN_PATH = 'cosmos_predict2/_src/predict2/tokenizers/wan2pt1.py'
WAN_SHA256 = '885aaa3250f60f026b279f099dc08b2548d904604b839c57000c6c65a8d165bb'


class FunctionalWan21Decode:
    """Frozen, nonparallel complete-request decoder for the current backend.

All temporal feature-cache writes occur on a private top-level codec instance.
Weights and stateless child modules are shared. R1 requires no codec buffers;
an unverified stateful module cannot silently enter this calibration path.
"""
    def __init__(self, tokenizer, *, runtime):
        backend, codec = tokenizer.model, tokenizer.model.model
        if tuple(type(v).__name__ for v in (tokenizer, backend, codec)) != (
                'Wan2pt1VAEInterface', 'WanVAE', 'WanVAE_'):
            raise ValueError('Registered original Wan2.1 interface/wrapper/codec required')
        module = sys.modules[type(backend).__module__]
        _origin(module, runtime, WAN_PATH, WAN_SHA256)
        expected = (Path(runtime)/WAN_PATH).resolve()
        for value in (tokenizer, backend, codec):
            function = type(value).decode
            if (Path(inspect.getfile(type(value))).resolve() != expected
                    or getattr(value.decode, '__func__', None) is not function
                    or Path(inspect.unwrap(function).__code__.co_filename).resolve() != expected):
                raise ValueError('Original unwrapped decode identity/source differs')
        self.tokenizer, self.backend, self.codec = tokenizer, backend, codec
        self._ready()
        source = ast.parse(expected.read_bytes())
        owner = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'WanVAE')
        original = next(n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == 'decode')
        if [ast.unparse(n) for n in original.decorator_list] != ['torch.no_grad()']:
            raise ValueError('Exactly the pinned WanVAE no_grad decorator required')
        node = copy.deepcopy(original)
        node.decorator_list = []
        inverse = copy.deepcopy(node)
        inverse.decorator_list = copy.deepcopy(original.decorator_list)
        if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
            raise ValueError('Calibration decode altered the original body')
        self.decode_backend = _compile(node, vars(module), WAN_PATH+'#read-write-calibration')
        self.interface_decode = type(tokenizer).decode
        self.proof = MappingProxyType(dict(source_path=WAN_PATH, source_sha256=WAN_SHA256,
            removed_decorators=['WanVAE.decode: torch.no_grad()'], inverse_AST_equal=True,
            backend_globals=_bindings(self.decode_backend, vars(module), {}),
            original_interface_normalization_and_dtype=True, original_temporal_cache_retained=True,
            original_production_decoder_patched=False, actual_weights_or_memory_verified=False))

    def _ready(self):
        if (self.tokenizer.model is not self.backend or self.backend.model is not self.codec
                or self.backend.is_parallel or self.backend.benchmark
                or any(m.training for m in self.codec.modules())
                or any(p.requires_grad for p in self.codec.parameters())
                or any(True for _ in self.codec.buffers())):
            raise ValueError('Frozen eval nonparallel nonbenchmark buffer-free original codec required')

    def decode(self, latent):
        self._ready()
        if (torch.is_inference_mode_enabled() or not isinstance(latent, torch.Tensor)
                or latent.ndim != 5 or latent.shape[:2] != (1, 16)
                or latent.shape[2] not in (1, 24) or not latent.is_floating_point()
                or not bool(torch.isfinite(latent).all())):
            raise ValueError('Non-inference complete image/full93 finite Wan2.1 latent required')
        codec = copy.copy(self.codec)
        codec._modules = dict(self.codec._modules)
        codec._buffers = dict(self.codec._buffers)
        # Original decode clears its own _feat_map/_conv_idx at start and end.
        # Those assignments now belong to codec, not the deployed decoder.
        backend = copy.copy(self.backend)
        backend.model = codec
        backend.decode = types.MethodType(self.decode_backend, backend)
        tokenizer = copy.copy(self.tokenizer)
        tokenizer.model = backend
        value = self.interface_decode(tokenizer, latent)
        expected = (1, 3, (latent.shape[2]-1)*4+1, latent.shape[3]*8, latent.shape[4]*8)
        if value.shape != expected or not bool(torch.isfinite(value).all()):
            raise ValueError('Original complete Wan2.1 decoded video geometry/finiteness differs')
        return value
