"""Pinned complete Cosmos Blocks, tiny declared CPU attention, all nine arms.

Checks own-state propagation, actual GEMM row counts, strictly past mixed
history, current identity, both CFG slots, rollback and transparent observers.
This is a CPU implementation test, not a GPU/video performance result.
"""
import ast
import copy
from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path
from typing import Optional
import types

import torch
from einops import rearrange

from wcomr.block_probe_r1 import ProbeHistory, BlockProbeArm, MODES
from wcomr.partial_mlp import PartialMLP, block_indices


SOURCE_SHA = 'a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'


def run(runtime):
    source = Path(runtime) / 'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    classes = [n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef)
               and n.name in ('GPT2FeedForward', 'Block')]
    assert len(classes) == 2

    class TinyAttention(torch.nn.Module):
        def __init__(self, *args, **kwargs):
            super().__init__(); self.calls = 0

        def forward(self, x, context=None, **kwargs):
            self.calls += 1
            # Nonlinear in current rows so stale absolute hidden cannot pass.
            return torch.sin(x) * .07 + (0 if context is None else context.mean() * .03)

        def init_weights(self):
            pass

    @dataclass
    class VideoSize:
        T: int
        H: int
        W: int

    ns = dict(torch=torch, nn=torch.nn, math=math, Optional=Optional,
              amp=torch.amp, rearrange=rearrange, Attention=TinyAttention,
              I2VCrossAttention=TinyAttention, VideoSize=VideoSize)
    exec(compile(ast.fix_missing_locations(ast.Module(body=classes, type_ignores=[])),
                 str(source) + '#isolated-B-CPU', 'exec'), ns)
    torch.manual_seed(823); torch.set_num_threads(2)
    layers = tuple(range(8)); p0_layers = (0, 2, 4, 6); l2_layers = (3, 5)
    blocks = torch.nn.ModuleList([ns['Block'](8, 8, 2, mlp_ratio=4,
        use_adaln_lora=bool(i % 2), adaln_lora_dim=4,
        backend='declared_tiny_CPU_attention') for i in layers]).eval()
    plain = copy.deepcopy(blocks).eval()
    owner = PartialMLP(blocks, p0_layers).install()
    reference_owner = PartialMLP(plain, p0_layers).install()
    history = ProbeHistory(blocks, mlp_layers=layers, residual_layers=l2_layers,
                           projection_owner=owner).install()
    context = ('B_CPU', 'pinned_complete_blocks', 'fixed_prompt_seed')
    shape = (1, 2, 2, 4, 8); tokens = math.prod(shape[:-1])
    rng = torch.random.get_rng_state().clone()
    parameters = [(p, p._version, p.clone()) for p in blocks.parameters()]
    parent_checks = []; checks = []; refusals = []

    def initial(step, slot):
        return torch.arange(math.prod(shape), dtype=torch.float32).reshape(shape) / 99 + step * .031 + slot * .21

    def kwargs(block, step, slot):
        emb = torch.arange(16, dtype=torch.float32).reshape(1, 2, 8) / 31 + step * .013
        return dict(emb_B_T_D=emb, crossattn_emb=torch.ones(1, 3, 8) * (slot + 1),
            adaln_lora_B_T_3D=(torch.linspace(-.3, .4, 48).reshape(1, 2, 24) * (.6 + slot)
                              if block.use_adaln_lora else None),
            extra_per_block_pos_emb=torch.full(shape, .005))

    def group(which, step, slot, *, override=None):
        x = initial(step, slot)
        for layer, block in enumerate(which):
            x = override(layer, block, x) if override else block(x, **kwargs(block, step, slot))
        return x

    def bank_signature():
        return {'mlp': {str(k): (hashlib.sha256(c.value.numpy().tobytes()).hexdigest(),
                 c.updated_at.tolist(), c.source.tolist(), c.last_actual_D) for k, c in history.mlp.items()},
            'residual': {str(k): (hashlib.sha256(c.value.numpy().tobytes()).hexdigest(),
                 c.born, c.source_kind, c.last_actual_D) for k, c in history.residual.items()},
            'step': history.last_step, 'records': copy.deepcopy(history.records)}

    def rejected(label, operation):
        try:
            operation()
        except ValueError:
            refusals.append(label)
        else:
            raise AssertionError('Expected refusal: ' + label)

    try:
        with torch.no_grad():
            # Natural D then actual P: P0 layers contain mixed token ages;
            # extra M8 layers really ran dense MLP on the actual P parent.
            for step, action in ((1, 'D'), (2, 'P')):
                ids = None if action == 'D' else block_indices(tokens, .5, block_size=4, opportunity=0)
                actual = []; expected = []
                with owner.pair(step=step, action=action, context=context, indices=ids):
                    with history.pair(step=step, action=action, context=context):
                        for slot in (0, 1):
                            with owner.branch(slot), history.branch(slot):
                                actual.append(group(blocks, step, slot))
                with reference_owner.pair(step=step, action=action, context=context, indices=ids):
                    for slot in (0, 1):
                        with reference_owner.branch(slot):
                            expected.append(group(plain, step, slot))
                assert all(torch.equal(a, b) for a, b in zip(actual, expected))
                parent_checks.append(dict(step=step, action=action, observer_bitwise_transparent=True))
            assert all(set(c.updated_at.tolist()) == {1, 2} for (l, s), c in history.mlp.items() if l in p0_layers)
            assert all(set(c.updated_at.tolist()) == {2} for (l, s), c in history.mlp.items() if l not in p0_layers)
            assert all(c.born == 2 and c.source_kind == 'P' and c.last_actual_D == 1
                       for c in history.residual.values())
            snapshot = history.snapshot(); before = bank_signature()
            dense = []
            with reference_owner.readonly():
                dense = [group(plain, 3, s) for s in (0, 1)]
            for mode in MODES:
                arm = BlockProbeArm(blocks, history, mode, p0_layers=p0_layers,
                    m8_layers=layers, residual_layers=l2_layers).install()
                ids = (block_indices(tokens, .5, block_size=4, opportunity=1,
                       random_seed=793 if mode.endswith('RANDOM') else None)
                       if mode.startswith(('P0_', 'M8_')) else None)
                linear_rows = []; handles = []
                for layer, block in enumerate(blocks):
                    for name in ('layer1', 'layer2'):
                        def count(module, args, layer=layer, name=name):
                            linear_rows.append((layer, name, math.prod(args[0].shape[:-1])))
                        handles.append(getattr(block.mlp, name).register_forward_pre_hook(count))
                attention_before = [(b.self_attn.calls, b.cross_attn.calls) for b in blocks]
                values = []
                try:
                    with owner.readonly(), history.readonly():
                        with arm.pair(step=3, context=context, indices=ids):
                            for slot in (0, 1):
                                with arm.branch(slot):
                                    values.append(group(blocks, 3, slot))
                    # Independent reference deliberately computes full selected
                    # MLPs then blends outputs. Actual arm must pass row counts.
                    expected = []
                    affected = p0_layers if mode.startswith('P0_') else layers
                    for slot in (0, 1):
                        temporary = []
                        if ids is not None:
                            for layer in affected:
                                def blend(module, args, value, layer=layer, slot=slot):
                                    old = history.mlp[(layer, slot)].value.reshape(tokens, shape[-1])
                                    mask = torch.zeros(tokens, dtype=torch.bool); mask[ids] = True
                                    return torch.where(mask[:, None], value.reshape(tokens, shape[-1]), old).reshape(shape)
                                temporary.append(plain[layer].mlp.register_forward_hook(blend))
                        try:
                            def block_reference(layer, block, x):
                                if mode == 'L2' and layer in l2_layers:
                                    return x + history.residual[(layer, slot)].value
                                return block(x, **kwargs(block, 3, slot))
                            with reference_owner.readonly():
                                expected.append(group(plain, 3, slot, override=block_reference))
                        finally:
                            for h in temporary:
                                h.remove()
                    for value, exp in zip(values, expected):
                        torch.testing.assert_close(value, exp, rtol=1e-5, atol=2e-6)
                    if mode.startswith('DENSE_'):
                        assert all(torch.equal(a, b) for a, b in zip(values, dense))
                    counts = {(l, name): [] for l in layers for name in ('layer1', 'layer2')}
                    for l, name, n in linear_rows:
                        counts[(l, name)].append(n)
                    for l in layers:
                        want = [] if mode == 'L2' and l in l2_layers else [
                            len(ids) if ids is not None and l in affected else tokens] * 2
                        assert counts[(l, 'layer1')] == counts[(l, 'layer2')] == want
                    for l, (b, (sa, ca)) in enumerate(zip(blocks, attention_before)):
                        calls = 0 if mode == 'L2' and l in l2_layers else 2
                        assert b.self_attn.calls - sa == b.cross_attn.calls - ca == calls
                    assert bank_signature() == before
                    assert all(c.last_actual_D == 1 for c in owner.cache.values())
                    checks.append(dict(mode=mode, own_intermediate_full_stack_reference=True,
                        both_CFG_slots=True, real_Linear_rows_verified=True,
                        real_attention_calls_verified=True, parent_history_unchanged=True,
                        receipt=arm.receipt()))
                    # Replay reset restores precisely the same old sources.
                    arm.reset_from_history()
                    with owner.readonly(), history.readonly(), arm.pair(step=3, context=context, indices=ids):
                        for slot in (0, 1):
                            with arm.branch(slot):
                                assert torch.equal(group(blocks, 3, slot), values[slot])
                finally:
                    for h in handles:
                        h.remove()
                    arm.close()
            # Arm-level refusal of future/stale-context sources and rollback.
            def try_l2():
                arm = BlockProbeArm(blocks, history, 'L2', p0_layers=p0_layers,
                    m8_layers=layers, residual_layers=l2_layers).install()
                try:
                    with owner.readonly(), history.readonly(), arm.pair(step=3, context=context):
                        for slot in (0, 1):
                            with arm.branch(slot):
                                group(blocks, 3, slot)
                finally:
                    arm.close()
            history.residual[(3, 0)] = replace(history.residual[(3, 0)], born=3)
            rejected('current_teacher_cannot_be_history', try_l2)
            history.restore(snapshot)
            history.residual[(3, 0)] = replace(history.residual[(3, 0)], context=('wrong', 'context', 'id'))
            rejected('different_context_history', try_l2)
            history.restore(snapshot)
            del history.residual[(3, 0)]
            rejected('missing_history_no_dense_fill', try_l2)
            history.restore(snapshot)
            def try_m8():
                arm = BlockProbeArm(blocks, history, 'M8_ROTATION', p0_layers=p0_layers,
                    m8_layers=layers, residual_layers=l2_layers).install()
                try:
                    with owner.readonly(), history.readonly(), arm.pair(
                            step=3, context=context, indices=torch.arange(tokens // 2)):
                        for slot in (0, 1):
                            with arm.branch(slot):
                                group(blocks, 3, slot)
                finally:
                    arm.close()
            history.mlp[(1, 0)] = replace(history.mlp[(1, 0)],
                updated_at=torch.full_like(history.mlp[(1, 0)].updated_at, 3))
            rejected('MLP_current_teacher_cannot_be_history', try_m8)
            history.restore(snapshot)
            del history.mlp[(1, 0)]
            rejected('MLP_missing_history_no_dense_fill', try_m8)
            history.restore(snapshot)
            arm = BlockProbeArm(blocks, history, 'L2', p0_layers=p0_layers,
                m8_layers=layers, residual_layers=l2_layers).install()
            try:
                try:
                    with owner.readonly(), history.readonly(), arm.pair(step=3, context=context):
                        with arm.branch(0):
                            group(blocks, 3, 0)
                        raise RuntimeError('Injected second-branch failure')
                except RuntimeError:
                    pass
                assert arm.poisoned and bank_signature() == before
                arm.reset_from_history()
                assert not arm.poisoned
            finally:
                arm.close()
            assert bank_signature() == before
            inference_checks = []
            with torch.inference_mode():
                assert torch.is_inference(initial(4, 0))
                with owner.pair(step=4, action='D', context=context):
                    with history.pair(step=4, action='D', context=context):
                        for slot in (0, 1):
                            with owner.branch(slot), history.branch(slot):
                                group(blocks, 4, slot)
                assert all(torch.is_inference(c.value) for c in history.residual.values())
                for mode in ('DENSE_L2_STATE', 'L2', 'M8_ROTATION'):
                    arm = BlockProbeArm(blocks, history, mode, p0_layers=p0_layers,
                        m8_layers=layers, residual_layers=l2_layers).install()
                    try:
                        ids = torch.arange(tokens // 2) if mode == 'M8_ROTATION' else None
                        with owner.readonly(), history.readonly(), arm.pair(step=5, context=context, indices=ids):
                            for slot in (0, 1):
                                with arm.branch(slot):
                                    value = group(blocks, 5, slot)
                                    assert torch.is_inference(value) and torch.isfinite(value).all()
                        inference_checks.append(mode)
                    finally:
                        arm.close()
            # Ordinary tensors still reject input mutation. The intentionally
            # faulty layer is isolated to this extra observer, then restored.
            faulty_history = ProbeHistory(blocks, mlp_layers=layers, residual_layers=l2_layers).install()
            faulty_block = blocks[l2_layers[0]]
            had_forward, old_attribute = 'forward' in vars(faulty_block), vars(faulty_block).get('forward')
            original_forward = faulty_block.forward
            def inplace_input(module, x, **kw):
                value = original_forward(x, **kw)
                x.add_(.01)
                return value
            faulty_block.forward = types.MethodType(inplace_input, faulty_block)
            try:
                try:
                    with owner.readonly(), faulty_history.pair(step=1, action='D', context=context):
                        with faulty_history.branch(0):
                            group(blocks, 6, 0)
                except ValueError as error:
                    assert 'identity mutated' in str(error)
                else:
                    raise AssertionError('Normal tensor input mutation was accepted')
                assert faulty_history.poisoned and not faulty_history.mlp and not faulty_history.residual
                refusals.append('normal_tensor_inplace_identity_mutation')
            finally:
                if had_forward:
                    faulty_block.forward = old_attribute
                else:
                    delattr(faulty_block, 'forward')
                faulty_history.close()
            assert torch.equal(torch.random.get_rng_state(), rng)
            assert all(p is old and p._version == version and torch.equal(p, value)
                       for p, (old, version, value) in zip(blocks.parameters(), parameters))
            return dict(status='BLOCK_PROBE_PINNED_COMPLETE_BLOCK_CPU_PASS_NOT_GPU',
                pinned_source_sha256=SOURCE_SHA, parent_checks=parent_checks,
                modes=checks, refusals=refusals, rollback_verified=True,
                inference_mode_parent_and_arms_verified=inference_checks,
                global_RNG_and_parameters_preserved=True,
                separate_D_stateful_controls=True, no_Q2_execution_or_speed_claim=True)
    finally:
        history.close(); owner.close(); reference_owner.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', required=True)
    parser.add_argument('--out')
    args = parser.parse_args()
    result = run(args.runtime)
    encoded = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(encoded + '\n')
    print(encoded)
