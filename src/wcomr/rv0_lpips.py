"""Frozen full-frame Native-relative LPIPS fidelity protocol, no physics claim."""
import math

import numpy as np
import torch

PROTOCOL = {'package': 'lpips', 'package_version': '0.1.4', 'metric_version': '0.1',
            'backbone': 'alex', 'spatial': False, 'precision': 'torch.float32',
            'device': 'cpu', 'RGB_input': 'UINT8_HWC_TO_NCHW_MINUS1_TO_PLUS1',
            'resize_crop_subsample': False, 'expected_frames': 93,
            'expected_HWC': [432, 768, 3], 'aggregation': 'ARITHMETIC_MEAN_ALL93_FRAME_DISTANCES',
            'reference': 'MATCHED_NATIVE_FULL35_SAME_REQUEST_NOISE_DECODE',
            'benefit': 'J_C_MINUS_J_D_NEGATIVE_VALUES_RETAINED',
            'policy': 'ONE_ACTION_ADAPTIVE_DIAGNOSTIC_NOT_BUDGET_MATCHED',
            'formal_RV_training_labels': False, 'physics_or_quality_noninferiority': False}


def prepare_rgb(rgb):
    if not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[-1] != 3:
        raise ValueError('LPIPS requires decoded uint8 HWC RGB')
    return torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).unsqueeze(0).float()/127.5-1.


def score_pair(reference, candidate, model, *, reference_sha256, candidate_sha256,
               expected_frames=93, expected_HWC=(432, 768, 3)):
    """Iterators yield (RGB, PTS, time_base); keep all frames and paired times."""
    if any(p.device.type != 'cpu' for p in model.parameters()) or model.training:
        raise ValueError('Frozen CPU eval LPIPS model required')
    for digest in [reference_sha256, candidate_sha256]:
        if type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Both LPIPS artifact identities must be explicit SHA256')
    sentinel = object(); left, right = iter(reference), iter(candidate); values = []; pts = []
    while True:
        a, b = next(left, sentinel), next(right, sentinel)
        if a is sentinel or b is sentinel:
            if a is not b: raise ValueError('Paired LPIPS frame count differs')
            break
        if tuple(a[0].shape) != expected_HWC or tuple(b[0].shape) != expected_HWC:
            raise ValueError('Full LPIPS frame geometry differs; do not resize')
        if (a[1], str(a[2])) != (b[1], str(b[2])):
            raise ValueError('Paired LPIPS timestamps differ')
        with torch.inference_mode(): score = model(prepare_rgb(a[0]), prepare_rgb(b[0]))
        if score.numel() != 1 or not bool(torch.isfinite(score).all()):
            raise ValueError('LPIPS output is nonfinite/non-scalar')
        values.append(float(score.item())); pts.append([a[1], str(a[2])])
    if len(values) != expected_frames: raise ValueError('LPIPS complete frame denominator differs')
    return {'frames': len(values), 'pts': pts, 'frame_distances': values,
            'mean_LPIPS': sum(values)/len(values), 'Native_fidelity_not_physics': True,
            'reference_sha256': reference_sha256, 'candidate_sha256': candidate_sha256}


def signed_diagnostic(c, d):
    if (c['frames'] != d['frames'] or c['pts'] != d['pts']
            or c['reference_sha256'] != d['reference_sha256']):
        raise ValueError('C/D LPIPS diagnostic references/frames not matched')
    if not all(math.isfinite(x) for x in (c['mean_LPIPS'], d['mean_LPIPS'])):
        raise ValueError('Nonfinite LPIPS branch loss')
    return {'LPIPS_C_minus_D': c['mean_LPIPS']-d['mean_LPIPS'],
            'protocol': PROTOCOL, 'signed_negative_retained': True,
            'budget_matched': False, 'formal_RV_training_label': False}
