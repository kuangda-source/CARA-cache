"""Pinned C/head/RF cut for immutable B1 readout controls.

Only the three original final-layer tensors are materialized. No deep forward,
conditioner, sampling, codec selection or deployment-memory claim is provided.
The CPU/GPU numerical control is an outcome, never a tolerance to tune.
"""
import ast
import hashlib
import math
from types import MethodType, ModuleType, SimpleNamespace
from typing import Optional

from einops import rearrange
import torch
from torch import amp, nn

from .cfg_paired_probe_forward import _compile, _function, WC_PATH, WC_SHA, RF_PATH
from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain
from .policy_interval_readout_r1 import ReadoutKernel
from .sq_q1_readout_r1 import source_from_anchors

DIT_PATH = 'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
DIT_SHA = 'a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'
CHECKPOINT_SHA = '565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47'
HEAD = {
    'linear.weight': ((64, 2048), '7c266057e634bfffa481fd48ba345b6ee212108ccb8f460b5cf57504232e0004'),
    'adaln_modulation.1.weight': ((256, 2048), 'aeff7bbfebf26969c1f1de535a02798d6237ea36cc27a97a3646e5f7167ca46c'),
    'adaln_modulation.2.weight': ((4096, 256), '5fabf73df79e695ceb1a9f55920b112759d98d5171c424907328029f3e29e0b7'),
}


def compile_head(runtime):
    """Compile the complete unchanged class and original unpatchify method."""
    raw = (runtime/DIT_PATH).read_bytes()
    if hashlib.sha256(raw).hexdigest() != DIT_SHA:
        raise ValueError('Pinned final-layer source changed')
    classes = [n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == 'FinalLayer']
    if len(classes) != 1:
        raise ValueError('One complete pinned FinalLayer required')
    namespace = dict(torch=torch, nn=nn, amp=amp, math=math, rearrange=rearrange, Optional=Optional)
    final_layer = _compile(classes[0], namespace, str(runtime/DIT_PATH)+'#whole-FinalLayer')
    unpatchify = _function(runtime, DIT_PATH, DIT_SHA, 'unpatchify')
    return final_layer, _compile(unpatchify, namespace, str(runtime/DIT_PATH)+'#unpatchify'), dict(
        source_sha256=DIT_SHA,
        entire_FinalLayer_AST_sha256=hashlib.sha256(ast.dump(classes[0], include_attributes=False).encode()).hexdigest(),
        unpatchify_AST_sha256=hashlib.sha256(ast.dump(unpatchify, include_attributes=False).encode()).hexdigest(),
        unchanged_whole_class=True, full_runtime_module_imported=False)


