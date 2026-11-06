"""Isolated, causal shallow-probe features for the F exploration.

No teacher, selector, cache mutation or runtime forward installation occurs here.
The callback boundary precedes both the action decision and deep execution.
Spatial transforms use actual B,T,H,W,D geometry, never flattened token indices.
"""
from dataclasses import dataclass, asdict
import ast
import copy
import hashlib
import inspect
import math
import statistics
import time
from textwrap import dedent

VERSION = 'ISOLATED_SPECTRAL_PAID_PROBE_R1'
CHANNELS_2048 = tuple(range(0, 2048, 128))
FFT_RADIUS = 0.25  # cycles per spatial sample; same frozen filter on c/u/source
FIT_ADDITIONS = {
    'F_RAW_SUB': ('raw_sub_guided', 'raw_sub_cosine'),
    'F_HAAR': ('haar_detail_guided_fraction', 'haar_detail_cfg_cosine'),
    'F_FFT': ('fft_high_guided_fraction', 'fft_high_cfg_cosine'),
}


@dataclass(frozen=True)
class ProbeIdentity:
    request_id: str
    step: int
    source_kind: str
    source_birth: int
    true_D_birth: int
    current_tau: float
    source_tau: float
    true_D_tau: float
    geometry: tuple
    source_id: str

    def validate(self):
        if (not self.request_id or not self.source_id or self.source_kind not in ('D', 'P')
                or type(self.step) is not int or type(self.source_birth) is not int
                or not 1 <= self.true_D_birth <= self.source_birth < self.step
                or len(self.geometry) != 5 or any(type(x) is not int or x < 1 for x in self.geometry)
                or not all(math.isfinite(float(x)) for x in
                           (self.current_tau, self.source_tau, self.true_D_tau))):
            raise ValueError('Bound strictly-past working source and actual BTHWD/tau required')
        if self.source_kind == 'D' and self.source_birth != self.true_D_birth:
            raise ValueError('D work source and true D birth differ')


