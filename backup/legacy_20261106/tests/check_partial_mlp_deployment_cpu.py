"""Pinned WC/RF/full Block deployment with declared small CPU attention.

All26 complete full36 paths use a Toy latent update, not UniPC or video.
The independent partial reference pays FULL MLP GEMMs then substitutes stale
inactive projections; only the candidate must actually gather before GEMMs.
"""
import argparse
import ast
import copy
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from types import MethodType, ModuleType, SimpleNamespace
from typing import Optional


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False, parents=True)
    import torch
    from einops import rearrange
    from wcomr.cfg_paired_probe_forward import WC_PATH, WC_SHA, RF_PATH, RF_SHA
    from wcomr.cfg_paired_probe_production import compile_production
    from wcomr.cfg_paired_probe_native_policy import NativePolicyPairedExecutor
    from wcomr.cfg_ra_calibration import SharedSchedulePairExecutor
    from wcomr.cfg_guided_w1_collection import tensor_sha
    from wcomr.partial_mlp_deployment import (PartialDeployment, PartialDeploymentPair,
        compile_partial_deployment, METHODS, P_STEPS, D_STEPS)
    assert not torch.cuda.is_initialized()
    def forbidden(*unused, **kw):
        raise RuntimeError('P0 deployment CPU forbids CUDA and downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)

    class DataType(str, Enum):
        VIDEO = 'video'
        IMAGE = 'image'
    quiet = SimpleNamespace(**{k: lambda *x, **y: None for k in ('info', 'debug', 'warning')})
    def module(relative, digest, names):
        path = args.runtime/relative
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest
        m = ModuleType('controlled_'+path.stem)
        m.__file__ = str(path)
        vars(m).update(torch=torch, rearrange=rearrange, amp=torch.amp,
            F=torch.nn.functional, DataType=DataType, log=quiet)
        nodes = [n for n in ast.walk(ast.parse(raw)) if isinstance(n, ast.FunctionDef) and n.name in names]
        assert sorted(n.name for n in nodes) == sorted(names)
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future]+nodes, type_ignores=[])),
                     str(path), 'exec'), vars(m))
        return m
    wc = module(WC_PATH, WC_SHA, ['worldcache_mini_train_dit_forward', 'apply_worldcache',
        'compute_optimal_gamma', 'estimate_optical_flow', 'warp_feature', 'compute_saliency_map'])
    rf = module(RF_PATH, RF_SHA, ['denoise'])
    rf.Video2WorldModelRectifiedFlow = SimpleNamespace(denoise=rf.denoise)
    block_path = args.runtime/'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py'
    block_raw = block_path.read_bytes()
    assert hashlib.sha256(block_raw).hexdigest() == 'a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071'
    classes = [n for n in ast.parse(block_raw).body if isinstance(n, ast.ClassDef)
               and n.name in ('Block', 'GPT2FeedForward')]
    assert len(classes) == 2
    class TinyAttention(torch.nn.Module):
        def __init__(self, *unused, **kw):
            super().__init__()
            self.calls = 0
        def forward(self, x, context=None, **kw):
            self.calls += 1
            return x*.007+(0 if context is None else context.mean()*.003)
        def init_weights(self):
            pass
    @dataclass
    class VideoSize:
        T: int
        H: int
        W: int
    ns = {'torch': torch, 'nn': torch.nn, 'math': math, 'Optional': Optional,
        'amp': torch.amp, 'rearrange': rearrange, 'Attention': TinyAttention,
        'I2VCrossAttention': TinyAttention, 'VideoSize': VideoSize}
    exec(compile(ast.fix_missing_locations(ast.Module(body=classes, type_ignores=[])),
                 str(block_path)+'#P0_deployment_CPU', 'exec'), ns)
    layers = (4, 10, 16, 22)
    class Head(torch.nn.Module):
        def forward(self, x, emb, **kw):
            return x+.01*x.square()+.003*emb.mean()
    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = torch.nn.ModuleList([ns['Block'](8, 8, 2, mlp_ratio=4,
                use_adaln_lora=False, backend='declared_tiny_CPU_attention') for _ in range(28)])
            self.final_layer = Head()
            self.use_crossattn_projection = self.use_wan_fp32_strategy = False
            self.t_embedder = lambda t: (t.reshape(1, 1, 1).expand(1, 2, 8).contiguous(), None)
            self.t_embedding_norm = lambda t: t
            self.prepare_embedded_sequence = lambda x, **kw: (x.movedim(1, -1).contiguous(), None, None)
            self.unpatchify = lambda x: x.movedim(-1, 1).contiguous()
        def forward(self, **kw):
            return wc.worldcache_mini_train_dit_forward(self, **kw)
    shape = (1, 8, 2, 8, 8)
    noise = torch.linspace(-.3, .7, math.prod(shape)).reshape(shape)
    initial = noise+.7
    class Condition:
        def __init__(self, branch):
            self.is_video = self.use_video_condition = True
            self.gt_frames = torch.full(shape, .2)
            self.condition_video_input_mask_B_C_T_H_W = torch.zeros(1, 1, 2, 8, 8)
            self.condition_video_input_mask_B_C_T_H_W[:, :, 0] = 1
            self.cross = torch.ones(1, 3, 8)*(branch+1)
        def to_dict(self):
            return {'crossattn_emb': self.cross, 'data_type': DataType.VIDEO}
    conditions = tuple(Condition(b) for b in (0, 1))
    pristine = [noise.clone(), initial.clone()]+[c.gt_frames.clone() for c in conditions]
    complete, failures = [], []
    context = ('CPU_FIXED_REQUEST', 'PINNED_FULL_BLOCK', 'FIXED_CONDITIONS')
    def semantic(method, step):
        if step in D_STEPS:
            return 'D'
        return 'P' if method not in ('SOURCE_BASE', 'OFF', 'DENSE_CONTROL') and step in P_STEPS else 'C'
    def independent_indices(method, step):
        tokens, block = 128, 16
        if method == 'FULL_P_DECLARED_P':
            return torch.arange(tokens)
        fraction = .5 if method.endswith('050') else .75
        count = math.floor(tokens//block*fraction)
        if method.startswith('RANDOM'):
            key = 'P0-DEPLOYMENT-CORE-R1:'+repr(context)+':'+str(step)
            seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big') % (2**63-1)
            selected = torch.randperm(tokens//block, generator=torch.Generator().manual_seed(seed))[:count].tolist()
        else:
            opportunity = P_STEPS.index(step)
            selected = [(opportunity*count+i) % (tokens//block) for i in range(count)]
        return torch.tensor(sorted(b*block+i for b in selected for i in range(block)))
    def run(flow, method, *, reference=False, fail=False):
        torch.manual_seed(7791)
        net = Net().eval()
        wc.apply_worldcache(net, num_steps=70, ret_ratio=.2, rel_l1_thresh=.08,
            probe_depth=2, osi_enabled=True, flow_enabled=flow, flow_scale=1)
        model = SimpleNamespace(net=net, tensor_kwargs={'dtype': torch.float32},
            config=SimpleNamespace(conditional_frame_timestep=.2, denoise_replace_gt_frames=True))
        model.denoise = MethodType(rf.denoise, model)
        deployment = None
        if method in ('SOURCE_BASE', 'TRUE_D_REFERENCE') or reference:
            _, denoise, proof = compile_production(args.runtime, wc, rf)
        else:
            deployment = PartialDeployment(model, method=method, context=context, layers=layers, block_size=16)
            if fail:
                original_hidden = deployment.hidden
                def injected(*values, **kw):
                    if deployment.current['step'] == 30 and values[2] == 1:
                        raise ValueError('Injected second-branch P0 failure step30')
                    return original_hidden(*values, **kw)
                deployment.hidden = injected
            _, denoise, proof = compile_partial_deployment(args.runtime, wc, rf, deployment)
        base = NativePolicyPairedExecutor(model, denoise, torch,
            wc_forward=wc.worldcache_mini_train_dit_forward, rf_denoise=rf.denoise)
        executor = PartialDeploymentPair(base, deployment) if deployment else SharedSchedulePairExecutor(base)
        logical = {'step': 0}
        reference_cache, hooks, linear_rows = {}, [], []
        if reference:
            for layer in layers:
                def replace_inactive(module, inputs, full, l=layer):
                    step, slot = logical['step'], net.cnt % 2
                    action = semantic(method, step)
                    assert action in ('D', 'P')
                    value = full
                    if action == 'P':
                        ids = independent_indices(method, step)
                        old = reference_cache[(l, slot)].reshape(128, 8)
                        value = old.clone()
                        value[ids] = full.reshape(128, 8)[ids]
                        value = value.reshape(full.shape)
                    reference_cache[(l, slot)] = value.detach().clone()
                    return value
                hooks.append(net.blocks[layer].mlp.register_forward_hook(replace_inactive))
        for layer in layers:
            for name in ('layer1', 'layer2'):
                def observe(m, inputs, l=layer, n=name):
                    linear_rows.append((logical['step'], net.cnt % 2, l, n, math.prod(inputs[0].shape[:-1])))
                hooks.append(getattr(net.blocks[layer].mlp, name).register_forward_pre_hook(observe))
        latent, guided, history = initial.clone(), [], []
        rng_after_constructor = torch.get_rng_state().clone()
        old_failure_cache = None
        error = None
        try:
            with torch.no_grad():
                for step in range(1, 37):
                    logical['step'] = step
                    if deployment is None:
                        executor.forced_action = 'DD' if step in P_STEPS and (reference or method == 'TRUE_D_REFERENCE') else None
                    if fail and step == 30:
                        old_failure_cache = dict(deployment.core.cache)
                        old_dense = copy.deepcopy([c.receipt() for c in deployment.dense])
                        old_working = copy.deepcopy(deployment.working)
                    values = executor.pair(noise, latent, torch.full((1, 1), 1-step/50), conditions, executor.choose)
                    value = values[0]+7*(values[0]-values[1])
                    guided.append(value.detach().clone())
                    latent = latent-.001*value
                    action = executor.last.get('semantic_action', executor.last['action'])
                    history.append({'step': step, 'action': action, 'counter': net.cnt})
                    if deployment:
                        row = deployment.history[-1]
                        expected = semantic(method, step)
                        assert row['action'] == expected*2
                        if expected != 'D':
                            assert row['true_D_before'] == row['true_D_after']
                        if expected == 'P':
                            assert row['working_source_ages'] == [0, 0]
                            assert all(s['kind'] == 'P' and s['creation_error'] == 'UNKNOWN_NOT_ZERO'
                                and not s['RA_zero_risk_reset_allowed'] for s in row['working_sources'])
                            assert all(r['last_actual_D'] < step for r in row['actual_projection_records'])
                            expected_rows = 128 if method == 'FULL_P_DECLARED_P' else 64 if method.endswith('050') else 96
                            observed = [r for r in linear_rows if r[0] == step]
                            assert len(observed) == 16 and all(r[-1] == expected_rows for r in observed)
                    if step == 35:
                        assert net.cnt == 0
                        if deployment:
                            assert deployment.working == [None, None]
                            assert all(not c.receipt()['anchor_steps'] for c in deployment.dense)
                            if deployment.core is not None:
                                assert not deployment.core.cache
                    if reference and step == 35:
                        reference_cache.clear()
                summary = deployment.finish() if deployment else None
        except ValueError as exc:
            error = str(exc)
        finally:
            for h in hooks:
                h.remove()
        if fail:
            assert error == 'Injected second-branch P0 failure step30', error
            assert len(guided) == 29 and deployment.poisoned and base.poisoned and deployment.core.poisoned
            assert all(deployment.core.cache[k] is v for k, v in old_failure_cache.items())
            assert [c.receipt() for c in deployment.dense] == old_dense and deployment.working == old_working
            refusals = 0
            with torch.no_grad():
                for call in (deployment.finish, lambda: deployment.begin(noise, latent, torch.ones(1, 1), conditions, None)):
                    try:
                        call()
                    except ValueError:
                        refusals += 1
            assert refusals == 2
            failures.append({'flow': flow, 'planned_pairs': 36, 'completed_pairs': 29,
                'failure_step': 30, 'failure_slot': 1, 'projection_cache_transaction_rolled_back': True,
                'working_and_D_ledger_not_committed': True, 'whole_WC_or_solver_fault_rollback_claim': False,
                'poisoned_no_resume': True, 'error': error})
            deployment.close()
            return
        assert error is None, error
        assert len(guided) == len(history) == 36 and [h['counter'] for h in history] == [2*s % 70 for s in range(1, 37)]
        assert torch.equal(torch.get_rng_state(), rng_after_constructor)
        if deployment:
            assert summary['teacher_calls'] == summary['extra_candidate_heads'] == 0
        label = 'flow'+str(flow)+'_'+method+('_INDEPENDENT_FULL_GEMM_REFERENCE' if reference else '')
        path = args.output/(label+'.pt')
        torch.save({'guided': guided, 'final_latent': latent}, path)
        loaded = torch.load(path, map_location='cpu', weights_only=True)
        assert all(torch.equal(x, y) for x, y in zip(guided, loaded['guided'])) and torch.equal(latent, loaded['final_latent'])
        complete.append({'flow': flow, 'method': method, 'independent_reference': reference,
            'completed_pairs': 36, 'actual_tensors_reloaded': 37,
            'guided_sha256': [tensor_sha(v) for v in guided], 'final_latent_sha256': tensor_sha(latent),
            'actual_Linear_input_rows': linear_rows, 'summary': summary, 'compiler': dict(proof),
            'path': str(path), 'bytes': path.stat().st_size(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        if deployment:
            deployment.close()
        return guided, latent
    for flow in (False, True):
        source = run(flow, 'SOURCE_BASE')
        full = run(flow, 'TRUE_D_REFERENCE')
        for method in METHODS:
            result = run(flow, method)
            if method in ('OFF', 'DENSE_CONTROL'):
                assert all(torch.equal(x, y) for x, y in zip(result[0], source[0]))
                assert torch.equal(result[1], source[1])
            elif method == 'FULL_P_DECLARED_P':
                assert all(torch.equal(x, y) for x, y in zip(result[0], full[0]))
                assert torch.equal(result[1], full[1])
            else:
                ref = run(flow, method, reference=True)
                for x, y in zip(result[0], ref[0]):
                    torch.testing.assert_close(x, y, rtol=1e-5, atol=2e-6)
                torch.testing.assert_close(result[1], ref[1], rtol=1e-5, atol=2e-6)
        run(flow, 'ROTATION_050', fail=True)
    assert len(complete) == 26 and len(failures) == 2
    assert len(list(args.output.glob('*.pt'))) == 26
    assert all(torch.equal(x, y) for x, y in zip(pristine, [noise, initial]+[c.gt_frames for c in conditions]))
    assert not torch.cuda.is_initialized()
    print(json.dumps({'status': 'P0_DEPLOYMENT_FULL36_PINNED_BLOCK_CPU_PASS_NOT_UNIPC_OR_VIDEO',
        'Torch_version': torch.__version__,
        'complete_paths': complete, 'registered_both_flow_second_branch_failures': failures,
        'actual_complete_pairs': 936, 'actual_normal_net_calls': 1872, 'actual_tensors_reloaded': 962,
        'independent_full_GEMM_then_replace_reference_for_all8_partial_rollouts': True,
        'OFF_and_dense_maintenance_full_source_parity_both_flows': True,
        'full_P_matches_true_D_output_but_remains_P_provenance_both_flows': True,
        'actual_gathered_Linear_rows_64_or_96_verified_for_all_partial_opportunities': True,
        'working_P_not_D_calibration_or_zero_risk_RA_source': True,
        'actual_UniPC_or_Cosmos_weights_or_video_or_quality_or_latency_claim': False,
        'CUDA_initialized': False, 'GPU_submissions': 0}, allow_nan=False))


if __name__ == '__main__':
    main()
