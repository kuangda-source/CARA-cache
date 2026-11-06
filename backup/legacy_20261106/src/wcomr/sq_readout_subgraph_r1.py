"""Pinned C/head/RF cut for immutable B1 readout controls.

Only the three original final-layer tensors are materialized. No deep forward,
conditioner, sampling, codec selection or deployment-memory claim is provided.
The CPU/GPU numerical control is an outcome, never a tolerance to tune.
"""
import ast
from contextlib import contextmanager
import hashlib
import math
from types import MethodType, ModuleType, SimpleNamespace
from typing import Optional

from einops import rearrange
import torch
from torch import amp, nn

from .cfg_paired_probe_forward import _compile, _function, WC_PATH, WC_SHA, RF_PATH
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain
from .policy_interval_readout_r1 import ReadoutKernel
from .sq_q1_readout_r1 import source_from_anchors

DIT_PATH = 'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
DIT_SHA = 'a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'
CHECKPOINT_SHA = '565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47'
BASE_CONFIG = 'cosmos_predict2/_src/predict2/configs/video2world/experiment/reason_embeddings/model_2B_reason_1p1_rectified_flow.py'
BASE_CONFIG_SHA = 'a8405ef1e46aedc7004026a51ce980a6a6509162738dfda34a10e83f3a19b32b'
SELECTED_CONFIG = 'cosmos_predict2/_src/predict2/configs/video2world/experiment/specialized_model/SFT_2B_RF.py'
SELECTED_CONFIG_SHA = '719fa25c90dcc4f51a9226fa1b5ac677c52cbb1c292c8eac1e3121ab3c3ce814'
BASE_NAME = 'T2V_REASON_EMBEDDINGS_V1P1_STAGE_C_PT_4_INDEX_26_SIZE_2B_RES_720_FPS16_RECTIFIED_FLOW'
SELECTED_NAME = 'STAGE_C_PT_4_INDEX_2_SIZE_2B_RES_720_FPS16_RECTIFIED_FLOW_WITH_EDM_CKPT'
LOADER_PATH = 'cosmos_predict2/_src/predict2/utils/model_loader.py'
LOADER_SHA = '34764531d719fd71c3db97db39ff1305121ada5a4534656ede5d9695718a79b6'
TRAINER_PATH = 'cosmos_predict2/_src/imaginaire/config.py'
TRAINER_SHA = '7ab54034ec40d4fffded33dcf70a4a076741fa08a72e360d41a760c37958b23d'
HEAD = {
    'linear.weight': ((64, 2048), '7c266057e634bfffa481fd48ba345b6ee212108ccb8f460b5cf57504232e0004'),
    'adaln_modulation.1.weight': ((256, 2048), 'aeff7bbfebf26969c1f1de535a02798d6237ea36cc27a97a3646e5f7167ca46c'),
    'adaln_modulation.2.weight': ((4096, 256), '5fabf73df79e695ceb1a9f55920b112759d98d5171c424907328029f3e29e0b7'),
}


def selected_settings(runtime):
    """Read the two pinned LazyDict declarations without importing training."""
    declarations = []
    for relative, digest, name in ((BASE_CONFIG, BASE_CONFIG_SHA, BASE_NAME),
                                   (SELECTED_CONFIG, SELECTED_CONFIG_SHA, SELECTED_NAME)):
        raw = (runtime/relative).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Selected 2B experiment source changed: '+relative)
        nodes = [n.value.args[0] for n in ast.parse(raw).body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
        if len(nodes) != 1:
            raise ValueError('One pinned selected 2B declaration required')
        declarations.append(nodes[0])
    def keyword(node, *path):
        for key in path:
            node = next(k.value for k in node.keywords if k.arg == key)
        return node
    base, selected = declarations
    if not any(isinstance(n, ast.Name) and n.id == BASE_NAME
               for n in ast.walk(keyword(selected, 'defaults'))):
        raise ValueError('Selected 2B experiment inheritance differs')
    strategy = ast.literal_eval(keyword(base, 'model', 'config', 'net', 'use_wan_fp32_strategy'))
    timestep = ast.literal_eval(keyword(selected, 'model', 'config', 'conditional_frame_timestep'))
    if strategy is not True or timestep != .1:
        raise ValueError('Selected original precision/conditioning configuration differs')
    return dict(use_wan_fp32_strategy=strategy, conditional_frame_timestep=timestep,
        selected_experiment='Stage-c_pt_4-Index-2-Size-2B-Res-720-Fps-16-Note-rf_with_edm_ckpt',
        source_sha256={BASE_CONFIG:BASE_CONFIG_SHA, SELECTED_CONFIG:SELECTED_CONFIG_SHA},
        full_config_module_imported=False)


@contextmanager
def original_backend_policy(runtime):
    """Bind the original loader's TF32 and default trainer cuDNN flags.

    The selected 2B declarations contain no cuDNN overrides. These flags are
    part of the original execution binding, not knobs for fitting parity.
    CUDA initialization and hardware admission remain the runner's job.
    """
    for relative, expected in ((LOADER_PATH, LOADER_SHA), (TRAINER_PATH, TRAINER_SHA)):
        if hashlib.sha256((runtime/relative).read_bytes()).hexdigest() != expected:
            raise ValueError('Pinned backend configuration source changed: '+relative)
    loader = ast.parse((runtime/LOADER_PATH).read_bytes())
    assignment = 'torch.backends.cudnn.allow_tf32 = torch.backends.cuda.matmul.allow_tf32 = True'
    if sum(isinstance(n, ast.Assign) and ast.unparse(n)==assignment for n in ast.walk(loader)) != 1:
        raise ValueError('Original TF32 loader assignment differs')
    trainer = ast.parse((runtime/TRAINER_PATH).read_bytes())
    config = next(n for n in trainer.body if isinstance(n, ast.ClassDef) and n.name=='CuDNNConfig')
    defaults = {n.target.id:ast.literal_eval(n.value) for n in config.body if isinstance(n, ast.AnnAssign)}
    if defaults['benchmark'] is not True or defaults['deterministic'] is not False:
        raise ValueError('Original trainer cuDNN defaults differ')
    before = backend_flags()
    precision = torch.get_float32_matmul_precision()
    warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.use_deterministic_algorithms(False)
        with torch.backends.cudnn.flags(enabled=True, benchmark=True, deterministic=False, allow_tf32=True):
            yield dict(flags=backend_flags(), float32_matmul_precision=torch.get_float32_matmul_precision(),
                       source_sha256={LOADER_PATH:LOADER_SHA, TRAINER_PATH:TRAINER_SHA},
                       original_loader_assignment_verified=True)
    finally:
        torch.backends.cuda.matmul.allow_tf32 = before['matmul_allow_tf32']
        torch.set_float32_matmul_precision(precision)
        torch.use_deterministic_algorithms(before['deterministic_algorithms'],warn_only=warn_only)
        if backend_flags() != before:
            raise RuntimeError('Readout backend policy leaked outside its scope')


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
    settings = selected_settings(runtime)
    # Explicit standalone binding: FP32 parameters and embedding/adaln, BF16
    # saved hidden features, no outer autocast. The saved output equality gate
    # must establish compatibility with the original execution precision.
    with torch.random.fork_rng(devices=[]), torch.device('cpu'):
        head = final_layer(2048, 2, 1, 16, use_adaln_lora=True,
                           adaln_lora_dim=256,
                           use_wan_fp32_strategy=settings['use_wan_fp32_strategy']).float().eval()
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
        config=SimpleNamespace(conditional_frame_timestep=settings['conditional_frame_timestep'],
                               denoise_replace_gt_frames=True))
    kernel = ReadoutKernel(model, runtime, wc, rf, warp=None)
    proof.update(head_tensors=metadata, parameter_dtype='torch.float32', outer_autocast=False,
                 selected_experiment_settings=settings,
                 head_parameter_bytes=sum(p.numel()*p.element_size() for p in net.parameters()),
                 WC=dict(kernel.proof), RF=dict(kernel.RF_proof), full_model_constructed=False)
    return kernel, proof


