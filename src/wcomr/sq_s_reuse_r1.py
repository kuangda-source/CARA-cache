"""Bridge retained DEV128 witnesses to S without changing either hash format."""
import hashlib

import torch

from .mid_coverage import tree_digest
from .rv0_video_reader import decoded_video


def tensor_bridge(value, legacy):
    """Verify the old raw-byte identity and retain the newer typed identity."""
    if not isinstance(value, torch.Tensor) or value.device.type != 'cpu':
        raise ValueError('Original CPU tensor required')
    value = value.detach().contiguous()
    raw = dict(dtype=str(value.dtype), shape=list(value.shape),
               sha256=hashlib.sha256(memoryview(value.reshape(-1).view(torch.uint8).numpy())).hexdigest())
    if raw != legacy:
        raise ValueError('Original tensor dtype, shape or bytes differ')
    return dict(legacy_raw_bytes=raw, S_typed_tensor=dict(dtype=raw['dtype'],
                shape=raw['shape'], sha256=tree_digest(value)))


def trajectory_bridge(guided, latent, checks):
    if not isinstance(guided, (list, tuple)) or len(guided) != 36 or checks['guided_steps'] != 36:
        raise ValueError('All original 36 guided updates required')
    if len(checks['guided_tensors']) != 36:
        raise ValueError('All original tensor identities required')
    return dict(guided=[tensor_bridge(v, ref) for v, ref in zip(guided, checks['guided_tensors'])],
                final_latent=tensor_bridge(latent, checks['latent_tensor']))


def decoded_rgb_signature(path):
    """Hash the complete decoded MP4 pixels, separately from pre-encode RGB."""
    digest = hashlib.sha256()
    count = 0
    with decoded_video(path) as frames:
        for frame, _, _ in frames:
            digest.update(memoryview(frame))
            count += 1
    if count != 93:
        raise ValueError('All original 93 decoded frames required')
    return dict(frames=count, sha256=digest.hexdigest())
