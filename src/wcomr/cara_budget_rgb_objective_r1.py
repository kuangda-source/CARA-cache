"""Complete pre-encoding RGB artifacts and equal-cohort endpoint MSE.

Values are captured after the original video guardrail and before the original
writer. There is no MP4 decode, clipping, resizing or frame selection here.
"""
import hashlib
import math
import os
from pathlib import Path

import numpy as np

from .cara_budget_search_journal_r1 import create_record, read_record, sync_directory

RGB_SPACE = 'GUARDRAIL_PASSED_PRE_ENCODE_CTHW_FLOAT32_UNIT_RANGE_R1'


def file_sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024**2), b''):
            result.update(block)
    return result.hexdigest()


def validate_rgb(rgb, shape):
    if (not isinstance(rgb, np.ndarray) or rgb.dtype != np.float32 or list(rgb.shape) != list(shape)
            or len(shape) != 4 or shape[0] != 3 or shape[1] != 93
            or any(type(n) is not int or n <= 0 for n in shape)
            or not np.isfinite(rgb).all() or rgb.min() < 0 or rgb.max() > 1):
        raise ValueError('Complete finite93-frame CTHW float32 unit-range RGB required')


def save_endpoint(directory, identity, rgb):
    directory = Path(directory)
    validate_rgb(rgb, identity['RGB_shape'])
    directory.mkdir(mode=0o700)
    sync_directory(directory.parent)
    # Intent persists even if array serialization, writing or completion fails.
    create_record(directory/'identity.json', identity)
    path = directory/'RGB.npy'
    with path.open('xb') as stream:
        np.save(stream, rgb, allow_pickle=False)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(directory)
    receipt = dict(identity=identity, RGB_space=RGB_SPACE,
        RGB_sha256=file_sha(path), bytes=path.stat().st_size, complete_frames=93)
    create_record(directory/'complete.json', receipt)
    return receipt


def read_endpoint(directory, expected_identity):
    directory = Path(directory)
    receipt = read_record(directory/'complete.json')
    path = directory/'RGB.npy'
    if (directory.is_symlink() or path.is_symlink() or not path.is_file()
            or receipt['identity'] != expected_identity
            or read_record(directory/'identity.json') != expected_identity
            or receipt['RGB_space'] != RGB_SPACE or receipt['complete_frames'] != 93
            or receipt['bytes'] != path.stat().st_size or file_sha(path) != receipt['RGB_sha256']):
        raise ValueError('Original complete RGB source/request/encoding identity differs')
    rgb = np.load(path, allow_pickle=False, mmap_mode='r')
    validate_rgb(rgb, expected_identity['RGB_shape'])
    return rgb, receipt


def full_rgb_mse(candidate, teacher):
    if candidate.shape != teacher.shape:
        raise ValueError('Same complete RGB geometry required')
    validate_rgb(candidate, list(candidate.shape))
    validate_rgb(teacher, list(teacher.shape))
    # Accumulate all pixels in float64, a frame at a time to avoid full-video
    # float64 copies. No per-frame scores are exposed to an unfinished search.
    sums = []
    for frame in range(93):
        delta = candidate[:,frame].astype(np.float64)-teacher[:,frame]
        sums.append(float(np.sum(delta*delta, dtype=np.float64)))
    return math.fsum(sums)/candidate.size
