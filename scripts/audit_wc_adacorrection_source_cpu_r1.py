#!/usr/bin/env python3
"""Characterize reviewed author methods on CPU; never instantiate the upstream CUDA wrapper."""
import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import torch

REVISION = 'cc468521527ab2c3610ede8ee0315b469c0570f5'
RELATIVE = 'xfuser/model_executor/cache/utils.py'
SELECTED = {
    'CachedTransformerBlocks': ('forward',),
    'FastCachedTransformerBlocks': (
        'compute_adacorr_offset_score', 'blend_with_adacorrection',
        'get_modulated_inputs', 'compute_motion_saliency', 'get_start_idx',
        'get_adaptive_threshold', 'are_two_tensor_similar',
        'process_blocks', 'process_transformer_blocks',
        'spectral_error_feedback_residual',
    ),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_reviewed_methods(source, expected):
    assert sha(source) == expected
    tree = ast.parse(source.read_text())
    methods, bindings = [], []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name not in SELECTED:
            continue
        for fn in node.body:
            if isinstance(fn, ast.FunctionDef) and fn.name in SELECTED[node.name]:
                assert not fn.decorator_list
                methods.append(copy.deepcopy(fn))
                bindings.append(dict(owner=node.name, method=fn.name,
                                     first_line=fn.lineno, last_line=fn.end_lineno))
    assert len(methods) == sum(len(v) for v in SELECTED.values())
    module = ast.Module(body=methods, type_ignores=[])
    ast.fix_missing_locations(module)
    env = dict(torch=torch, math=math)
    exec(compile(module, str(source), 'exec'), env)
    cls = type('ReviewedAuthorMethodsCPUOnly', (), {fn.name: env[fn.name] for fn in methods})
    return cls, bindings


class CountingBlock:
    def __init__(self):
        self.calls = 0

    def __call__(self, hidden, encoder, *args, **kwargs):
        self.calls += 1
        return hidden + 0.125, encoder + 0.25


def owner(cls, *, blocks=3, gamma=1.0):
    obj = cls()
    obj.adacorr_lambda, obj.adacorr_gamma = 1.0, gamma
    obj.enable_adacorrection = True
    obj.enable_freq_error_feedback = obj.enable_token_merge = False
    obj.enable_enhanced_linear_approx = False
    obj.return_hidden_states_first = True
    obj.transformer_blocks = [CountingBlock() for _ in range(blocks)]
    # The learned projections are not released/loaded by this audit. Identity
    # stand-ins isolate control flow; they cannot establish feature quality.
    obj.block_projections = [torch.nn.Identity() for _ in range(blocks)]
    obj.single_transformer_blocks = None
    obj.cache_context = SimpleNamespace(
        prev_hidden_states=None, static_token_mask=None,
        hidden_states_residual=None, encoder_hidden_states_residual=None,
        original_hidden_states=None, original_encoder_hidden_states=None,
    )
    obj.callback_handler = SimpleNamespace(trigger_event=lambda *args: None)
    obj.cnt = torch.tensor(0.0)
    obj.total_steps = torch.tensor(0)
    obj.cache_hits = torch.tensor(0)
    obj.rel_l1_thresh = torch.tensor(0.05)
    obj.motion_threshold = 0.1
    obj.beta0, obj.beta1, obj.beta2, obj.beta3 = 0.01, 0.5, -0.002, 0.00005
    obj.z_score = 1.96
    return obj


def characterize(source, expected):
    cls, methods = load_reviewed_methods(source, expected)
    guard = mock.patch.object(torch.Tensor, 'cuda', side_effect=AssertionError('CPU audit requested CUDA'))
    with guard, torch.inference_mode():
        core = owner(cls)
        h = torch.tensor([[[0.01, 0.02, 0.04, 0.08]]], dtype=torch.float64)
        old = torch.zeros_like(h)
        actual = core.compute_adacorr_offset_score(h, old)
        temporal = torch.linalg.vector_norm(h - old, dim=-1).mean()
        dispersion = h.std(dim=-1, unbiased=False).clamp_min(1e-6).mean()
        expected_code = temporal.square() + dispersion
        torch.testing.assert_close(actual, expected_code, rtol=1e-12, atol=1e-12)
        paper_v3_unsquared = temporal + dispersion
        assert not torch.isclose(actual, paper_v3_unsquared)
        assert core.compute_adacorr_offset_score(h, None).item() == 0
        blends = []
        for score, weight in ((-1.0, 0.0), (0.25, 0.25), (2.0, 1.0)):
            out = core.blend_with_adacorrection(torch.ones_like(h), 3 * torch.ones_like(h), torch.tensor(score))
            torch.testing.assert_close(out, (1 + 2 * weight) * torch.ones_like(h))
            blends.append(dict(score=score, expected_weight=weight, output_mean=out.mean().item()))

        paths = []
        for gamma, value in ((0.0, 0.35), (1.0, math.sqrt(0.5 / 4)), (1.0, 0.75)):
            probe = owner(cls, gamma=gamma)
            hidden = torch.full((1, 3, 4), value)
            encoder = torch.ones_like(hidden)
            probe.cache_context.prev_hidden_states = torch.zeros_like(hidden)
            weights = []
            original = probe.compute_adacorr_offset_score

            def observed(current, previous):
                score = original(current, previous)
                weights.append(float(torch.clamp(gamma * score, 0, 1)))
                return score

            probe.compute_adacorr_offset_score = observed
            probe.process_transformer_blocks(0, hidden, encoder)
            counts = [b.calls for b in probe.transformer_blocks]
            assert counts == [1, 1, 1] and len(weights) == 3
            paths.append(dict(gamma=gamma, first_weight=weights[0], all_weights=weights,
                              dense_block_calls=counts, fresh_computation_skipped_by_weight=False))

        first = owner(cls)
        hidden = torch.full((1, 3, 4), 0.1)
        encoder = torch.full_like(hidden, 0.2)
        first.forward(hidden, encoder)
        assert first.cache_context.hidden_states_residual is None
        assert first.cache_context.encoder_hidden_states_residual is None
        before = [b.calls for b in first.transformer_blocks]
        try:
            first.forward(hidden.clone(), encoder.clone())
        except TypeError as error:
            reuse_error = dict(type=type(error).__name__, message=str(error))
        else:
            raise AssertionError('Expected original uninitialized residual failure was not reproduced')
        assert first.use_cache.item() is True
        assert [b.calls for b in first.transformer_blocks] == before

        # The separate cache-hit control starts with explicitly supplied valid
        # residuals. This is a fixture, not a silent upstream implementation fix.
        cache_hit = owner(cls)
        cache_hit.cache_context.prev_hidden_states = hidden.clone()
        cache_hit.cache_context.hidden_states_residual = torch.full_like(hidden, 0.3)
        cache_hit.cache_context.encoder_hidden_states_residual = torch.full_like(encoder, 0.4)
        correction_calls = []
        score_impl = cache_hit.compute_adacorr_offset_score

        def record_score(*args):
            correction_calls.append(1)
            return score_impl(*args)

        cache_hit.compute_adacorr_offset_score = record_score
        returned, returned_encoder = cache_hit.forward(hidden, encoder)
        torch.testing.assert_close(returned, hidden + 0.3)
        torch.testing.assert_close(returned_encoder, encoder + 0.4)
        assert cache_hit.use_cache.item() is True and not correction_calls
        assert [b.calls for b in cache_hit.transformer_blocks] == [0, 0, 0]

    assert not torch.cuda.is_initialized()
    return dict(
        status='ADACORRECTION_PINNED_AUTHOR_METHOD_CPU_CHARACTERIZATION_NOT_COSMOS_ADAPTER',
        revision=REVISION, source_file=RELATIVE, source_sha256=expected, method_bindings=methods,
        kernel_arithmetic=dict(code_squared_temporal_score=actual.item(),
                              paper_v3_unsquared_score=paper_v3_unsquared.item(),
                              version_difference_observed=True, clipped_blend_controls=blends),
        blend_path_cost_controls=paths,
        ordinary_forward_reuse=dict(first_call_dense_block_calls=before,
                                   residual_buffers_initialized_by_first_call=False,
                                   second_identical_call_use_cache=True, original_failure=reuse_error),
        valid_residual_cache_hit_fixture=dict(dense_block_calls=0, correction_score_calls=0,
                                             fixture_residuals_injected=True),
        boundaries=dict(full_upstream_constructor_imported=False, full_upstream_pipeline_executed=False,
                        projections='IDENTITY_CPU_FIXTURE_NOT_PRETRAINED_WEIGHTS',
                        CPU_shapes=[1, 3, 4], Cosmos_adapter_implemented=False,
                        spectral_token_merge_or_block_exploration_reopened=False,
                        GPU_submissions=0, SSH_calls=0, model_weights_downloaded=0,
                        scientific_quality_or_runtime_result=False, CUDA_initialized=False),
    )


def characterize_dispatch(source, expected):
    """Run the reviewed unknown-model branch with a Cosmos-name stand-in."""
    assert sha(source) == expected
    tree = ast.parse(source.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'apply_cache_on_transformer')
    assert not function.decorator_list
    events = []

    def no_import(*args, **kwargs):
        raise AssertionError('Unknown-model dispatch must not import a backend')

    env = dict(TRANSFORMER_ADAPTER_REGISTRY={},
               logger=SimpleNamespace(error=lambda msg: events.append(msg)),
               importlib=SimpleNamespace(import_module=no_import))
    module = ast.Module(body=[copy.deepcopy(function)], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(source), 'exec'), env)
    standin = type('MinimalV1LVGDiT', (), {})()
    returned = env['apply_cache_on_transformer'](standin, use_cache='Fast', enable_adacorrection=True)
    assert returned is standin and events == ['Unknown transformer class: MinimalV1LVGDiT']
    return dict(source_sha256=expected, first_line=function.lineno, last_line=function.end_lineno,
                model_class_name='MinimalV1LVGDiT', real_model_instantiated=False,
                unknown_model_returns_input_unchanged=True, logger_events=events,
                upstream_backend_imports=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    receipt = json.loads((args.source_root / 'source-receipt.json').read_text())
    assert receipt['commit'] == REVISION and not receipt['upstream_code_executed']
    binding = next(x for x in receipt['files'] if x['path'] == RELATIVE)
    source = args.source_root / 'tree' / RELATIVE
    result = characterize(source, binding['sha256'])
    dispatch_path = 'xfuser/model_executor/cache/diffusers_adapters/__init__.py'
    dispatch_binding = next(x for x in receipt['files'] if x['path'] == dispatch_path)
    result['unknown_Cosmos_name_dispatch'] = characterize_dispatch(
        args.source_root / 'tree' / dispatch_path, dispatch_binding['sha256'])
    result.update(source_archive_sha256=receipt['archive_sha256'], source_inventory_files=len(receipt['files']),
                  audit_script_sha256=sha(Path(__file__)))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('method_bindings', 'blend_path_cost_controls')}))


if __name__ == '__main__':
    main()
