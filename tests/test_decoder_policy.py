import types
import pytest
import torch
from wcomr.decoder_policy import backend_flags,decode_policy,module_identity,tokenizer_identity,compare_decoder_identity


@pytest.mark.parametrize('enabled',[False,True])
@pytest.mark.parametrize('exception',[False,True])
def test_scoped_policy_restores_flags_rng_and_preserves_tensors(enabled,exception):
    original=backend_flags();x=torch.randn(3);rng=torch.random.get_rng_state().clone()
    def decode(value):
        if exception:raise ValueError('original decode error')
        return value
    try:
        with decode_policy(enabled) as active:
            assert active['cudnn_allow_tf32']==original['cudnn_allow_tf32']
            assert active['matmul_allow_tf32']==original['matmul_allow_tf32']
            if enabled:
                assert not active['cudnn_benchmark'] and active['cudnn_deterministic']
            else:assert active==original
            result=decode(x)
            assert result is x
    except ValueError as e:
        assert exception and str(e)=='original decode error'
    assert backend_flags()==original and torch.equal(rng,torch.random.get_rng_state())


def test_fingerprint_preserves_registered_state_and_detects_changes():
    m=torch.nn.Linear(2,3);m.register_buffer('state',torch.ones(2))
    rng=torch.random.get_rng_state().clone();before={k:v.clone() for k,v in m.state_dict().items()}
    a=module_identity(m);b=module_identity(m)
    assert a==b and torch.equal(rng,torch.random.get_rng_state())
    assert all(torch.equal(v,m.state_dict()[k]) for k,v in before.items())
    m.eval();assert module_identity(m)['training_flags_sha256']!=a['training_flags_sha256']
    with torch.no_grad():m.weight.add_(1)
    assert module_identity(m)['parameters_sha256']!=a['parameters_sha256']
    m.state.add_(1);assert module_identity(m)['buffers_sha256']!=a['buffers_sha256']


def test_normalization_identity_separates_mutable_decoder_cache():
    m=torch.nn.Linear(1,1);m._feat_map=[None];m._conv_idx=[0];m._enc_feat_map=[None];m._enc_conv_idx=[0]
    vae=types.SimpleNamespace(model=m,scale=[torch.tensor(1),torch.tensor(2)],img_mean=torch.zeros(1),
        img_std=torch.ones(1),video_mean=torch.zeros(1),video_std=torch.ones(1),dtype=torch.bfloat16,
        is_amp=False,is_parallel=False,temporal_window=4,context_parallel_enabled=False,benchmark=False)
    tok=types.SimpleNamespace(model=vae,keep_decoder_cache=False,keep_encoder_cache=False,chunk_duration=81,cp_initialized=False)
    a=tokenizer_identity(tok);m._feat_map=[torch.ones(1)];b=tokenizer_identity(tok)
    assert a['cache']!=b['cache'] and all(compare_decoder_identity(a,b).values())
    vae.scale[0].add_(1);assert not compare_decoder_identity(b,tokenizer_identity(tok))['normalization']


def test_policy_summary_rejects_changed_latent_flags_and_decoder_state():
    import copy
    from wcomr.decoder_policy_summary import summarize_policy
    flags=backend_flags();inside=dict(flags,cudnn_benchmark=False,cudnn_deterministic=True)
    call={'before':{'parameters_sha256':'p','cache':[]},'after':{'parameters_sha256':'p','cache':[]},
          'flags_before':flags,'flags_after':flags,'flags_inside':inside}
    a={'status':'STAGE_WITNESS_ACCEPTED_SINGLE_FRESH_PROCESS','decoder_policy':{'enabled':True},'decoder_calls':[call],
       'forward_output_sha256':['f']*72,'decoded_rgb':[{}]*93,'pid':1,'source_sha256':{},'decoder_checkpoint':{},
       'block_counts':{},'trace':[],'cache_end_sha256':'c','sampling':{},'sample':{},'runtime_identity':{},'encoding':[],
       'events':[{'stage':'sample_return','value':'x'},{'stage':'decode_input','value':'x'},{'stage':'decode_output','value':'y'}],
       'video_sha256':'v'}
    b=copy.deepcopy(a);b['pid']=2;reference=copy.deepcopy(a)
    assert summarize_policy(a,b,reference)['status']=='LOCAL_DECODE_POLICY_REPRODUCTION_PASS'
    b['events'][-1]['value']='other'
    assert summarize_policy(a,b,reference)['status']=='LOCAL_DECODE_POLICY_REPRODUCTION_NOT_ESTABLISHED'
    b=copy.deepcopy(a);b['pid']=2;b['decoder_calls'][0]['flags_inside']['matmul_allow_tf32']=not flags['matmul_allow_tf32']
    with pytest.raises(AssertionError):summarize_policy(a,b,reference)
    b=copy.deepcopy(a);b['pid']=2;b['decoder_calls'][0]['before']['parameters_sha256']='changed'
    with pytest.raises(AssertionError):summarize_policy(a,b,reference)
    reference['events'][0]['value']='changed'
    with pytest.raises(AssertionError):summarize_policy(a,dict(a,pid=2),reference)
