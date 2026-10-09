"""Pinned WC/RF A readout controls with declared small Toy modules.

Complete full36 direct rollouts exercise both flow settings, D6 and the real
RA selector interface. The latent update is a Toy update, not UniPC/video.
"""
import argparse
import ast
import copy
from enum import Enum
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace, ModuleType, MethodType


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    assert not args.output.exists()
    args.output.mkdir(parents=True)
    import torch
    from einops import rearrange
    from wcomr.cfg_paired_probe_forward import WC_PATH, WC_SHA, RF_PATH, RF_SHA
    from wcomr.cfg_paired_probe_production import compile_production
    from wcomr.cfg_guided_w1_forward import compile_collection
    from wcomr.cfg_guided_w1_deployment import (
        GuidedW1Readout, GuidedW1DeploymentPair, METHODS, alpha_at)
    from wcomr.cfg_guided_w1_collection import DENSE_STEPS, tensor_sha
    from wcomr.cfg_ra_calibration import SharedSchedulePairExecutor
    from wcomr.cfg_paired_probe_native_policy import NativePolicyPairedExecutor
    from wcomr.cfg_ra_joint_control import Calibration, JointCDController
    from wcomr.cfg_ra_joint_execution import JointPolicyPairExecutor
    assert not torch.cuda.is_initialized()
    def forbidden(*unused, **kw):
        raise RuntimeError('A deployment CPU forbids CUDA/download')
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
        nodes = [n for n in ast.walk(ast.parse(raw))
                 if isinstance(n, ast.FunctionDef) and n.name in names]
        assert sorted(n.name for n in nodes) == sorted(names)
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future]+nodes, type_ignores=[])),
                     str(path), 'exec'), vars(m))
        return m
    wc = module(WC_PATH, WC_SHA, ['worldcache_mini_train_dit_forward', 'apply_worldcache',
        'compute_optimal_gamma', 'estimate_optical_flow', 'warp_feature', 'compute_saliency_map'])
    rf = module(RF_PATH, RF_SHA, ['denoise'])
    rf.Video2WorldModelRectifiedFlow = SimpleNamespace(denoise=rf.denoise)
    class Block(torch.nn.Module):
        def __init__(self, index):
            super().__init__()
            self.gain = torch.nn.Parameter(torch.tensor(1.001+index*.0001), requires_grad=False)
            self.register_buffer('visits', torch.zeros(()))
        def forward(self, x, **kw):
            self.visits.add_(1)
            return x*self.gain+.002*kw['crossattn_emb'].mean()+.0001*kw['emb_B_T_D'].mean()+torch.rand(())*.00001
    class Head(torch.nn.Module):
        def forward(self, x, emb, **kw):
            return x+.01*x.square()+.003*emb.mean()
    class Net(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = torch.nn.ModuleList([Block(i) for i in range(4)])
            self.final_layer = Head()
            self.use_crossattn_projection = self.use_wan_fp32_strategy = False
            self.t_embedder = lambda t: (t.unsqueeze(-1), None)
            self.t_embedding_norm = lambda t: t
            self.prepare_embedded_sequence = lambda x, **kw: (x.movedim(1, -1).contiguous(), None, None)
            self.unpatchify = lambda x: x.movedim(-1, 1).contiguous()
        def forward(self, **kw):
            return wc.worldcache_mini_train_dit_forward(self, **kw)
    shape = (1, 8, 2, 8, 8)
    noise = torch.linspace(-.3, .7, 1024).reshape(shape)
    initial = noise+.7
    class Condition:
        def __init__(self, branch):
            self.is_video = self.use_video_condition = True
            self.gt_frames = torch.full(shape, .2)
            self.condition_video_input_mask_B_C_T_H_W = torch.zeros(1, 1, 2, 8, 8)
            self.condition_video_input_mask_B_C_T_H_W[:, :, 0] = 1
            self.cross = torch.ones(1, 3, 4)*(branch+1)
        def to_dict(self):
            return {'crossattn_emb': self.cross, 'data_type': DataType.VIDEO}
    conditions = tuple(Condition(b) for b in (0, 1))
    initial_rng = torch.get_rng_state().clone()
    input_values = [noise.clone(), initial.clone()]+[c.gt_frames.clone() for c in conditions]
    calibration = Calibration('EXPLICIT_TOY_PRIOR_NOT_REAL_CAL',
        {(a, s): .95 for a in range(1, 36) for s in range(a+1, 37)}, {s: 1. for s in range(1, 37)})
    complete = []
    def run(flow, method, selector='D6', fail=False):
        torch.set_rng_state(initial_rng)
        net = Net().eval()
        wc.apply_worldcache(net, num_steps=70, ret_ratio=.2, rel_l1_thresh=.08,
            probe_depth=2, osi_enabled=True, flow_enabled=flow, flow_scale=1)
        model = SimpleNamespace(net=net, tensor_kwargs={'dtype': torch.float32},
            config=SimpleNamespace(conditional_frame_timestep=.2, denoise_replace_gt_frames=True))
        model.denoise = MethodType(rf.denoise, model)
        readout = None
        if method == 'SOURCE_BASE':
            _, denoise, proof = compile_production(args.runtime, wc, rf)
        else:
            readout = GuidedW1Readout(model, method=method, context=('CPU', selector, str(flow)))
            _, denoise, proof = compile_collection(args.runtime, wc, rf, readout)
        base = NativePolicyPairedExecutor(model, denoise, torch,
            wc_forward=wc.worldcache_mini_train_dit_forward, rf_denoise=rf.denoise)
        policy = (SharedSchedulePairExecutor(base) if selector == 'D6'
                  else JointPolicyPairExecutor(base, JointCDController(calibration, .015)))
        executor = GuidedW1DeploymentPair(policy, readout) if readout else policy
        if fail:
            real_hidden = readout.hidden
            # Recompile the explicit hook binding; changing the object after
            # compilation would leave the original bound callback installed.
            def injected(*values, **kw):
                if readout.current['step'] == 30 and values[2] == 1:
                    raise ValueError('Injected second-branch A failure at step30')
                return real_hidden(*values, **kw)
            readout.hidden = injected
            _, base.denoise, proof = compile_collection(args.runtime, wc, rf, readout)
        latent = initial.clone()
        guided, checks, output_checks = [], [], []
        if readout:
            original_end = readout.end
            def audited_end(actual, action):
                cur = readout.current
                alpha = alpha_at(method, cur['step'])
                expected = actual
                if alpha and action == 'CC':
                    proposed = tuple(readout.to_velocity(model, cur['noise'], cur['latent'], cur['timestep'],
                        cur['conditions'][b], _supplied_net_output=cur['branches'][b]['proposed_head'])
                        if cur['branches'][b]['proposed_head'] is not None else actual[b] for b in (0, 1))
                    expected = proposed if alpha == 1 else tuple(a+alpha*(b-a) for a, b in zip(actual, proposed))
                result = original_end(actual, action)
                assert all(torch.equal(a, b) for a, b in zip(result, expected))
                output_checks.append({'step': cur['step'], 'alpha': alpha, 'action': action,
                    'actual_post_RF_fusion_direct_equal': True, 'extra_teacher_calls': 0})
                return result
            readout.end = audited_end
        error = None
        with torch.no_grad():
            try:
                for step in range(1, 37):
                    values = executor.pair(noise, latent, torch.full((1, 1), 1-step/50), conditions, executor.choose)
                    value = values[0]+7*(values[0]-values[1])
                    guided.append(value.detach().clone())
                    latent = latent-.001*value
                    checks.append({'step': step, 'action': policy.last['action'], 'counter': net.cnt,
                        'buffers': [float(b) for b in net.buffers()], 'rng': tensor_sha(torch.get_rng_state())})
                summary = readout.finish() if readout else None
            except ValueError as exc:
                error = str(exc)
        if fail:
            assert error == 'Injected second-branch A failure at step30', error
            assert readout.poisoned and base.poisoned and readout.completed == 29
            refused = 0
            with torch.no_grad():
                for call in (lambda: readout.finish(), lambda: readout.begin(noise, latent, torch.ones(1, 1), conditions)):
                    try: call()
                    except ValueError: refused += 1
            assert refused == 2
            return {'status': 'EXPECTED_FAILURE', 'planned_pairs': 36, 'completed_pairs': 29,
                'failure_branch': 1, 'failure_step': 30, 'poisoned_no_resume': True,
                'complete_scope_retained': True, 'error': error}
        assert error is None, error
        assert len(guided) == 36 and [x['counter'] for x in checks] == [2*s % 70 for s in range(1, 37)]
        if selector == 'D6':
            assert [x['action'] for x in checks] == ['DD' if s in DENSE_STEPS else 'CC' for s in range(1, 37)]
        if readout:
            assert len(output_checks) == 36 and summary['teacher_calls'] == summary['extra_candidate_deep_blocks'] == 0
            for h in summary['history']:
                assert h['shared_alpha'] == alpha_at(method, h['step'])
                for anchors in h['past_D_steps']:
                    assert all(a <= h['step'] if h['action'] == 'DD' else a < h['step'] for a in anchors)
            if method == 'OFF':
                assert summary['extra_candidate_heads'] == 0
                assert all(not c['anchor_steps'] for c in summary['D_only_final_history'])
            else:
                assert summary['extra_candidate_heads'] > 0
        label = 'flow'+str(flow)+'_'+selector+'_'+method
        path = args.output/(label+'.pt')
        torch.save({'guided': guided, 'final_latent': latent}, path)
        loaded = torch.load(path, map_location='cpu', weights_only=True)
        assert all(torch.equal(x, y) for x, y in zip(guided, loaded['guided']))
        assert torch.equal(latent, loaded['final_latent'])
        complete.append({'flow': flow, 'selector': selector, 'method': method, 'completed_pairs': 36,
            'guided_sha256': [tensor_sha(x) for x in guided], 'final_latent_sha256': tensor_sha(latent),
            'actual_tensors_reloaded': 37, 'compiler': dict(proof), 'summary': summary,
            'actual_post_RF_checks': output_checks, 'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        return {'guided': guided, 'latent': latent, 'checks': checks, 'rng': torch.get_rng_state().clone()}
    refusals = []
    for method, step in (('unknown', 1), ('W1_GLOBAL_1', 0), ('W1_ONE_PHASE', 37), ('OFF', True)):
        try: alpha_at(method, step)
        except ValueError: refusals.append([method, step])
        else: raise AssertionError('Invalid method/horizon accepted')
    for flow in (False, True):
        baseline = run(flow, 'SOURCE_BASE')
        off = run(flow, 'OFF')
        assert baseline['checks'] == off['checks'] and torch.equal(baseline['rng'], off['rng'])
        assert torch.equal(baseline['latent'], off['latent'])
        assert all(torch.equal(a, b) for a, b in zip(baseline['guided'], off['guided']))
        for method in METHODS[1:]:
            result = run(flow, method)
            assert all(torch.equal(a, b) for a, b in zip(baseline['guided'][:7], result['guided'][:7]))
        for method in ('OFF', 'W1_ONE_PHASE'):
            run(flow, method, selector='RA_TOY_PRIOR')
    failure = run(True, 'W1_ONE_PHASE', fail=True)
    assert len(complete) == 16 and len(list(args.output.glob('*.pt'))) == 16
    assert all(torch.equal(a, b) for a, b in zip(input_values, [noise, initial]+[c.gt_frames for c in conditions]))
    torch.set_rng_state(initial_rng)
    assert not torch.cuda.is_initialized()
    print(json.dumps({'status': 'A_DEPLOYMENT_FULL36_CONTROLLED_CPU_PASS_NOT_UNIPC_OR_VIDEO',
        'Torch_version': torch.__version__, 'complete_paths': complete,
        'actual_complete_pairs': 576, 'actual_normal_net_calls': 1152,
        'actual_tensors_reloaded': 592, 'registered_second_branch_failure': failure,
        'invalid_method_horizon_refused': refusals,
        'both_flow_OFF_direct_source_parity': True,
        'RA_prior_is_explicit_Toy_not_real_CAL': True,
        'CUDA_initialized': False, 'GPU_submissions': 0,
        'actual_UniPC_or_Cosmos_weights_or_video_or_quality_or_latency_claim': False}, allow_nan=False))


if __name__ == '__main__':
    main()
