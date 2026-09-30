"""CPU RGB fidelity/motion descriptors, not physical or semantic quality scores."""
from itertools import zip_longest
import math
import numpy as np


def score_frames(reference, candidate, expected_frames=93):
    count = elements = 0
    squared = absolute = 0.0
    maximum = 0
    previous = [None, None]
    motion = [0.0, 0.0]
    motion_elements = 0
    shape = None
    for pair in zip_longest(reference, candidate):
        if any(item is None for item in pair):
            raise ValueError('Video frame counts differ')
        (a, ap, at), (b, bp, bt) = pair
        if a.dtype != np.uint8 or b.dtype != np.uint8 or a.ndim != 3 or a.shape[-1] != 3 or a.shape != b.shape or (shape is not None and tuple(a.shape) != shape):
            raise ValueError('Video RGB geometry/dtype differs')
        if ap != bp or at != bt:
            raise ValueError('Video PTS/time bases differ')
        shape = tuple(a.shape)
        x, y = a.astype(np.float32), b.astype(np.float32)
        delta = x-y
        squared += float(np.sum(delta*delta, dtype=np.float64))
        absolute += float(np.sum(np.abs(delta), dtype=np.float64))
        maximum = max(maximum, int(np.max(np.abs(delta))))
        if previous[0] is not None:
            for i, current in enumerate([x, y]):
                motion[i] += float(np.sum(np.abs(current-previous[i]), dtype=np.float64))
            motion_elements += x.size
        previous = [x, y]
        elements += x.size
        count += 1
    if count != expected_frames or not elements:
        raise ValueError('Video does not have expected complete frame count')
    mse = squared/elements
    return {'frames': count, 'shape': list(shape), 'rgb_mse': mse, 'rgb_mae': absolute/elements,
            'rgb_max_abs_difference': maximum, 'psnr_db': 10*math.log10(255**2/mse) if mse > 0 else None,
            'identical_rgb': maximum == 0, 'reference_temporal_rgb_mae': motion[0]/motion_elements if motion_elements else None,
            'candidate_temporal_rgb_mae': motion[1]/motion_elements if motion_elements else None,
            'scope': 'Complete encoded RGB fidelity and temporal variation only; distance to WC and motion change do not establish correctness or quality.'}


def compare_videos(reference, candidate):
    import av
    with av.open(str(reference)) as a, av.open(str(candidate)) as b:
        def frames(container):
            for frame in container.decode(video=0):
                yield frame.to_ndarray(format='rgb24'), frame.pts, str(frame.time_base)
        return score_frames(frames(a), frames(b))
