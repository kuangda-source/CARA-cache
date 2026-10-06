"""Pinned forward CPU fixtures for three real masks, not actual generator execution."""
import argparse
import ast
import copy
from enum import Enum
import hashlib
import json
from pathlib import Path
import types
from typing import List, Optional, Tuple, Union


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    import sys
    sys.path.insert(0, str(args.stage/'src'))
    import torch
    from einops import rearrange
    from wcomr.fixed_replay import FixedReplay, build_replay_forward
    from wcomr.measurement import BlockCounts
    from wcomr.own_state_shadow import OwnStateProbe, build_own_state_forward
    if torch.cuda.is_initialized():raise RuntimeError('CPU contract already has CUDA context')
    torch.cuda._lazy_init = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('No CUDA in CPU core fixtures'))
    torch.set_num_threads(2)
    source = args.runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
    expected = json.loads((args.stage/'manifests/upstream.json').read_text())['cache_module_sha256']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    tree = ast.parse(source.read_text())
    selected = ['compute_optimal_gamma','estimate_optical_flow','warp_feature','worldcache_mini_train_dit_forward','apply_worldcache']
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in selected]
    assert len(tree.body) == len(selected)
    class DataType(Enum):VIDEO=1
    namespace = dict(torch=torch, amp=torch.amp, F=torch.nn.functional, rearrange=rearrange,
        DataType=DataType, Optional=Optional, List=List, Tuple=Tuple, Union=Union,
        log=types.SimpleNamespace(info=lambda *a: None))
    exec(compile(tree,str(source),'exec'),namespace)
    original = namespace['worldcache_mini_train_dit_forward']
    prereg = json.loads((args.stage/'manifests/wc_post_reference_hypotheses_r1_20261006.json').read_text())
    planned = prereg['future_measurement']
    assert planned['fixed_CFG_calls'] == [45,46,67,68] and len(planned['scenes']) == 3
    old = json.loads((args.stage/'reports/w1_replay_r1_runner.json').read_text())
    rows = {c['name']:c for c in old['cases']}
    class Block(torch.nn.Module):
        def __init__(self,factor):super().__init__();self.factor=factor
        def forward(self,x,**kwargs):return x*self.factor+.01
    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__();self.blocks=torch.nn.ModuleList([Block(1.02),Block(1.03),Block(1.04)])
            self.patch_spatial=self.patch_temporal=1
            self.use_crossattn_projection=self.use_wan_fp32_strategy=False
            self.t_embedder=lambda t:(t.unsqueeze(-1),None)
            self.t_embedding_norm=lambda t:t
            self.final_layer=lambda x,*a,**k:x
        def prepare_embedded_sequence(self,x,**kwargs):return x.permute(0,2,3,4,1).contiguous(),None,None
        def unpatchify(self,x):return x.permute(0,4,1,2,3).contiguous()
    def make(flow=False):
        return namespace['apply_worldcache'](Toy(),num_steps=70,ret_ratio=.2,rel_l1_thresh=1,
            probe_depth=1,osi_enabled=True,flow_enabled=flow,flow_scale=1).eval()
    def same(a,b):
        if isinstance(a,torch.Tensor):assert torch.equal(a,b)
        elif isinstance(a,dict):
            assert a.keys()==b.keys()
            for k in a:same(a[k],b[k])
        elif isinstance(a,(list,tuple)):
            assert len(a)==len(b)
            for x,y in zip(a,b):same(x,y)
        else:assert a==b
    def fixture(name,flow,random_tail=False):
        entry=rows[name]['scalar_off'];trace=entry['trace'];params=entry['replay']['calibration_params']
        assert entry['outcome']=='ACCEPTED' and len(trace)==72 and params==old['protocol']['calibration_defaults']
        nets=[make(flow),make(flow)]
        controllers=[FixedReplay(trace,'scalar',params) for _ in nets]
        for replay in controllers:replay.begin_request('paired')
        probe=OwnStateProbe(planned['fixed_CFG_calls'],controllers[1]);probe.begin_request('paired')
        nets[0].forward=types.MethodType(build_replay_forward(original,controllers[0]),nets[0])
        nets[1].forward=types.MethodType(build_own_state_forward(original,controllers[1],probe),nets[1])
        class RandomBlock(torch.nn.Module):
            def __init__(self):super().__init__();self.register_buffer('visits',torch.zeros(()))
            def forward(self,x,**kwargs):
                self.visits.add_(1);return x*1.03+torch.rand_like(x)*.001
        if random_tail:
            for net in nets:net.blocks[1]=RandomBlock().eval()
        all_results=[];manual={}
        for arm,net in enumerate(nets):
            torch.manual_seed(107);counter=BlockCounts(net.blocks,cache_model=net)
            x=torch.linspace(.7,1.3,72).reshape(1,3,2,3,4);output=[]
            try:
                for step in range(36):
                    velocities=[]
                    for branch in range(2):
                        call=2*step+branch+1;t=torch.tensor([1-step/36])
                        if arm==0 and call in planned['fixed_CFG_calls'] and not random_tail:
                            # Independent official forward on this exact candidate cache/input, never the old OFF trajectory.
                            fork=copy.deepcopy(net)
                            for module in fork.modules():
                                module._forward_hooks.clear();module._forward_pre_hooks.clear()
                            control=FixedReplay(trace,'official');control.begin_request('counterfactual')
                            control.call=call-1
                            fork.forward=types.MethodType(build_replay_forward(original,control),fork)
                            official=fork(x,t,torch.ones(1))
                            truth=x.permute(0,2,3,4,1).clone()
                            for block in fork.blocks:truth=block(truth)
                            truth=fork.unpatchify(truth)
                            manual[call]={'official':official,'truth':truth}
                        v=net(x,t,torch.ones(1));velocities.append(v);output.append(v.clone())
                    x=x+.005*(velocities[0]+velocities[1])
                all_results.append({'outputs':output,'trace':copy.deepcopy(counter.trace),
                    'counts':counter.result(),'RNG':torch.get_rng_state().clone()})
            finally:counter.close()
        for key in ['outputs','trace','counts','RNG']:same(all_results[0][key],all_results[1][key])
        same(controllers[0].finish(),controllers[1].finish())
        for field in ['residual_cache','probe_residual_cache','residual_window','probe_residual_window',
                      'previous_input','previous_output','previous_internal_states','resume_flag','accumulated_rel_l1_distance']:
            same(getattr(nets[0],field),getattr(nets[1],field))
        assert all_results[0]['trace']==trace and not hasattr(nets[1],'_w1_shadow_active')
        records=probe.finish();assert len(records)==4
        if random_tail:same(nets[0].blocks[1].visits,nets[1].blocks[1].visits)
        else:
            for record in records:
                call=record['call'];truth=manual[call]['truth']
                for mode,pred in [('official',manual[call]['official']),('scalar',all_results[0]['outputs'][call-1])]:
                    mse=(pred.float()-truth.float()).square().mean().item()
                    assert abs(record['candidates'][mode]['velocity']['mse']-mse)<1e-12
        return {'scene':name,'flow':flow,'random_state_fixture':random_tail,'calls':[r['call'] for r in records],
            '72_outputs_trace_full_anchors_cache_RNG_unchanged':True,'both_CFG_actual_input_pairs_equal':True,
            'official_and_scalar_MSE_independent_teacher_checked':not random_tail}
    checks=[fixture(name,flow) for name in planned['scenes'] for flow in [False,True]]
    checks.append(fixture(planned['scenes'][0],False,True))
    with torch.inference_mode():checks.append(fixture(planned['scenes'][0],True))
    refusals=[]
    trace=rows[planned['scenes'][0]]['scalar_off']['trace'];params=old['protocol']['calibration_defaults']
    for calls in [[45],[46,47],[45,46,45,46],[1,2],[73,74]]:
        try:OwnStateProbe(calls,FixedReplay(trace,'scalar',params))
        except ValueError:refusals.append(calls)
        else:raise AssertionError('Malformed or full registered pair accepted')
    replay=FixedReplay(trace,'scalar',params);replay.begin_request('bad-CFG')
    probe=OwnStateProbe([45,46],replay);probe.begin_request('bad-CFG');net=make()
    net.forward=types.MethodType(build_own_state_forward(original,replay,probe),net)
    for call in range(1,46):net(torch.ones(1,3,2,3,4),torch.ones(1),torch.ones(1))
    try:net(torch.ones(1,3,2,3,4)*1.01,torch.ones(1),torch.ones(1))
    except RuntimeError as error:assert 'same actual solver input' in str(error)
    else:raise AssertionError('Separate CFG solver input accepted')
    replay=FixedReplay(trace,'scalar',params);replay.begin_request('fault')
    probe=OwnStateProbe([45,46],replay);probe.begin_request('fault');net=make()
    class FaultBlock(Block):
        def __init__(self):super().__init__(1.04);self.register_buffer('visits',torch.zeros(()))
        def forward(self,x,**kwargs):
            if getattr(net,'_w1_shadow_active',False):
                self.visits.add_(7);torch.rand(1);raise RuntimeError('Deliberate teacher failure')
            return super().forward(x,**kwargs)
    net.blocks[-1]=FaultBlock().eval()
    net.forward=types.MethodType(build_own_state_forward(original,replay,probe),net)
    for call in range(1,45):net(torch.ones(1,3,2,3,4),torch.ones(1),torch.ones(1))
    rng=torch.get_rng_state().clone();buffer=net.blocks[-1].visits.clone()
    try:net(torch.ones(1,3,2,3,4),torch.ones(1),torch.ones(1))
    except RuntimeError as error:assert 'Deliberate teacher failure' in str(error)
    else:raise AssertionError('Teacher failure not surfaced')
    assert torch.equal(rng,torch.get_rng_state()) and torch.equal(buffer,net.blocks[-1].visits)
    assert not hasattr(net,'_w1_shadow_active') and not probe.records and probe.official_hidden is None
    assert not torch.cuda.is_initialized()
    print(json.dumps({'status':'OWN_W1_STATE_PINNED_FORWARD_THREE_MASK_CPU_CORE_PASS_NOT_REAL_MODEL',
        'checks':checks,'malformed_or_non_skip_pair_refusals':refusals,'mismatched_actual_CFG_input_refused':True,
        'teacher_exception_restores_RNG_buffer_marker_without_label':True,
        'source_sha256':expected,'prereg_sha256':hashlib.sha256((args.stage/'manifests/wc_post_reference_hypotheses_r1_20261006.json').read_bytes()).hexdigest(),
        'CPU_only':True,'CUDA_initialized':False,'GPU_submissions':0,'real_model_weights_loaded':False,
        'new_scientific_teacher_labels':0,'actual_videos':0,'test_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}))


if __name__=='__main__':main()
