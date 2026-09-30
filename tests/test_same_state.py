import ast
import torch
import pytest
from einops import rearrange
from test_integration import upstream, Toy, run, model, SOURCE
from test_shadow_forward import equal_tree
from wcomr.same_state import SameStateProbe, build_same_state_forward
from wcomr.integration import build_forward
from wcomr.measurement import BlockCounts


def same_model(probe, flow=False):
    ns=upstream()
    if flow:
        tree=ast.parse(SOURCE.read_text())
        tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('estimate_optical_flow','warp_feature')]
        ns.update(F=torch.nn.functional,rearrange=rearrange)
        exec(compile(tree,str(SOURCE),'exec'),ns)
    ns['worldcache_mini_train_dit_forward']=build_same_state_forward(ns['worldcache_mini_train_dit_forward'],probe)
    m=ns['apply_worldcache'](Toy(),num_steps=20,ret_ratio=.3,rel_l1_thresh=1,probe_depth=1,
                            osi_enabled=True,flow_enabled=flow,flow_scale=1).eval()
    return m


@pytest.mark.parametrize('flow',[False,True])
def test_same_state_candidates_preserve_official_outputs_cache_counts_and_full_only_anchors(flow):
    probe=SameStateProbe([8,9,10,11,12]);probe.begin_request('one')
    scored=same_model(probe,flow)
    plain=model('official').eval()
    if flow:
        # Use the same pinned functions for the plain official path.
        ns=upstream();ns.update(F=torch.nn.functional,rearrange=rearrange)
        tree=ast.parse(SOURCE.read_text())
        tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('estimate_optical_flow','warp_feature')]
        exec(compile(tree,str(SOURCE),'exec'),ns)
        plain=ns['apply_worldcache'](Toy(),num_steps=20,ret_ratio=.3,rel_l1_thresh=1,probe_depth=1,
                                   osi_enabled=True,flow_enabled=True,flow_scale=1).eval()
    counts=BlockCounts(scored.blocks,cache_model=scored)
    rng=torch.get_rng_state().clone()
    a,b=run(plain,12),run(scored,12)
    assert torch.equal(rng,torch.get_rng_state())
    for x,y in zip(a,b):assert torch.equal(x,y)
    for field in ['cnt','residual_cache','probe_residual_cache','residual_window','probe_residual_window',
                  'previous_input','previous_output','previous_internal_states','resume_flag','accumulated_rel_l1_distance']:
        equal_tree(getattr(plain,field),getattr(scored,field))
    assert counts.result()=={'denoiser_calls':12,'full_calls':6,'skipped_deep_calls':6}
    assert len(probe.records)==5
    for record in probe.records:
        assert set(record['candidates'])=={'official','scalar','shrink'}
        for mode in ('scalar','shrink'):
            c=record['candidates'][mode]
            assert c['reason']==mode
            assert c['history']['anchor_steps']==([2,4] if record['cfg_branch']==0 else [3,5])
            assert max(c['history']['anchor_steps'])<record['cache_counter']
            assert all(c[k]['status']=='OK' for k in ('prewarp_residual','postwarp_residual','velocity'))
        # CPU toy allows a full-stack truth computed independently at this input.
        i=record['call']-1;truth=torch.full((1,2,2,2,3),1+i*.001)
        for block in plain.blocks:truth=block(truth)
        expected=((b[i]-truth).square().mean()/truth.square().mean()).item()
        assert record['candidates']['official']['velocity']['relative_mse']==pytest.approx(expected)
    counts.close()


@pytest.mark.parametrize('mode',['scalar','shrink'])
def test_candidate_pinned_warp_matches_actual_injected_candidate_forward_on_spatial_input(mode):
    probe=SameStateProbe([7,8]);probe.begin_request('request')
    scored=same_model(probe,flow=True)
    ns=upstream();ns.update(F=torch.nn.functional,rearrange=rearrange)
    tree=ast.parse(SOURCE.read_text())
    tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('estimate_optical_flow','warp_feature')]
    exec(compile(tree,str(SOURCE),'exec'),ns)
    ns['worldcache_mini_train_dit_forward']=build_forward(ns['worldcache_mini_train_dit_forward'],mode)
    deployed=ns['apply_worldcache'](Toy(),num_steps=20,ret_ratio=.3,rel_l1_thresh=1,probe_depth=1,
                                  osi_enabled=True,flow_enabled=True,flow_scale=1).eval()
    spatial=torch.linspace(.7,1.3,72).reshape(1,2,3,4,3)
    for i in range(8):
        x=spatial+i*.0001*(1+spatial.square())
        scored(x,torch.ones(1),torch.ones(1))
        actual=deployed(x,torch.ones(1),torch.ones(1))
        if i>=6:
            truth=x.clone()
            for block in scored.blocks:truth=block(truth)
            expected=((actual-truth).square().mean()/truth.square().mean()).item()
            assert probe.records[-1]['candidates'][mode]['velocity']['relative_mse']==pytest.approx(expected)
            assert probe.records[-1]['candidates'][mode]['reason']==mode


def test_reset_requests_and_cache_horizon_never_reuse_old_anchors():
    probe=SameStateProbe([8]);probe.begin_request('r1');m=same_model(probe)
    run(m,20);run(m,1)
    assert probe.cycle==2
    assert probe.calibrators['scalar'][0].receipt()['anchor_steps']==[0]
    assert probe.calibrators['scalar'][1].receipt()['anchor_steps']==[]
    m.cnt=0;probe.begin_request('r2');run(m,1)
    assert probe.cycle==1 and probe.records==[]
    assert probe.calibrators['shrink'][0].context[0]=='r2'


def test_extra_head_deep_and_warp_restore_rng_and_buffers():
    class RandomBlock(torch.nn.Module):
        def __init__(self):
            super().__init__();self.register_buffer('visits',torch.zeros(()))
        def forward(self,x,**kwargs):
            self.visits.add_(1);return x*1.03+torch.rand_like(x)*.001
    probe=SameStateProbe([8,9,10,11,12]);probe.begin_request('random')
    plain=model('official').eval();observed=same_model(probe)
    plain.blocks[1]=RandomBlock().eval();observed.blocks[1]=RandomBlock().eval()
    torch.manual_seed(77);a=run(plain,12);after=torch.get_rng_state().clone()
    torch.manual_seed(77);b=run(observed,12)
    assert torch.equal(after,torch.get_rng_state())
    assert torch.equal(plain.blocks[1].visits,observed.blocks[1].visits)
    for x,y in zip(a,b):assert torch.equal(x,y)


def test_same_state_requires_request_and_supported_source():
    probe=SameStateProbe([8]);m=same_model(probe)
    with pytest.raises(RuntimeError,match='begin_request'):run(m,1)
    with pytest.raises(RuntimeError,match='warp section'):
        build_same_state_forward(SameStateProbe.collect,probe)


def test_expert_switch_resets_candidates_and_falls_back_without_old_anchors():
    probe=SameStateProbe([8]);probe.begin_request('expert-change');m=same_model(probe)
    run(m,7)
    assert probe.calibrators['scalar'][1].anchors
    m._w1_expert_key='second-expert'
    run(m,1)
    record=probe.records[0]
    assert record['cycle']==2
    for mode in ('scalar','shrink'):
        c=record['candidates'][mode]
        assert c['history']['anchor_steps']==[]
        assert c['reason']=='insufficient_anchors'
