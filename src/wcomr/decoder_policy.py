"""A scoped cuDNN decode policy and read-only tokenizer identity witnesses."""
from contextlib import contextmanager
import hashlib
import json
import torch
from .stage_witness import witness


def backend_flags():
    return {'cudnn_enabled':torch.backends.cudnn.enabled,
            'cudnn_benchmark':torch.backends.cudnn.benchmark,
            'cudnn_deterministic':torch.backends.cudnn.deterministic,
            'cudnn_allow_tf32':torch.backends.cudnn.allow_tf32,
            'matmul_allow_tf32':torch.backends.cuda.matmul.allow_tf32,
            'deterministic_algorithms':torch.are_deterministic_algorithms_enabled()}


@contextmanager
def decode_policy(enabled):
    """Change cuDNN selection only within decode; propagate original exceptions."""
    before=backend_flags()
    try:
        if enabled:
            with torch.backends.cudnn.flags(enabled=before['cudnn_enabled'], benchmark=False,
                    deterministic=True, allow_tf32=before['cudnn_allow_tf32']):
                yield backend_flags()
        else:
            yield backend_flags()
    finally:
        assert backend_flags()==before, 'Decoder policy leaked backend flags'


def _plain(value):
    if isinstance(value,torch.Tensor):return witness(value)
    if isinstance(value,(list,tuple)):return [_plain(x) for x in value]
    if isinstance(value,dict):return {str(k):_plain(v) for k,v in value.items()}
    if value is None or isinstance(value,(int,float,str,bool)):return value
    raise TypeError('Unsupported decoder state: '+type(value).__name__)


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def module_identity(module):
    """Hash named weights/buffers without retaining or changing live tensors."""
    cpu=torch.random.get_rng_state()
    cuda=torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else []
    tensors={'parameters':{k:witness(v) for k,v in module.named_parameters()},
             'buffers':{k:witness(v) for k,v in module.named_buffers()}}
    training={k:v.training for k,v in module.named_modules()}
    assert torch.equal(cpu,torch.random.get_rng_state())
    if cuda:assert all(torch.equal(a,b) for a,b in zip(cuda,torch.cuda.get_rng_state_all()))
    return {'parameters_sha256':_hash(tensors['parameters']),
            'buffers_sha256':_hash(tensors['buffers']),
            'parameter_tensors':len(tensors['parameters']),
            'buffer_tensors':len(tensors['buffers']),
            'training_flags_sha256':_hash(training),
            'training_modules':sum(training.values()),'modules':len(training)}


def tokenizer_identity(tokenizer):
    vae=tokenizer.model
    result=module_identity(vae.model)
    result['normalization']={name:_plain(getattr(vae,name)) for name in
                            ['scale','img_mean','img_std','video_mean','video_std']}
    result['settings']={name:str(getattr(vae,name)) for name in
        ['dtype','is_amp','is_parallel','temporal_window','context_parallel_enabled','benchmark']}
    result['interface']={name:getattr(tokenizer,name) for name in
                        ['keep_decoder_cache','keep_encoder_cache','chunk_duration','cp_initialized']}
    # These caches belong to the original decoder and may legitimately clear.
    # They are inspected separately from immutable weight/normalization identity.
    result['cache']={name:_plain(getattr(vae.model,name)) for name in
                    ['_feat_map','_conv_idx','_enc_feat_map','_enc_conv_idx']}
    return result


def compare_decoder_identity(before, after):
    return {key:before[key]==after[key] for key in before if key!='cache'}
