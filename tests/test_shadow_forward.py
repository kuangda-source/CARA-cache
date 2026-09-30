import copy
import torch
import pytest
from test_integration import upstream, Toy, run, model
from wcomr.shadow_forward import ShadowProbe, build_shadow_forward
from wcomr.measurement import BlockCounts


def shadow_model(mode, probe):
    ns=upstream()
    ns['worldcache_mini_train_dit_forward']=build_shadow_forward(ns['worldcache_mini_train_dit_forward'],mode,probe)
    return ns['apply_worldcache'](Toy(),num_steps=20,ret_ratio=.3,rel_l1_thresh=1,probe_depth=1,osi_enabled=True).eval()


def equal_tree(a,b):
    if isinstance(a,torch.Tensor): assert torch.equal(a,b)
    elif isinstance(a,(list,tuple)):
        assert len(a)==len(b)
        for x,y in zip(a,b): equal_tree(x,y)
    else: assert a==b


@pytest.mark.parametrize('mode',['official','scalar','shrink'])
def test_same_state_truth_preserves_outputs_cache_anchors_and_deployment_counts(mode):
    plain=model(mode).eval();probe=ShadowProbe([8,9,10,11,12]);probe.begin_request('r')
    instrumented=shadow_model(mode,probe)
    counts=BlockCounts(instrumented.blocks,cache_model=instrumented)
    rng=torch.get_rng_state().clone()
    a=run(plain,12);b=run(instrumented,12)
    for x,y in zip(a,b): assert torch.equal(x,y)
    assert torch.equal(rng,torch.get_rng_state())
    for field in ['cnt','residual_cache','probe_residual_cache','residual_window',
                  'previous_input','previous_output','previous_internal_states','resume_flag']:
        equal_tree(getattr(plain,field),getattr(instrumented,field))
    if mode!='official':
        for x,y in zip(plain._w1_calibrators,instrumented._w1_calibrators): assert x.receipt()==y.receipt()
    assert probe.records and all(r['request']=='r' for r in probe.records)
    assert counts.result()['denoiser_calls']==12
    assert counts.result()['skipped_deep_calls']>0
    for record in probe.records:
        i=record['call']-1
        x=torch.full((1,2,2,2,3),1+i*.001)
        for block in plain.blocks:x=block(x)
        expected=((b[i]-x).square().mean()/x.square().mean()).item()
        assert record['metrics']['velocity']['relative_mse']==pytest.approx(expected)
    counts.close()


def test_missing_request_refuses_diagnostics():
    probe=ShadowProbe([8]);m=shadow_model('official',probe)
    with pytest.raises(RuntimeError,match='begin_request'):run(m,1)


def test_shadow_restores_rng_and_registered_buffers_on_extra_deep_calls():
    class Stateful(Toy):
        pass
    class RandomBlock(torch.nn.Module):
        def __init__(self):
            super().__init__();self.register_buffer('visits',torch.zeros(()))
        def forward(self,x,**kwargs):
            self.visits.add_(1)
            return x*1.03+torch.rand_like(x)*.001
    plain=model('official').eval();probe=ShadowProbe([8,9,10,11,12]);probe.begin_request('r')
    observed=shadow_model('official',probe)
    plain.blocks[1]=RandomBlock().eval();observed.blocks[1]=RandomBlock().eval()
    torch.manual_seed(123);a=run(plain,12);after=torch.get_rng_state().clone()
    torch.manual_seed(123);b=run(observed,12)
    assert torch.equal(after,torch.get_rng_state())
    assert torch.equal(plain.blocks[1].visits,observed.blocks[1].visits)
    for x,y in zip(a,b): assert torch.equal(x,y)
    assert probe.records