def load_head_weights(head, checkpoint):
    selected = {name.removeprefix('net.final_layer.'): value for name, value in checkpoint.items()
                if name.startswith('net.final_layer.')}
    if set(selected) != set(HEAD):
        raise ValueError('Exactly the three registered head weights required')
    metadata = {}
    for name, (shape, expected) in HEAD.items():
        value = selected[name]
        if not isinstance(value, torch.Tensor) or tuple(value.shape) != shape or value.dtype != torch.bfloat16:
            raise ValueError('Registered BF16 head shape/dtype differs: '+name)
        digest = hashlib.sha256(value.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
        if digest != expected:
            raise ValueError('Registered head tensor SHA differs: '+name)
        metadata[name] = dict(shape=list(shape), checkpoint_dtype=str(value.dtype), sha256=digest)
    head.load_state_dict(selected, strict=True)
    return metadata


class ReadoutOnlyNet(nn.Module):
    def forward(self, *args, **kwargs):
        raise RuntimeError('A deep/network forward is outside the saved readout cut')


def build_kernel(runtime, checkpoint, *, device='cpu'):
    final_layer, unpatchify, proof = compile_head(runtime)
    # Explicit standalone binding: FP32 parameters and embedding/adaln, BF16
    # saved hidden features, no outer autocast. The saved output equality gate
    # must establish compatibility with the original execution precision.
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        head = final_layer(2048, 2, 1, 16, use_adaln_lora=True,
                           adaln_lora_dim=256, use_wan_fp32_strategy=False).float().eval()
    metadata = load_head_weights(head, checkpoint)
    net = ReadoutOnlyNet()
    net.final_layer = head.to(device=device)
    net.patch_spatial, net.patch_temporal = 2, 1
    net.unpatchify = MethodType(unpatchify, net)
    net.worldcache_osi_enabled = True
    net.worldcache_flow_enabled = True
    net.worldcache_flow_scale = 2.
    net.eval()
    wc = ModuleType('sq_pinned_WC_cut'); wc.__file__ = str(runtime/WC_PATH)
    vars(wc).update(torch=torch, F=torch.nn.functional, rearrange=rearrange)
    for name in ('compute_optimal_gamma', 'estimate_optical_flow', 'warp_feature'):
        vars(wc)[name] = _compile(_function(runtime, WC_PATH, WC_SHA, name), vars(wc), str(runtime/WC_PATH))
    rf = ModuleType('sq_pinned_RF_cut'); rf.__file__ = str(runtime/RF_PATH)
    rf.torch = torch
    model = SimpleNamespace(net=net, sample_scheduler=SimpleNamespace(),
        tensor_kwargs={'device': device, 'dtype': torch.bfloat16},
        config=SimpleNamespace(conditional_frame_timestep=-1., denoise_replace_gt_frames=True))
    kernel = ReadoutKernel(model, runtime, wc, rf, warp=None)
    proof.update(head_tensors=metadata, parameter_dtype='torch.float32', outer_autocast=False,
                 head_parameter_bytes=sum(p.numel()*p.element_size() for p in net.parameters()),
                 WC=dict(kernel.proof), RF=dict(kernel.RF_proof), full_model_constructed=False)
    return kernel, proof


def compare_outputs(outputs, expected):
    if len(outputs) != 2 or len(expected) != 2:
        raise ValueError('Two complete branch outputs required')
    rows = []
    for value, target in zip(outputs, expected):
        if value.shape != target.shape or value.dtype != target.dtype or not torch.isfinite(value).all():
            raise ValueError('Saved output shape/dtype/finite control differs')
        difference = value.double()-target.double()
        rows.append(dict(exact=torch.equal(value, target), max_absolute=float(difference.abs().max()),
                         MSE=float(difference.square().mean()), dtype=str(value.dtype), shape=list(value.shape)))
    return dict(exact=all(r['exact'] for r in rows), branches=rows)


@torch.no_grad()
def original_controls(kernel, inputs, payload):
    """One original C pair plus one stored-D-hidden head pair, no codecs."""
    protected = plain((inputs, payload['teacher_hidden']))
    before = tree_digest(protected)
    rng = torch.get_rng_state().clone()
    versions = [(p, p._version) for p in kernel.net.parameters()]
    outputs = kernel.run('C', source=source_from_anchors(inputs['anchors']),
                         current=inputs['current'], pair_inputs=inputs['pair_inputs'])[0]
    C = compare_outputs(outputs, payload['readouts']['WC_C']['outputs'])
    noise, latent, timestep, conditions = inputs['pair_inputs']
    dense = []
    for branch in (0, 1):
        row = inputs['current'][branch]
        head = kernel.net.unpatchify(kernel.net.final_layer(payload['teacher_hidden'][branch],
            row['embedding'], adaln_lora_B_T_3D=row['adaln']))
        dense.append(kernel.to_velocity(kernel.model, noise, latent, timestep,
                     conditions[branch], _supplied_net_output=head))
    D = compare_outputs(dense, payload['teacher'])
    if tree_digest(protected) != before or not torch.equal(torch.get_rng_state(), rng):
        raise RuntimeError('Saved readout cut mutated original inputs or CPU RNG')
    if any(p._version != version for p, version in versions):
        raise RuntimeError('Saved readout cut mutated original head weights')
    return dict(original_C=C, stored_dense_hidden_head=D, original_controls_exact=C['exact'] and D['exact'],
                original_C_pairs=1, stored_dense_hidden_head_pairs=1, head_calls=4, deep_calls=0,
                codec_pairs=0, inputs_and_CPU_RNG_unchanged=True, weights_unchanged=True,
                complete_Q1_cohort=False, deployment_memory_measured=False)