def channel_indices(width):
    """Fixed equal-stride channels; reduced fixtures use all available <=16."""
    if type(width) is not int or width < 1:
        raise ValueError('Positive feature width required')
    count = min(16, width)
    return tuple((i * width) // count for i in range(count))


def _torch():
    import torch
    return torch


def select_channels(x, indices=None):
    torch = _torch()
    if x.ndim != 5 or not x.is_floating_point():
        raise ValueError('An actual floating B,T,H,W,D probe is required')
    ids = channel_indices(x.shape[-1]) if indices is None else tuple(indices)
    if not ids or len(set(ids)) != len(ids) or any(type(i) is not int or not 0 <= i < x.shape[-1] for i in ids):
        raise ValueError('Unique valid fixed channel indices required')
    return x.index_select(-1, torch.tensor(ids, device=x.device)), ids


def causal_slice(original, probe, working_probe, *, cpu=False):
    """Current shallow residual and SAME working-source residual, selected first.

    Arithmetic preserves the runtime input dtype before float32 transform.
    No full-width float32 copy is needed. Saving on CPU is offline IO and is
    excluded only from the ONLINE feature timer, not the experiment GPU ledger.
    """
    if original.shape != probe.shape or working_probe.shape != probe.shape:
        raise ValueError('Current, input and source layouts must match')
    current, ids = select_channels(probe)
    base, _ = select_channels(original, ids)
    source, _ = select_channels(working_probe, ids)
    current = (current - base).detach().clone()
    source = source.detach().clone()
    if cpu:
        current, source = current.cpu(), source.cpu()
    return current, source, ids


def _spatial(x):
    return x.to(dtype=_torch().float32).permute(0, 1, 4, 2, 3).contiguous()


def _haar_axis(x, axis):
    """Orthogonal pairs plus one UNPADDED singleton scaling coefficient.

    For H=27: low=14 rows, high=13; the last row is untouched in low.
    No replicated/zero-padded sample is treated as an observed latent token.
    """
    torch = _torch()
    n = x.shape[axis]
    even = x.index_select(axis, torch.arange(0, n - 1, 2, device=x.device))
    odd = x.index_select(axis, torch.arange(1, n, 2, device=x.device))
    low, high = (even + odd) / math.sqrt(2.), (even - odd) / math.sqrt(2.)
    if n % 2:
        low = torch.cat((low, x.narrow(axis, n - 1, 1)), dim=axis)
    return low, high


def haar_bands(x):
    low_h, high_h = _haar_axis(x, -2)
    ll, lh = _haar_axis(low_h, -1)
    hl, hh = _haar_axis(high_h, -1)
    return ll, (lh, hl, hh)


def fft_bands(x):
    """rFFT with conjugate multiplicity, including odd/even/DC/Nyquist."""
    torch = _torch()
    h, w = x.shape[-2:]
    z = torch.fft.rfft2(x, dim=(-2, -1), norm='ortho')
    fy = torch.fft.fftfreq(h, device=x.device)
    fx = torch.fft.rfftfreq(w, device=x.device)
    low = fy[:, None].square() + fx[None, :].square() <= FFT_RADIUS ** 2
    multiplicity = torch.full((w // 2 + 1,), 2., device=x.device)
    multiplicity[0] = 1.
    if w % 2 == 0:
        multiplicity[-1] = 1.
    return z, low, multiplicity


def _energy(c, u, denominator, weights=None):
    torch = _torch()
    ec, eu = c.abs().square(), u.abs().square()
    cross = (c * u.conj()).real
    if weights is not None:
        ec, eu, cross = ec * weights, eu * weights, cross * weights
    ec, eu, cross = ec.sum() / denominator, eu.sum() / denominator, cross.sum() / denominator
    # Accumulate the guided vector directly: strong CFG cancellation can make
    # a subtraction of large energies inaccurate in float32.
    guided = (8 * c - 7 * u).abs().square()
    if weights is not None:
        guided = guided * weights
    g = guided.sum() / denominator
    cosine = torch.where(ec * eu > 0, cross / (ec * eu).clamp_min(1e-30).sqrt(), torch.zeros_like(cross))
    return {'c': ec, 'u': eu, 'cross': cross, 'guided': g, 'cosine': cosine}


def feature_tensors(current_pair, source_pair, *, mode='ALL'):
    """Device-resident scalar outputs; caller controls CPU transfer/sync.

    Inputs are equal-layout selected-channel shallow residuals. Use
    causal_slice first, whose gather/difference cost MUST also be timed.
    Raw full-width/RA features are already-paid proxies supplied separately.
    """
    torch = _torch()
    if mode not in ('RAW', 'HAAR', 'FFT', 'ALL') or len(current_pair) != 2 or len(source_pair) != 2:
        raise ValueError('One declared transform and complete CFG pair required')
    shapes = {tuple(x.shape) for x in (*current_pair, *source_pair)}
    if len(shapes) != 1 or len(next(iter(shapes))) != 5:
        raise ValueError('Same actual BTHWD for both branches and sources required')
    dc, du = [_spatial(current_pair[b]) - _spatial(source_pair[b]) for b in (0, 1)]
    denom = dc.numel()
    raw = _energy(dc, du, denom)
    out = {'raw_sub_' + k: v for k, v in raw.items()}
    if mode in ('HAAR', 'ALL'):
        cl, ch = haar_bands(dc); ul, uh = haar_bands(du)
        low = _energy(cl, ul, denom)
        detail = [_energy(c, u, denom) for c, u in zip(ch, uh)]
        high = {k: sum(d[k] for d in detail) for k in ('c', 'u', 'cross', 'guided')}
        high['cosine'] = torch.where(high['c'] * high['u'] > 0,
            high['cross'] / (high['c'] * high['u']).clamp_min(1e-30).sqrt(), torch.zeros_like(high['cross']))
        out.update({'haar_low_' + k: v for k, v in low.items()})
        out.update({'haar_detail_' + k: v for k, v in high.items()})
        out['haar_detail_guided_fraction'] = torch.where(raw['guided'] > 0,
            high['guided'] / raw['guided'].clamp_min(1e-30), torch.zeros_like(raw['guided']))
    if mode in ('FFT', 'ALL'):
        zc, low_mask, mult = fft_bands(dc); zu, low2, mult2 = fft_bands(du)
        low = _energy(zc, zu, denom, mult * low_mask)
        high = _energy(zc, zu, denom, mult * ~low_mask)
        out.update({'fft_low_' + k: v for k, v in low.items()})
        out.update({'fft_high_' + k: v for k, v in high.items()})
        out['fft_high_guided_fraction'] = torch.where(raw['guided'] > 0,
            high['guided'] / raw['guided'].clamp_min(1e-30), torch.zeros_like(raw['guided']))
    # Names explicitly mark the two additional regression features per method.
    if 'haar_detail_cosine' in out:
        out['haar_detail_cfg_cosine'] = out['haar_detail_cosine']
    if 'fft_high_cosine' in out:
        out['fft_high_cfg_cosine'] = out['fft_high_cosine']
    return out


def probe_features(current_pair, source_pair, identity, raw_proxies, *, mode='ALL'):
    identity.validate()
    if not isinstance(raw_proxies, dict) or not raw_proxies or any(
            not math.isfinite(float(v)) for v in raw_proxies.values()):
        raise ValueError('Explicit already-paid raw/RA strong baseline required')
    expected = (*identity.geometry[:-1], min(identity.geometry[-1], 16))
    if any(tuple(x.shape) != expected for x in (*current_pair, *source_pair)):
        raise ValueError('Selected channels do not match bound actual geometry')
    tensors = feature_tensors(current_pair, source_pair, mode=mode)
    values = {k: float(v.detach().cpu()) for k, v in tensors.items()}
    if not all(math.isfinite(v) for v in values.values()):
        raise ValueError('Nonfinite feature row')
    return {'version': VERSION, 'identity': asdict(identity),
        'metadata': {'source_is_P': int(identity.source_kind == 'P'),
            'step': identity.step, 'source_age': identity.step - identity.source_birth,
            'true_D_age': identity.step - identity.true_D_birth,
            'tau': identity.current_tau, 'source_tau_span': identity.current_tau - identity.source_tau,
            'D_tau_span': identity.current_tau - identity.true_D_tau},
        'raw_full_paid_proxies': dict(raw_proxies), 'features': values,
        'fixed_channel_indices': list(channel_indices(identity.geometry[-1])),
        'fit_additions': FIT_ADDITIONS, 'same_current_source_CFG_spatial_transform': True,
        'teacher_features': False, 'mode': mode}


def time_device_pipeline(fn, *, device, authorized_gpu=False, warmups=10, repeats=30):
    """Whole callable wall time, including gather/layout/state maintenance.

    No CPU staging or file writes belong inside the online callable. The caller
    must include all required source maintenance and controller work and report
    that exact boundary. This utility neither admits nor launches model work.
    """
    torch = _torch()
    device = torch.device(device)
    if device.type == 'cuda' and not authorized_gpu:
        raise ValueError('GPU timing needs the admitted caller card')
    if warmups != 10 or repeats != 30:
        raise ValueError('Frozen ten warmups and thirty repeats required')
    sync = (lambda: torch.cuda.synchronize(device)) if device.type == 'cuda' else (lambda: None)
    with torch.no_grad():
        for _ in range(warmups):
            result = fn()
        sync(); seconds = []
        for _ in range(repeats):
            sync(); start = time.perf_counter(); result = fn(); sync()
            seconds.append(time.perf_counter() - start)
    return {'seconds': seconds, 'warmups': warmups, 'repeats': repeats,
        'median_seconds': statistics.median(seconds), 'min_seconds': min(seconds),
        'max_seconds': max(seconds), 'device': str(device),
        'boundary': 'WHOLE_CALLABLE_GATHER_LAYOUT_TRANSFORM_AGGREGATE_SOURCE_MAINTENANCE_AND_OPTIONAL_CONTROLLER',
        'model_or_end_to_end_speed_claim': False}


def compile_probe_collection(runtime, wc, rf, collector, pre_action_callback, *, dense_context=None):
    """Existing source-exact collector plus ONE pre-decision observation.

    Callback signature: (net, slot, ori_x, test_x, working_probe). Both probes
    have not yet completed at slot0; buffer only selected slices until slot1.
    It must be observational: no RNG, model/cache/controller changes or teacher.
    Existing source inverse checks cover the new hook because it is in the
    `_mf_a_` observation family. No module global or original source is edited.
    """
    from . import cfg_guided_w1_forward as base
    if not callable(pre_action_callback):
        raise ValueError('Explicit causal callback required')
    source = dedent(inspect.getsource(base.compile_collection))
    before = '    inverse = copy.deepcopy(node)\n'
    injection = '''    class SpectralObservation(ast.NodeTransformer):
        def visit_If(self, n):
            if isinstance(n.test, ast.Yield):
                hook = ast.parse('_mf_a_spectral_probe(self, current_idx, ori_x, test_x, self.probe_residual_cache[current_idx])').body[0]
                return [hook, n]
            return self.generic_visit(n)
    node = SpectralObservation().visit(node)
'''
    after = injection + before
    old_helper = "    if dense_context is not None:helpers['_mf_p_dense_context']=dense_context\n"
    new_helper = "    helpers['_mf_a_spectral_probe'] = _spectral_callback\n" + old_helper
    if source.count(before) != 1 or source.count(old_helper) != 1:
        raise ValueError('Original observation compiler boundary changed')
    changed = source.replace(before, after).replace(old_helper, new_helper)
    inverse = changed.replace(new_helper, old_helper).replace(after, before)
    if inverse != source or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(source)):
        raise ValueError('Observation compiler changed outside two declared sites')
    namespace = {**vars(base), '_spectral_callback': pre_action_callback}
    exec(compile(changed, __file__ + '#isolated-paid-probe-observer', 'exec'), namespace)
    net, denoise, proof = namespace['compile_collection'](runtime, wc, rf, collector, dense_context=dense_context)
    return net, denoise, {**dict(proof), 'spectral_version': VERSION,
        'spectral_pre_action_observation_sites': 1,
        'source_compiler_inverse_bytes_and_AST_equal': True,
        'source_compiler_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'teacher_or_action_change': False}
