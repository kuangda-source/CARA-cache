import hashlib
import tempfile
from pathlib import Path
from unittest import TestCase
import torch
from wcomr.wc_qkv_snapshot import dump_qkv


def test_noncontiguous_bf16_snapshot_roundtrip_preserves_inputs_rng_and_bytes():
    q = torch.arange(48, dtype=torch.bfloat16).reshape(1, 2, 4, 6).transpose(1, 2)
    rng, version, original = torch.random.get_rng_state(), q._version, q.clone()
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'qkv.pt'
        result = dump_qkv((q, q + 1, q + 2), target, list(q.shape), str(q.dtype))
        stored = torch.load(target, weights_only=True)
        assert torch.equal(stored['q'], original) and stored['q'].is_contiguous()
        assert result['tensors']['q']['stride'] == list(q.stride())
        raw = hashlib.sha256(memoryview(original.contiguous().reshape(-1).view(torch.uint8).numpy())).hexdigest()
        assert raw == result['tensors']['q']['raw_sha256']
        assert hashlib.sha256(target.read_bytes()).hexdigest() == result['sha256']
        with TestCase().assertRaisesRegex(ValueError, 'fresh snapshot'):
            dump_qkv((q, q, q), target, list(q.shape), str(q.dtype))
    assert q._version == version and torch.equal(q, original)
    assert torch.equal(rng, torch.random.get_rng_state())


def test_invalid_shape_and_nonfinite_refuse_snapshot():
    q = torch.zeros(1, 4, 2, 6, dtype=torch.bfloat16)
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'qkv.pt'
        with TestCase().assertRaisesRegex(ValueError, 'shape/dtype'):
            dump_qkv((q, q, q), target, [1, 2, 4, 6], str(q.dtype))
        assert not target.exists()
        q[0, 0, 0, 0] = float('nan')
        with TestCase().assertRaisesRegex(ValueError, 'Nonfinite'):
            dump_qkv((q, q, q), target, list(q.shape), str(q.dtype))
        assert not target.exists()
