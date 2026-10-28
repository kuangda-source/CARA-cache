"""Offline Q0 wire format and C readout adapter; no deployment installation.

Each token has independent 128-channel groups. Scales are little-endian FP32,
rounding is ties-to-even, signed codes use symmetric [-7,7]/[-127,127].
Tail channels and 64-byte block alignment are physically stored and counted.
No teacher, model conversion, source-cache mutation, or persistent raw shadow.
"""
import math
import struct
from dataclasses import dataclass

import torch

GROUP = 128
ALIGN = 64
HEADER = struct.Struct('<8sBBBBHH5IQQQ4x')
PAIR_HEADER = struct.Struct('<8sBB6xQQ32x')
DTYPES = (torch.float16, torch.bfloat16, torch.float32)


def aligned(n):
    return (n + ALIGN - 1) // ALIGN * ALIGN


def _shape(shape):
    if not 1 <= len(shape) <= 5 or any(type(n) is not int or n <= 0 or n >= 2**32 for n in shape):
        raise ValueError('Positive <=5D tensor with channel-last coordinates required')
    return math.prod(shape[:-1]), shape[-1]


def encode_tensor(value, bits, *, chunk_tokens=256):
    if bits not in (4, 8) or value.dtype not in DTYPES or value.device.type != 'cpu':
        raise ValueError('CPU FP16/BF16/FP32 and INT4/INT8 required')
    if chunk_tokens <= 0:
        raise ValueError('Positive streaming bound required')
    shape = tuple(value.shape)
    tokens, channels = _shape(shape)
    per_token = (channels + GROUP - 1) // GROUP
    groups = tokens * per_token
    scale_bytes = groups * 4
    payload_bytes = groups * GROUP * bits // 8
    offset = HEADER.size + aligned(scale_bytes)
    blob = bytearray(offset + aligned(payload_bytes))
    HEADER.pack_into(blob, 0, b'SQTENS01', 1, bits, DTYPES.index(value.dtype), len(shape), GROUP, 0,
                     *(shape + (0,) * (5 - len(shape))), value.numel(), groups, offset)
    rows = value.reshape(tokens, channels)
    qmax = 2**(bits-1)-1
    for lo in range(0, tokens, chunk_tokens):
        x = rows[lo:lo+chunk_tokens].float()
        if not torch.isfinite(x).all():
            raise ValueError('Nonfinite cache refused')
        # Tail zeros affect neither absmax nor the valid channels.
        x = torch.nn.functional.pad(x, (0, per_token*GROUP-channels)).reshape(-1, GROUP)
        maximum = x.abs().amax(dim=-1)
        scales = maximum / qmax
        scales = torch.where(maximum == 0, torch.ones_like(scales), scales)
        if not torch.isfinite(scales).all() or not (scales > 0).all():
            raise ValueError('Unrepresentable FP32 scale')
        codes = (x / scales[:, None]).round().clamp(-qmax, qmax).to(torch.int8).reshape(-1)
        g0 = lo * per_token
        sb = scales.numpy().astype('<f4', copy=False).tobytes()
        blob[HEADER.size+g0*4:HEADER.size+g0*4+len(sb)] = sb
        if bits == 4:
            nibbles = codes.to(torch.uint8) & 15
            packed = nibbles[0::2] | (nibbles[1::2] << 4)
        else:
            packed = codes.view(torch.uint8)
        pb = packed.numpy().tobytes()
        at = offset + g0*GROUP*bits//8
        blob[at:at+len(pb)] = pb
    return bytes(blob)


