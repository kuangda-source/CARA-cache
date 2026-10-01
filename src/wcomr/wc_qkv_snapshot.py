"""CPU-owned QKV dump; input identity/version/RNG are preserved."""
import hashlib
from pathlib import Path
import torch


def dump_qkv(args, target, expected_shape, expected_dtype):
    target = Path(target)
    if len(args) != 3 or target.exists():
        raise ValueError('Expected three QKV tensors and a fresh snapshot path')
    cpu_rng = torch.random.get_rng_state()
    cuda_rng = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else []
    tensors, meta = {}, {}
    for name, value in zip(['q', 'k', 'v'], args):
        if list(value.shape) != expected_shape or str(value.dtype) != expected_dtype:
            raise ValueError('Actual QKV shape/dtype differs from scope')
        version = None if value.is_inference() else value._version
        cpu = value.detach().to('cpu', copy=True).contiguous()
        if not bool(torch.isfinite(cpu).all()):
            raise ValueError('Nonfinite actual QKV')
        digest = hashlib.sha256(memoryview(cpu.reshape(-1).view(torch.uint8).numpy())).hexdigest()
        meta[name] = {'shape': list(value.shape), 'dtype': str(value.dtype), 'stride': list(value.stride()),
                      'finite': True, 'raw_sha256': digest}
        assert version is None or value._version == version, 'Observer mutated input'
        tensors[name] = cpu
    torch.save(tensors, target)
    assert torch.equal(cpu_rng, torch.random.get_rng_state()), 'Observer changed CPU RNG'
    if cuda_rng:
        assert all(torch.equal(x, y) for x, y in zip(cuda_rng, torch.cuda.get_rng_state_all())), 'Observer changed CUDA RNG'
    digest = hashlib.sha256()
    with target.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            digest.update(chunk)
    return {'path': str(target), 'sha256': digest.hexdigest(), 'bytes': target.stat().st_size, 'tensors': meta,
            'point': 'actual attn_op input after QK norm and self RoPE; NHD', 'rng_preserved': True}
