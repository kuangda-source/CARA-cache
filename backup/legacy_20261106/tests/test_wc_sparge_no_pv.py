"""CPU packing/dispatch controls, not CUDA kernel numerics or speed."""
import math
from unittest import TestCase
import torch
from wcomr.sparge_no_pv import prepare_inputs, _invoke, block_sparse_no_pv


def inputs():
    q = torch.arange(256 * 16 * 128, dtype=torch.float32).remainder(256).to(torch.bfloat16).reshape(1, 256, 16, 128)
    return q, q + 1, q + 2, torch.ones(1, 16, 2, 4, dtype=torch.bool)


def test_packing_and_no_pv_binding_preserve_projection_layout():
    q, k, v, mask = inputs()
    packed = prepare_inputs(q, k, v, mask)
    assert torch.equal(packed['q'], q.transpose(1, 2))
    assert packed['q'].is_contiguous() and packed['v'].dtype == torch.float16
    calls = []
    def quant(qh, kh, km, blockq, blockk):
        assert (blockq, blockk) == (128, 64)
        assert torch.equal(km, kh.mean(dim=-2, keepdim=True))
        return qh.to(torch.int8), torch.ones(1), kh.to(torch.int8), torch.ones(1)
    def lut(m):
        assert torch.equal(m, mask)
        return torch.zeros_like(m, dtype=torch.int32), m.sum(-1).to(torch.int32)
    def kernel(*args):
        calls.append(args)
        args[3].copy_(packed['q'])
    out = _invoke(packed, quant, lut, kernel)
    assert len(calls[0]) == 12  # No PV threshold argument.
    assert calls[0][8:11] == (1, 0, 1)
    assert calls[0][11] == 1 / math.sqrt(128)
    assert out.dtype == q.dtype and out.shape == (1, 256, 2048)
    assert torch.equal(out, q.reshape(1, 256, 2048))


def test_invalid_mask_nonfinite_and_cpu_kernel_rejected():
    q, k, v, mask = inputs()
    mask[:, :, 0, :] = False
    with TestCase().assertRaisesRegex(ValueError, 'retain at least one'):
        prepare_inputs(q, k, v, mask)
    mask.fill_(True)
    with TestCase().assertRaisesRegex(ValueError, 'wrong dtype'):
        prepare_inputs(q, k, v, mask.to(torch.int32))
    q[0, 0, 0, 0] = float('nan')
    with TestCase().assertRaisesRegex(ValueError, 'nonfinite'):
        prepare_inputs(q, k, v, mask)
    with TestCase().assertRaisesRegex(ValueError, 'actual sm86'):
        block_sparse_no_pv(q, k, v, mask)


def test_nonfinite_binding_output_rejected():
    q, k, v, mask = inputs()
    packed = prepare_inputs(q, k, v, mask)
    def quant(*args):
        return packed['q'].to(torch.int8), torch.ones(1), packed['k'].to(torch.int8), torch.ones(1)
    def kernel(*args):
        args[3].fill_(float('nan'))
    with TestCase().assertRaisesRegex(ValueError, 'nonfinite kernel output'):
        _invoke(packed, quant, lambda m: (m, m.sum(-1)), kernel)
