"""Small-tensor source-bound tests, not real weights, full parent or host admission."""
import ast
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
from types import ModuleType, SimpleNamespace
import unittest

import numpy as np
import torch
from einops import rearrange

from wcomr.cfg_paired_probe_forward import WC_PATH, WC_SHA, RF_PATH, RF_SHA, _function, _compile
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_interval_readout_r1 import ReadoutKernel
from wcomr.scout_readout_v22 import (Anchor, LABELS, ScoutReadoutKernel, UnsupportedReadout,
                                    proposal, validate_state, spatial_gradient_diagnostics)

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ('EXPLICIT_CPU_FIXTURE', 'SMALL_TENSOR_NOT_COSMOS_WEIGHTS',
           '008d9fa12c7aad67e40440533a6e552147d79b82e44afebd8df55954f47b6e60')
torch.set_num_threads(1)


def module(runtime, path, digest, names):
    raw = (runtime/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest
    m = ModuleType('scout_cpu_'+Path(path).stem); m.__file__ = str(runtime/path)
    vars(m).update(torch=torch, rearrange=rearrange, F=torch.nn.functional)
    nodes = [n for n in ast.walk(ast.parse(raw)) if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == len(names)
    tree = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)]+nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(tree), str(runtime/path), 'exec'), vars(m))
    return m


class Head(torch.nn.Module):
    def forward(self, x, embedding, **kwargs):
        return x + .01*x.square() + .003*embedding.mean()


class Net(torch.nn.Module):
    def __init__(self, flow):
        super().__init__(); self.final_layer=Head(); self.register_buffer('audit_buffer',torch.zeros(1))
        self.worldcache_osi_enabled=True; self.worldcache_flow_enabled=flow; self.worldcache_flow_scale=1.
        self.cnt=0; self.residual_cache=[None,None]; self.previous_input=[None,None]
    def unpatchify(self, x): return x.movedim(-1,1).contiguous()


class Condition:
    def __init__(self, shape):
        self.is_video=True; self.use_video_condition=True
        self.gt_frames=torch.full(shape,.2)
        self.condition_video_input_mask_B_C_T_H_W=torch.zeros(shape[0],1,*shape[2:])
        self.condition_video_input_mask_B_C_T_H_W[:,:,0]=1
    def to_dict(self): return {}


def fixture(flow=False, step=33):
    runtime=ROOT/'cache/runtime'
    wc=module(runtime,WC_PATH,WC_SHA,['compute_optimal_gamma','estimate_optical_flow','warp_feature'])
    rf=module(runtime,RF_PATH,RF_SHA,['denoise'])
    original=_function(runtime,WC_PATH,WC_SHA,'worldcache_mini_train_dit_forward')
    nodes=[n for n in ast.walk(original) if isinstance(n,ast.If) and ast.unparse(n.test)=="getattr(self, 'worldcache_flow_enabled', False) and self.previous_input[current_idx] is not None"]
    assert len(nodes)==1
    fn=ast.parse('def warp(self,x_B_T_H_W_D,residual_x,T):\n current_idx=self.cnt%2\n return x_B_T_H_W_D').body[0]
    fn.body.insert(1,copy.deepcopy(nodes[0]));warp=_compile(fn,vars(wc),str(runtime/WC_PATH)+'#scout-test-exact-warp')
    net=Net(flow).eval(); model=SimpleNamespace(net=net,sample_scheduler=SimpleNamespace(history=[torch.ones(2)]),
        tensor_kwargs={'dtype':torch.float32},config=SimpleNamespace(conditional_frame_timestep=.2,denoise_replace_gt_frames=True))
    kernel=ScoutReadoutKernel(model,runtime,wc,rf,warp,max_logical_copy_bytes=128*1024**2)
    metadata=json.loads((ROOT/'plans/cara_predictor_refresh_scout_v2_20261026/E1_STATE_METADATA_V22.json').read_text())
    row=next(r for r in metadata['rows_per_prompt'] if r['step']==step)
    shape=(1,2,8,8,4); template=torch.linspace(-.2,.8,512).reshape(shape)
    anchors=[]; current=[]
    for b in (0,1):
        po=template+.1*b; pb=po+.2; ro=po*1.5+.3; rb=ro+.5
        anchors.append((Anchor(CONTEXT,b,row['anchor_older'],row['xi']-row['h']-row['H'],po,ro),
                        Anchor(CONTEXT,b,row['anchor_b'],row['xi']-row['h'],pb,rb)))
        ori=template+.7
        current.append(dict(original=ori,probe=ori+pb+.15,embedding=torch.ones(1,2,4),adaln=None))
    output_shape=(1,4,2,8,8);noise=torch.ones(output_shape);latent=noise*.5
    args=dict(context=CONTEXT,step=step,xi=row['xi'],anchors=tuple(anchors),current=current,
              pair_inputs=(noise,latent,torch.ones(1,2)*.7,tuple(Condition(output_shape) for _ in (0,1))))
    return kernel,args


