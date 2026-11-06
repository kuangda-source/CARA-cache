"""Sparse same-call deep truth for W1 diagnostics; not enabled in F1.

Executes the remaining block stack directly, never a second cache forward.
Real-model output parity, CUDA cost and memory are still required before use.
"""
import inspect
import time
import torch
from . import integration
from .shadow_metrics import score_shadow_pair


class ShadowProbe:
    def __init__(self, calls):
        if not calls or any(type(c) is not int or c < 1 for c in calls):
            raise ValueError('Supply positive one-based calls')
        self.calls = frozenset(calls)
        self.request = None
        self.records = []

    def begin_request(self, identity):
        if identity is None:
            raise ValueError('Explicit request identity required')
        self.request, self.call = identity, 0
        self.records = []

    def start_call(self):
        if self.request is None:
            raise RuntimeError('begin_request must precede diagnostic forward')
        self.call += 1

    @torch.no_grad()
    def collect(self, net, *, skipped, branch, probe, original_input,
                predicted_hidden, predicted_velocity, block_kwargs, embedding, adaln):
        if not skipped or self.call not in self.calls:
            return
        if net.training or any(module.training for module in net.modules()):
            raise RuntimeError('Shadow diagnostics require eval mode')
        if getattr(net, '_w1_shadow_active', False):
            raise RuntimeError('Nested shadow execution')
        device = probe.device
        devices = [device.index if device.index is not None else torch.cuda.current_device()] if device.type == 'cuda' else []
        sync = (lambda: torch.cuda.synchronize(device)) if devices else (lambda: None)
        # Preserve registered state if an inference block happens to update it.
        buffers = [(buf, buf.detach().clone()) for buf in net.buffers()]
        sync(); start = time.perf_counter()
        try:
            net._w1_shadow_active = True
            with torch.random.fork_rng(devices=devices):
                truth = probe.detach().clone()
                for block in net.blocks[net.probe_depth:]:
                    truth = block(truth, **block_kwargs)
                truth_velocity = net.unpatchify(net.final_layer(truth, embedding, adaln_lora_B_T_3D=adaln))
                metrics = score_shadow_pair(residual_prediction=predicted_hidden-original_input,
                    residual_truth=truth-original_input, velocity_prediction=predicted_velocity,
                    velocity_truth=truth_velocity)
            sync()
            self.records.append({'request': self.request, 'call': self.call,
                'cache_counter': net.cnt, 'cfg_branch': branch,
                'shadow_deep_blocks': len(net.blocks)-net.probe_depth,
                'diagnostic_seconds': time.perf_counter()-start, 'metrics': metrics})
        finally:
            for buf, saved in buffers:
                buf.copy_(saved)
            net._w1_shadow_active = False


def build_shadow_forward(original, mode, diagnostic):
    """Version hash must be checked by caller before installation, as in W1 install."""
    if mode not in {'official', 'scalar', 'shrink'}:
        raise ValueError(mode)
    source = inspect.getsource(original)
    if mode != 'official':
        source = integration.inject_source(source)
    anchor = '    # Increment Step Counter'
    if source.count(anchor) != 1:
        raise RuntimeError('Unsupported shadow injection anchor')
    inserted = '''    _shadow_collect(self, skipped=skip_forward, branch=current_idx,
        probe=test_x if skip_forward else None, original_input=ori_x,
        predicted_hidden=x_B_T_H_W_D, predicted_velocity=x_B_C_Tt_Hp_Wp,
        block_kwargs=block_kwargs, embedding=t_embedding_B_T_D, adaln=adaln_lora_B_T_3D)

'''
    source = source.replace(anchor, inserted + anchor)
    namespace = dict(original.__globals__)
    namespace.update(_w1_begin=integration._begin, _w1_predict=integration._predict,
                     _w1_observe=integration._observe, _shadow_collect=diagnostic.collect)
    exec(compile(source, '<w1-same-state-shadow>', 'exec'), namespace)
    result = namespace[original.__name__]

    def forward(net, *args, **kwargs):
        diagnostic.start_call()
        net._w1_mode = mode
        return result(net, *args, **kwargs)
    return forward


def install(mode, root, diagnostic):
    """Install only against the pinned module; caller still owns request boundaries."""
    import hashlib
    import json
    from pathlib import Path
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    lock = json.loads((Path(root) / 'manifests/upstream.json').read_text())
    path = Path(inspect.getfile(wc))
    if hashlib.sha256(path.read_bytes()).hexdigest() != lock['cache_module_sha256']:
        raise RuntimeError('Shadow cache module differs from pinned source')
    wc.worldcache_mini_train_dit_forward = build_shadow_forward(
        wc.worldcache_mini_train_dit_forward, mode, diagnostic)
