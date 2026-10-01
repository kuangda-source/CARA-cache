"""Experimental Ampere no-PV entry; not installed in the Cosmos runner.

The two mask arms share packing, quantization, scale and the upstream PV-mode-0
binding. CUDA execution remains gated by external admission and budget control.
"""
import math


def prepare_inputs(q, k, v, block_mask):
    """Validate and pack NHD inputs. CPU calls test this contract, not the kernel."""
    import torch
    if q.ndim != 4 or q.shape != k.shape or q.shape != v.shape:
        raise ValueError('self-attention Q/K/V must share a four-dimensional NHD shape')
    b, n, h, d = q.shape
    if b != 1 or h != 16 or d != 128 or n < 128 or n % 128:
        raise ValueError('initial contract requires B1/H16/D128 and N divisible by128')
    if q.dtype not in [torch.bfloat16, torch.float16] or q.dtype != k.dtype or q.dtype != v.dtype:
        raise ValueError('matched BF16 or FP16 Q/K/V required')
    if not (q.device == k.device == v.device == block_mask.device):
        raise ValueError('inputs and mask must share one device')
    if block_mask.dtype != torch.bool or list(block_mask.shape) != [b, h, n // 128, n // 64]:
        raise ValueError('explicit boolean block mask has wrong dtype or Ampere block shape')
    if not bool(block_mask.any(dim=-1).all().item()):
        raise ValueError('every query block must retain at least one key block')
    if any(x.requires_grad for x in [q, k, v]):
        raise ValueError('inference-only contract')
    if not all(bool(torch.isfinite(x).all().item()) for x in [q, k, v]):
        raise ValueError('nonfinite Q/K/V')
    return {
        'q': q.transpose(1, 2).contiguous(),
        'k': k.transpose(1, 2).contiguous(),
        'v': v.transpose(1, 2).contiguous().to(torch.float16),
        'mask': block_mask.contiguous(),
        'scale': 1.0 / math.sqrt(d),
    }


def _invoke(packed, quantize, make_lut, kernel):
    """Binding contract split out for CPU spy tests; it does not accept a PV threshold."""
    import torch
    q, k, v = packed['q'], packed['k'], packed['v']
    km = k.mean(dim=-2, keepdim=True)
    q_int8, q_scale, k_int8, k_scale = quantize(q, k, km, 128, 64)
    lut, valid = make_lut(packed['mask'])
    out = torch.empty_like(q)
    # HND layout=1, noncausal=0, per-block QK quantization=1. This upstream
    # binding has no PV threshold and dispatches PVThresholdMode::kNone.
    kernel(q_int8, k_int8, v, out, lut, valid, q_scale, k_scale, 1, 0, 1, packed['scale'])
    if not bool(torch.isfinite(out).all().item()):
        raise ValueError('nonfinite kernel output')
    b, h, n, d = out.shape
    return out.transpose(1, 2).reshape(b, n, h * d)


def block_sparse_no_pv(q, k, v, block_mask):
    """Run the actual upstream sm86 binding. Full-QK and sparse-QK use this same path.

    Includes validation/synchronization, packing, quantization, LUT creation and
    output flattening. These costs must remain in the first end-to-end timing.
    """
    import torch
    if q.device.type != 'cuda' or torch.cuda.get_device_capability(q.device) != (8, 6):
        raise ValueError('actual sm86 CUDA tensors required; CPU is not kernel execution')
    packed = prepare_inputs(q, k, v, block_mask)
    from spas_sage_attn import _qattn
    from spas_sage_attn.utils import get_vanilla_qk_quant, block_map_lut_triton
    return _invoke(packed, get_vanilla_qk_quant, block_map_lut_triton,
                   _qattn.qk_int8_sv_f16_accum_f16_block_sparse_attn_inst_buf)
