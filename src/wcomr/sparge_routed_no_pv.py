"""Pinned upstream fused pooling/selection/quantization, paired no-PV controls."""
from .sparge_no_pv import _invoke, prepare_inputs


def routed_invoke(packed, router, make_lut, kernel, sim, cdf, force_full=False):
    import torch
    q, k = packed['q'], packed['k']
    mask, qi, qs, ki, ks = router(q, k, k.mean(dim=-2, keepdim=True), is_causal=False,
                                 BLKQ=128, BLKK=64, simthreshd1=sim, cdfthreshd=cdf,
                                 topk=None, return_lut=False, attention_sink=False)
    if mask.dtype != torch.bool or mask.shape != packed['mask'].shape or mask.device != q.device:
        raise ValueError('Routed block map contract differs')
    if not bool(mask.any(-1).all().item()):
        raise ValueError('Routed empty query row refused')
    selected = float(mask.float().mean().item())
    # Both paths run identical routing/quantization. Only executed QK blocks
    # differ; force_full is a cost control, never a deployment optimization.
    effective = torch.ones_like(mask) if force_full else mask.contiguous()
    packed = dict(packed, mask=effective)
    output = _invoke(packed, lambda *_: (qi, qs, ki, ks), make_lut, kernel)
    return output, {'selected_fraction': selected, 'executed_fraction': 1.0 if force_full else selected}


def routed_no_pv(q, k, v, full_mask, sim, cdf, force_full=False):
    import torch
    if q.device.type != 'cuda' or torch.cuda.get_device_capability(q.device) != (8, 6):
        raise ValueError('Actual sm86 QKV required')
    packed = prepare_inputs(q, k, v, full_mask)
    from spas_sage_attn import _qattn
    from spas_sage_attn.utils import get_block_map_meansim_fuse_quant, block_map_lut_triton
    return routed_invoke(packed, get_block_map_meansim_fuse_quant, block_map_lut_triton,
                         _qattn.qk_int8_sv_f16_accum_f16_block_sparse_attn_inst_buf,
                         sim, cdf, force_full)
