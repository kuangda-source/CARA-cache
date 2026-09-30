import types
import numpy as np
import pytest
import torch
from wcomr.stage_witness import StageWitness, witness, compare_stages


def test_observers_preserve_identity_rng_buffers_and_restore_class_methods():
    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.register_buffer('counter', torch.tensor(0))
        def generate(self, x):
            self.counter.add_(1)
            return [x, x]
    m = Model(); x = torch.randn(2, 3)
    rng = torch.random.get_rng_state().clone(); version = x._version
    p = StageWitness(); p.wrap(m, 'generate', lambda a,k:p.record('in',a[0]), lambda r:p.record('out',r))
    result = m.generate(x)
    assert result[0] is x and result[1] is x
    assert m.counter.item() == 1 and x._version == version
    assert torch.equal(rng, torch.random.get_rng_state())
    p.close(); assert 'generate' not in vars(m)
    assert m.generate(x)[0] is x


def test_exception_and_none_preserve_semantics_and_original_module_alias():
    def f(x):
        if x is None: return None
        raise ValueError('original')
    module=types.SimpleNamespace(f=f); p=StageWitness()
    p.wrap(module,'f',after=lambda r:p.record('guardrail',r))
    assert module.f(None) is None
    with pytest.raises(ValueError,match='original'): module.f(1)
    p.close(); assert module.f is f
    assert p.events==[{'stage':'guardrail','value':{'kind':'None'}}]


def test_array_layout_hash_and_nonfinite_fail_closed():
    x=np.arange(12,dtype=np.uint8).reshape(3,4)[:,::2]; before=x.copy()
    assert witness(x)==witness(x.copy())
    assert np.array_equal(x,before)
    with pytest.raises(AssertionError,match='Nonfinite'): witness(torch.tensor(float('nan')))


def test_first_different_boundary_and_runtime_guard():
    base={key:[] for key in ['forward_output_sha256','block_counts','trace','cache_end_sha256','sampling','runtime_identity','encoding','decoded_rgb','video_sha256']}
    base['events']=[{'stage':'sample','value':1},{'stage':'decode_out','value':2}]
    changed=dict(base,events=[{'stage':'sample','value':1},{'stage':'decode_out','value':3}])
    result=compare_stages(base,changed)
    assert result['first_difference']=='decode_out' and result['previous_matching_boundary']=='sample'
    assert compare_stages(base,dict(base,runtime_identity=['changed']))['status']=='UPSTREAM_OR_RUNTIME_MISMATCH'
    assert compare_stages(base,base)['status']=='EXACT_PIPELINE_REPRODUCTION_TWO_FRESH_PROCESSES'


def test_inference_mode_tensors_are_readable_without_version_counter():
    with torch.inference_mode():
        x=torch.ones(2)
        p=StageWitness();p.record('sample',x)
        assert p.events[0]['value']['finite']


def test_call_context_wraps_only_original_call_and_restores_on_failure():
    from wcomr.decoder_policy import backend_flags,decode_policy
    original=backend_flags();observations=[]
    def decode(x):
        observations.append(('original',backend_flags()))
        if x is None:raise ValueError('original')
        return x
    module=types.SimpleNamespace(decode=decode);p=StageWitness()
    p.wrap(module,'decode',before=lambda a,k:observations.append(('before',backend_flags())),
           after=lambda r:observations.append(('after',backend_flags())),call_context=lambda:decode_policy(True))
    x=torch.ones(1);assert module.decode(x) is x
    assert observations[0][1]==original and observations[-1][1]==original
    assert observations[1][1]['cudnn_deterministic'] and not observations[1][1]['cudnn_benchmark']
    with pytest.raises(ValueError,match='original'):module.decode(None)
    assert backend_flags()==original
    p.close();assert module.decode is decode