def tensor_info(blob):
    if len(blob) < HEADER.size:
        raise ValueError('Truncated tensor header')
    h = HEADER.unpack_from(blob)
    magic, version, bits, dtype, ndim, group, flags = h[:7]
    shape = tuple(h[7:12][:ndim])
    n, groups, offset = h[12:]
    if magic != b'SQTENS01' or version != 1 or bits not in (4, 8) or dtype >= len(DTYPES) or group != GROUP or flags:
        raise ValueError('Unknown codec format')
    tokens, channels = _shape(shape)
    if any(h[7:12][ndim:]) or n != math.prod(shape) or groups != tokens*((channels+GROUP-1)//GROUP):
        raise ValueError('Shape/count mismatch')
    scale_bytes = groups*4
    payload_bytes = groups*GROUP*bits//8
    if offset != HEADER.size+aligned(scale_bytes) or len(blob) != offset+aligned(payload_bytes):
        raise ValueError('Invalid packed byte extent')
    if any(blob[HEADER.size+scale_bytes:offset]) or any(blob[offset+payload_bytes:]):
        raise ValueError('Nonzero alignment padding')
    return dict(shape=list(shape), dtype=str(DTYPES[dtype]), dtype_id=dtype, bits=bits,
                group_channels=GROUP, group_count=groups, tokens=tokens, channels=channels,
                tail_channels_per_token=(-channels) % GROUP,
                scale_bytes=scale_bytes, payload_bytes=payload_bytes, header_bytes=HEADER.size,
                padding_bytes=len(blob)-HEADER.size-scale_bytes-payload_bytes,
                alignment_bytes=ALIGN, actual_bytes=len(blob), payload_offset=offset)


def decode_tensor(blob, *, chunk_tokens=256):
    info = tensor_info(blob)
    tokens, channels = info['tokens'], info['channels']
    per_token = (channels+GROUP-1)//GROUP
    result = torch.empty((tokens, channels), dtype=DTYPES[info['dtype_id']])
    for lo in range(0, tokens, chunk_tokens):
        nt = min(chunk_tokens, tokens-lo)
        g0, ng = lo*per_token, nt*per_token
        scale_view = bytearray(blob[HEADER.size+4*g0:HEADER.size+4*(g0+ng)])
        scales = torch.frombuffer(scale_view, dtype=torch.float32)
        if not torch.isfinite(scales).all() or not (scales > 0).all():
            raise ValueError('Invalid packed scale')
        at = info['payload_offset']+g0*GROUP*info['bits']//8
        codes = torch.frombuffer(bytearray(blob[at:at+ng*GROUP*info['bits']//8]), dtype=torch.uint8)
        if info['bits'] == 4:
            q = torch.stack((codes & 15, codes >> 4), dim=-1).reshape(-1).to(torch.int16)
            q = torch.where(q >= 8, q-16, q)
        else:
            q = codes.view(torch.int8)
        if (q == -(2**(info['bits']-1))).any():
            raise ValueError('Unused negative code refused')
        x = (q.reshape(ng, GROUP).float()*scales[:, None]).reshape(nt, per_token*GROUP)
        if channels % GROUP and (x[:, channels:] != 0).any():
            raise ValueError('Nonzero tail channel padding')
        result[lo:lo+nt] = x[:, :channels]
    return result.reshape(info['shape'])


@dataclass(frozen=True)
class PackedPair:
    wire: bytes

    def components(self):
        if len(self.wire) < PAIR_HEADER.size:
            raise ValueError('Truncated pair')
        magic, basis, dtype, a, b = PAIR_HEADER.unpack_from(self.wire)
        if magic != b'SQPAIR01' or basis not in (0, 1) or dtype >= len(DTYPES) or len(self.wire) != PAIR_HEADER.size+a+b:
            raise ValueError('Invalid pair header')
        c0 = self.wire[PAIR_HEADER.size:PAIR_HEADER.size+a]
        c1 = self.wire[PAIR_HEADER.size+a:]
        if tensor_info(c0)['shape'] != tensor_info(c1)['shape']:
            raise ValueError('Pair shape mismatch')
        return basis, DTYPES[dtype], c0, c1

    def info(self):
        basis, dtype, c0, c1 = self.components()
        return dict(basis='I' if basis == 0 else 'M', original_dtype=str(dtype),
                    pair_header_bytes=PAIR_HEADER.size, actual_bytes=len(self.wire),
                    components=[tensor_info(c0), tensor_info(c1)])

    def decode(self):
        basis, dtype, c0, c1 = self.components()
        a, b = decode_tensor(c0), decode_tensor(c1)
        if basis == 1:
            return (a + .5*b).to(dtype), (a - .5*b).to(dtype)
        return a.to(dtype), b.to(dtype)


def encode_pair(c, u, *, basis, bits):
    if c.shape != u.shape or c.dtype != u.dtype or c.dtype not in DTYPES or basis not in ('I', 'M') or tuple(bits) not in ((8,8), (4,8), (8,4)):
        raise ValueError('Aligned CFG cache pair and registered representation/rate required')
    # FP32 transform includes its own measurable rounding; no teacher input.
    cf, uf = c.float(), u.float()
    values = (cf, uf) if basis == 'I' else ((cf+uf)*.5, cf-uf)
    blobs = [encode_tensor(v, b) for v, b in zip(values, bits)]
    header = PAIR_HEADER.pack(b'SQPAIR01', int(basis == 'M'), DTYPES.index(c.dtype), *(len(b) for b in blobs))
    return PackedPair(header+b''.join(blobs))


def transform_roundtrip(c, u):
    m, delta = (c.float()+u.float())*.5, c.float()-u.float()
    return (m+.5*delta).to(c.dtype), (m-.5*delta).to(u.dtype)


def storage_bytes(value):
    """Count actual unique storage capacity, including aliases and stale entries."""
    seen = {}
    def visit(x):
        if isinstance(x, torch.Tensor):
            s = x.untyped_storage()
            seen[(str(x.device), s.data_ptr(), s.nbytes())] = s.nbytes()
        elif isinstance(x, dict):
            for v in x.values(): visit(v)
        elif isinstance(x, (list, tuple)):
            for v in x: visit(v)
    visit(value)
    return sum(seen.values())


def packed_source(source, *, basis, bits):
    """Offline adapter covers every r-window slot and residual_cache alias.

    Returned decoded view is ephemeral. Original source is an offline teacher;
    this function is not a claim of reduced deployed persistent/peak memory.
    """
    if len(source) != 2 or len(source[0]['residual_window']) != len(source[1]['residual_window']):
        raise ValueError('Complete aligned branch windows required')
    pairs, keys, slots = [], {}, []
    def key(t):
        s = t.untyped_storage()
        return (s.data_ptr(), t.storage_offset(), tuple(t.shape), tuple(t.stride()), t.dtype)
    originals = list(zip(source[0]['residual_window'], source[1]['residual_window']))
    originals.append((source[0]['residual'], source[1]['residual']))
    for c, u in originals:
        identity = (key(c), key(u))
        if identity not in keys:
            keys[identity] = len(pairs)
            pairs.append(encode_pair(c, u, basis=basis, bits=bits))
        slots.append(keys[identity])
    decoded = [p.decode() for p in pairs]
    view = [dict(s) for s in source]
    for branch in (0, 1):
        view[branch]['residual_window'] = [decoded[i][branch] for i in slots[:-1]]
        view[branch]['residual'] = decoded[slots[-1]][branch]
    # A real descriptor table: counts and each window/cache alias, aligned to 64.
    descriptor = struct.pack('<8sII', b'SQWIN001', len(pairs), len(slots))
    descriptor += struct.pack('<'+'I'*len(slots), *slots)
    descriptor += bytes(aligned(len(descriptor))-len(descriptor))
    encoded_bytes = len(descriptor)+sum(len(p.wire) for p in pairs)
    raw = storage_bytes(originals)
    return view, dict(actual_packed_bytes=encoded_bytes, pair_bytes=sum(len(p.wire) for p in pairs),
                      window_descriptor_bytes=len(descriptor), raw_r_unique_storage_bytes=raw,
                      slot_to_pair=slots, unique_pairs=len(pairs),
                      window_slots=len(slots)-1, persistent_deployment_measured=False), pairs


def readout_C(kernel, *, source, current, pair_inputs, basis, bits):
    view, info, _ = packed_source(source, basis=basis, bits=bits)
    outputs = kernel.run('C', source=view, current=current, pair_inputs=pair_inputs)[0]
    return outputs, info


def leave_one_prompt_out(rows, *, basis, rate, objective):
    """Select one global direction on training prompt, evaluate held-out prompt.

    Input scores must already be measured actual C outputs, never raw MSE.
    State identities and actual bytes must match across competing directions.
    """
    if basis not in ('I','M') or rate not in ('R16','R12') or objective not in ('BR','CFG'):
        raise ValueError('Registered selection cell required')
    selected = [r for r in rows if r['basis'] == basis and r['rate'] == rate]
    prompts = sorted({r['prompt'] for r in selected})
    directions = [(8,8)] if rate == 'R16' else [(4,8),(8,4)]
    if len(prompts) != 2 or any(r.get('coordinate') != 'ACTUAL_C_POST_RF' for r in selected):
        raise ValueError('Two prompts and actual C output evidence required')
    table = {}
    for r in selected:
        k = (r['prompt'], r['state'], tuple(r['bits']))
        if k in table or tuple(r['bits']) not in directions or not math.isfinite(r[objective]) or r[objective] < 0:
            raise ValueError('Duplicate or invalid direction evidence')
        table[k] = r
    folds = []
    for held in prompts:
        train = next(p for p in prompts if p != held)
        states = {p:sorted({s for p0,s,b in table if p0 == p}) for p in prompts}
        for p in prompts:
            for s in states[p]:
                rs = [table.get((p,s,d)) for d in directions]
                if any(r is None for r in rs) or len({r['actual_bytes'] for r in rs}) != 1:
                    raise ValueError('Missing state or unequal actual bytes')
        scores = {d:sum(table[(train,s,d)][objective] for s in states[train])/len(states[train]) for d in directions}
        best = min(directions, key=lambda d:(scores[d],d))
        folds.append(dict(training_prompt=train, heldout_prompt=held, bits=list(best),
                          heldout_mean=sum(table[(held,s,best)][objective] for s in states[held])/len(states[held]),
                          training_scores={str(d):v for d,v in scores.items()}))
    return folds
