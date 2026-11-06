"""Focused CPU correctness checks for spatial F features, not model efficacy."""
import ast
import copy
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


def run():
    import torch
    from wcomr import spectral_probe_r1 as s
    torch.manual_seed(20261013)
    checks = []

    # All parity cases use the true unpadded latent geometry. rFFT must count
    # only non-DC/non-Nyquist conjugates twice; Haar must retain singleton rows.
    for h, w in ((27, 48), (6, 8), (5, 7), (6, 7), (5, 8), (1, 1)):
        current = tuple(torch.randn(1, 2, h, w, 16) for _ in range(2))
        source = tuple(torch.randn_like(x) for x in current)
        before_rng = torch.get_rng_state().clone()
        copies = [x.clone() for x in (*current, *source)]
        f = s.feature_tensors(current, source)
        for key in ('c', 'u', 'cross', 'guided'):
            torch.testing.assert_close(f['haar_low_' + key] + f['haar_detail_' + key],
                                       f['raw_sub_' + key], rtol=2e-5, atol=2e-5)
            torch.testing.assert_close(f['fft_low_' + key] + f['fft_high_' + key],
                                       f['raw_sub_' + key], rtol=2e-5, atol=2e-5)
        assert torch.equal(before_rng, torch.get_rng_state())
        assert all(torch.equal(x, y) for x, y in zip(copies, (*current, *source)))
        checks.append({'test': 'Parseval_real_CFG_and_no_mutation', 'H': h, 'W': w})

    # A phase shift preserves the individual amplitude spectra. Complex
    # differences must nevertheless record its nonzero spatial drift.
    h, w = 27, 48
    x = torch.sin(2 * math.pi * torch.arange(w).float() / w)[None, None, None, :, None].expand(1, 1, h, w, 16).clone()
    y = x.roll(3, dims=3)
    zx = torch.fft.rfft2(s._spatial(x), norm='ortho')
    zy = torch.fft.rfft2(s._spatial(y), norm='ortho')
    torch.testing.assert_close(zx.abs(), zy.abs(), rtol=1e-5, atol=1e-5)
    f = s.feature_tensors((x, x), (y, y))
    assert float(f['raw_sub_guided']) > .01
    torch.testing.assert_close(f['fft_low_guided'] + f['fft_high_guided'], f['raw_sub_guided'])
    checks.append({'test': 'complex_phase_change_not_lost'})

    # Full CFG cancellation produces zero exactly, with finite zero-cosine
    # conventions. No numerical negative guided energy is clamped into success.
    c = torch.ones(1, 1, 27, 48, 16) * 7
    u = torch.ones_like(c) * 8
    zero = torch.zeros_like(c)
    f = s.feature_tensors((c, u), (zero, zero))
    assert all(torch.isfinite(v) for v in f.values())
    assert f['raw_sub_guided'] == 0
    assert f['haar_detail_guided_fraction'] == f['fft_high_guided_fraction'] == 0
    checks.append({'test': 'strong_CFG_cancellation_zero_finite'})

    # Same fixed real channels for original/current/source; subtraction occurs
    # in runtime dtype. No channel-average or flattened-token pseudo spectrum.
    original = torch.arange(2048, dtype=torch.float32).view(1, 1, 1, 1, 2048).expand(1, 1, 27, 48, 2048).clone()
    probe = original + 2
    working = torch.ones_like(probe)
    current, source, ids = s.causal_slice(original, probe, working, cpu=True)
    assert ids == s.CHANNELS_2048 and current.shape == (1, 1, 27, 48, 16)
    assert torch.equal(current, torch.full_like(current, 2)) and torch.equal(source, torch.ones_like(source))
    identity = s.ProbeIdentity('CAL_ONLY', 10, 'P', 8, 7, .7, .8, .9,
                              tuple(probe.shape), 'CAL_ONLY:P:8')
    row = s.probe_features((current, current), (source, source), identity,
                           {'delta_x_c': .1, 'delta_y_c': .2, 'delta_x_u': .1, 'delta_y_u': .2})
    assert row['metadata']['source_age'] == 2 and row['metadata']['true_D_age'] == 3
    assert row['raw_full_paid_proxies']['delta_y_c'] == .2 and not row['teacher_features']
    assert len(row['fit_additions']['F_HAAR']) == len(row['fit_additions']['F_FFT']) == 2
    json.dumps(row, allow_nan=False)
    checks.append({'test': 'actual_2048_channel_mapping_same_source_and_noise_time'})

    # BF16/FP16 FFT converts to FP32 and retains the quantized runtime delta.
    for dtype in (torch.float16, torch.bfloat16):
        a = torch.randn(1, 1, 27, 48, 16).to(dtype)
        b = torch.randn_like(a)
        f = s.feature_tensors((a, a), (b, b))
        torch.testing.assert_close(f['fft_low_guided'] + f['fft_high_guided'],
                                   f['raw_sub_guided'], rtol=1e-5, atol=1e-5)
        checks.append({'test': 'low_precision_explicit_FP32_transform', 'dtype': str(dtype)})

    bad = copy.copy(identity)
    object.__setattr__(bad, 'source_birth', 10)
    try:
        bad.validate()
    except ValueError:
        pass
    else:
        raise AssertionError('Current/future source accepted')
    try:
        s.time_device_pipeline(lambda: None, device='cuda', authorized_gpu=False)
    except ValueError:
        pass
    else:
        raise AssertionError('Unadmitted GPU timer accepted')
    timing = s.time_device_pipeline(lambda: s.feature_tensors((current, current), (source, source), mode='HAAR'), device='cpu')
    assert len(timing['seconds']) == 30 and timing['warmups'] == 10
    checks.append({'test': 'source_causality_GPU_guard_and_CPU_timer'})
    return {'status': 'SPECTRAL_FEATURE_CPU_MATH_LAYOUT_PASS_NOT_REAL_MODEL_OR_SPEED',
            'checks': checks, 'GPU_calls': 0, 'teacher_or_model_runs': 0}


def compiler_contract(runtime, wc, rf, collector):
    """Called by an actual source-bound CPU runner when its modules are ready."""
    from wcomr import spectral_probe_r1 as s
    seen = []
    def callback(net, slot, original, probe, source):
        seen.append(slot)
    net, denoise, proof = s.compile_probe_collection(runtime, wc, rf, collector, callback,
                                                    dense_context=collector.dense_context)
    assert proof['WC_collection_inverse_AST_equal'] and proof['RF_collection_inverse_AST_equal']
    assert proof['spectral_pre_action_observation_sites'] == 1
    assert proof['source_compiler_inverse_bytes_and_AST_equal']
    assert not seen  # compilation itself executes no probe/model/teacher
    return net, denoise, proof


if __name__ == '__main__':
    try:
        import torch
    except ImportError:
        print(json.dumps({'status': 'NOT_RUN_TORCH_UNAVAILABLE', 'GPU_calls': 0}))
        raise SystemExit(2)
    print(json.dumps(run(), indent=2))