class ScoutTests(unittest.TestCase):
    def test_pinned_head_RF_old_A_parity_all_states_and_flows(self):
        for flow in (False,True):
            for step in (22,23,25,33,34,35):
                kernel,a=fixture(flow,step)
                source=[dict(probe=b.probe,residual=b.residual,probe_window=[o.probe,b.probe],residual_window=[o.residual,b.residual]) for o,b in a['anchors']]
                old=ReadoutKernel.run(kernel,'A_ONE' if step<25 else 'A_HALF',source=source,current=copy.deepcopy(a['current']),pair_inputs=a['pair_inputs'])[0]
                new=kernel.evaluate('A_PHASE',**a)
                for x,y in zip(old,new['outputs']): self.assertTrue(torch.equal(x,y))
                # Original RF conditioning must preserve the known first-frame teacher velocity.
                self.assertTrue(torch.equal(new['outputs'][0][:,:,0],torch.full_like(old[0][:,:,0],.8)))

    def test_all_candidates_order_independent_and_restore(self):
        for flow in (False,True):
            k,a=fixture(flow);s=CompleteStateRoundtrip(k.net,k.model.sample_scheduler,a['pair_inputs'][1]);before=s.fingerprint()
            first={label:k.evaluate(label,**a) for label in LABELS}
            for label in reversed(LABELS):
                other=k.evaluate(label,**a)
                for x,y in zip(first[label]['outputs'],other['outputs']):self.assertTrue(torch.equal(x,y))
                self.assertEqual(s.fingerprint(),before)

    def test_short_fallback_exact_A_and_long_matches_global(self):
        for step in (22,23,25,33,34,35):
            k,a=fixture(step=step)
            left=k.evaluate('R4_LONG',**a)['outputs']
            right=k.evaluate('A_PHASE' if step<30 else 'R4_GLOBAL',**a)['outputs']
            for x,y in zip(left,right):self.assertTrue(torch.equal(x,y))

    def test_DCTA_three_clipping_regions_and_zero_denominator(self):
        _,a=fixture();o,b=a['anchors'][0]
        for ratio,expected in ((.5,1.),(1.5,1.5),(3.,2.)):
            p=o.probe+ratio*(b.probe-o.probe)
            out,meta=proposal('DCTA',p,o,b,kappa=1.,age=3)
            self.assertAlmostEqual(meta['gamma'],expected,places=5)
            self.assertTrue(torch.allclose(out,o.residual+expected*(b.residual-o.residual)))
        with self.assertRaises(UnsupportedReadout):proposal('DCTA',o.probe,o,replace(b,probe=o.probe),kappa=1.,age=3)

    def test_same_current_shallow_remainder_algebra_discriminates_FULL(self):
        _,a=fixture();o,b=a['anchors'][0]
        o=replace(o,probe=torch.tensor([0.,0.]),residual=torch.tensor([0.,0.]))
        b=replace(b,probe=torch.tensor([10.,0.]),residual=torch.tensor([11.,0.]))
        p=torch.tensor([110.,0.]);truth=torch.tensor([112.,1.])
        vals={j:proposal(j,p,o,b,kappa=1.,age=3)[0] for j in ('A_PHASE','FULL','R4_GLOBAL')}
        errors={j:float((v-truth).square().sum()) for j,v in vals.items()}
        self.assertEqual(errors,dict(A_PHASE=2.,FULL=8101.,R4_GLOBAL=1.))

    def test_wrong_history_branch_request_and_noise_rejected(self):
        _,a=fixture();pairs=a['anchors']
        for altered in (replace(pairs[0][1],branch=1),replace(pairs[0][1],context=('other',*CONTEXT[1:])),
                        replace(pairs[0][1],step=33),replace(pairs[0][1],xi=pairs[0][0].xi)):
            with self.assertRaises(UnsupportedReadout):validate_state(CONTEXT,a['step'],a['xi'],((pairs[0][0],altered),pairs[1]))

    def test_failure_restores_solver_cache_buffers_and_three_rngs(self):
        k,a=fixture();s=CompleteStateRoundtrip(k.net,k.model.sample_scheduler,a['pair_inputs'][1]);before=s.fingerprint()
        def broken(*args,**kwargs):
            k.net.cnt=999;k.net.audit_buffer.add_(1);k.model.sample_scheduler.history.append(torch.zeros(1))
            random.random();np.random.rand();torch.rand(2)
            raise OSError('injected head failure')
        k.net.final_layer.forward=broken
        with self.assertRaisesRegex(OSError,'injected'):k.evaluate('R4_GLOBAL',**a)
        self.assertEqual(s.fingerprint(),before)

    def test_private_input_copy_and_missing_support(self):
        k,a=fixture();old=k._evaluate
        def mutate(label,spans,anchors,current,pair_inputs):
            current[0]['original'].add_(10);anchors[0][0].probe.add_(20)
            return old(label,spans,anchors,current,pair_inputs)
        k._evaluate=mutate
        before=a['current'][0]['original'].clone();po=a['anchors'][0][0].probe.clone()
        k.evaluate('A_PHASE',**a)
        self.assertTrue(torch.equal(before,a['current'][0]['original']))
        self.assertTrue(torch.equal(po,a['anchors'][0][0].probe))
        with self.assertRaises(UnsupportedReadout):k.evaluate('DCTA',**{**a,'anchors':(a['anchors'][0],)})

    def test_spatial_gradient_constant_teacher_and_axis_separation(self):
        d=torch.zeros(1,2,3,4,5);v=d.clone();v[:,:,:,2:]=1
        m=spatial_gradient_diagnostics(v,d)
        self.assertTrue(m['zero_teacher_gradient']);self.assertGreater(m['gradient_residual_MSE'],0)
        temporal=d.clone();temporal[:,:,1:]=10
        self.assertEqual(spatial_gradient_diagnostics(temporal,d)['gradient_residual_MSE'],0)

    def test_copy_budget_refuses_before_clone_or_head(self):
        k,a=fixture();k.max_logical_copy_bytes=1
        def forbidden(*args,**kwargs):raise AssertionError('head must not run')
        k.net.final_layer.forward=forbidden
        with self.assertRaisesRegex(UnsupportedReadout,'budget'):k.evaluate('R4_GLOBAL',**a)

    def test_WC_C_rejects_invalid_features_and_training(self):
        k,a=fixture();a['current'][0]['probe'][0,0,0,0,0]=float('nan')
        with self.assertRaises(UnsupportedReadout):k.evaluate('WC_C',**a)
        k,a=fixture();k.net.train()
        with self.assertRaises(UnsupportedReadout):k.evaluate('WC_C',**a)


if __name__=='__main__':unittest.main()
