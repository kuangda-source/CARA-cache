import torch
from unittest import TestCase
from wcomr.sparge_no_pv import prepare_inputs
from wcomr.sparge_routed_no_pv import routed_invoke


def test_paired_routing_full_and_sparse_change_only_executed_map():
    q = torch.arange(256 * 16 * 128, dtype=torch.float32).remainder(256).to(torch.bfloat16).reshape(1, 256, 16, 128)
    full = torch.ones(1, 16, 2, 4, dtype=torch.bool)
    mask = full.clone(); mask[..., 2:] = False
    packed = prepare_inputs(q, q + 1, q + 2, full)
    qi, ki = packed['q'].to(torch.int8), packed['k'].to(torch.int8)
    qs, ks = torch.ones(1), torch.ones(1) * 2
    masks, quant_args, routes = [], [], []
    def router(qh, kh, km, **kw):
        assert torch.equal(km, kh.mean(-2, keepdim=True))
        assert kw == dict(is_causal=False, BLKQ=128, BLKK=64, simthreshd1=.6, cdfthreshd=.98,
                          topk=None, return_lut=False, attention_sink=False)
        routes.append(kw)
        return mask, qi, qs, ki, ks
    def lut(m):
        masks.append(m.clone())
        return m.to(torch.int32), m.sum(-1).to(torch.int32)
    def kernel(*args):
        assert len(args) == 12 and args[8:11] == (1, 0, 1)
        quant_args.append((args[0], args[1], args[6], args[7]))
        args[3].copy_(packed['q'])
    rng, version = torch.random.get_rng_state(), q._version
    a, am = routed_invoke(packed, router, lut, kernel, .6, .98, True)
    b, bm = routed_invoke(packed, router, lut, kernel, .6, .98, False)
    assert len(routes) == 2 and all(x is y for x, y in zip(*quant_args))
    assert torch.equal(masks[0], full) and torch.equal(masks[1], mask)
    assert am == {'selected_fraction': .5, 'executed_fraction': 1.0}
    assert bm == {'selected_fraction': .5, 'executed_fraction': .5}
    assert torch.equal(a, b) and a.shape == (1, 256, 2048)
    assert torch.equal(rng, torch.random.get_rng_state()) and q._version == version


def test_routed_invalid_map_refused_before_kernel():
    q = torch.zeros(1, 128, 16, 128, dtype=torch.bfloat16)
    full = torch.ones(1, 16, 1, 2, dtype=torch.bool)
    packed = prepare_inputs(q, q, q, full)
    def forbidden(*args):
        raise AssertionError('Kernel must not execute')
    for mask in [torch.zeros_like(full), full.to(torch.int32), full[..., :1]]:
        router = lambda *a, m=mask, **kw: (m, None, None, None, None)
        with TestCase().assertRaises(ValueError):
            routed_invoke(packed, router, forbidden, forbidden, .6, .98)