def compare_outputs(outputs, expected):
    if len(outputs) != 2 or len(expected) != 2:
        raise ValueError('Two complete branch outputs required')
    rows = []
    for value, target in zip(outputs, expected):
        value, target = value.detach().cpu(), target.detach().cpu()
        if value.shape != target.shape or value.dtype != target.dtype or not torch.isfinite(value).all():
            raise ValueError('Saved output shape/dtype/finite control differs')
        difference = value.double()-target.double()
        rows.append(dict(exact=torch.equal(value, target), max_absolute=float(difference.abs().max()),
                         MSE=float(difference.square().mean()), dtype=str(value.dtype), shape=list(value.shape)))
    return dict(exact=all(r['exact'] for r in rows), branches=rows)


@torch.no_grad()
def dense_hidden_outputs(kernel, inputs, teacher_hidden):
    """Only the original head/RF on stored teacher hidden, never deep blocks."""
    noise, latent, timestep, conditions = inputs['pair_inputs']
    outputs = []
    for branch in (0, 1):
        row = inputs['current'][branch]
        hidden = teacher_hidden[branch].to(device=row['embedding'].device)
        head = kernel.net.unpatchify(kernel.net.final_layer(hidden,
            row['embedding'], adaln_lora_B_T_3D=row['adaln']))
        outputs.append(kernel.to_velocity(kernel.model, noise, latent, timestep,
                       conditions[branch], _supplied_net_output=head))
    return tuple(outputs)


@torch.no_grad()
def original_controls(kernel, inputs, payload):
    """One original C pair plus one stored-D-hidden head pair, no codecs."""
    protected = plain((inputs, payload['teacher_hidden']))
    before = tree_digest(protected)
    snapshot = CompleteStateRoundtrip(kernel.net, kernel.model.sample_scheduler, inputs['pair_inputs'][1])
    state_before = snapshot.fingerprint()
    versions = [(p, p._version) for p in kernel.net.parameters()]
    try:
        outputs = kernel.run('C', source=source_from_anchors(inputs['anchors']),
                             current=inputs['current'], pair_inputs=inputs['pair_inputs'])[0]
        C = compare_outputs(outputs, payload['readouts']['WC_C']['outputs'])
        D = compare_outputs(dense_hidden_outputs(kernel, inputs, payload['teacher_hidden']), payload['teacher'])
    finally:
        snapshot.restore()
        if tree_digest(protected) != before or snapshot.fingerprint() != state_before:
            raise RuntimeError('Saved readout cut mutated original inputs or protected state')
        if any(p._version != version for p, version in versions):
            raise RuntimeError('Saved readout cut mutated original head weights')
    return dict(original_C=C, stored_dense_hidden_head=D, original_controls_exact=C['exact'] and D['exact'],
                original_C_pairs=1, stored_dense_hidden_head_pairs=1, head_calls=4, deep_calls=0,
                codec_pairs=0, inputs_and_CPU_RNG_unchanged=True, all_RNG_and_buffers_restored=True,
                weights_unchanged=True,
                complete_Q1_cohort=False, deployment_memory_measured=False)
