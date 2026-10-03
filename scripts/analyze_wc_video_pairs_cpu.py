#!/usr/bin/env python3
"""Descriptive encoded-video fidelity/motion diagnostics; CPU only, no acceptance gate."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


@contextmanager
def rgb_frames(path, *, width=768, height=432):
    import numpy as np
    process = subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '1',
        '-filter_threads', '1', '-i', str(path), '-map', '0:v:0', '-an',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def frames():
        size = width * height * 3
        while True:
            data = process.stdout.read(size)
            if not data:
                return
            if len(data) != size:
                raise ValueError('Truncated decoded RGB frame')
            yield np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
    try:
        yield frames()
        if process.stdout.read(1):
            raise ValueError('Unconsumed video frames')
        process.stdout.close()
        error = process.stderr.read().decode(errors='replace')
        process.stderr.close()
        if process.wait(timeout=30) != 0 or error.strip():
            raise ValueError('Video decode failed: ' + error)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=30)
        if not process.stdout.closed:
            process.stdout.close()
        if not process.stderr.closed:
            process.stderr.close()


def compare_frames(left, right, *, expected_frames):
    import numpy as np
    from skimage.metrics import structural_similarity
    frame_rows, transitions = [], []
    previous_left = previous_right = None
    sentinel = object()
    for index in range(expected_frames):
        lraw, rraw = next(left, sentinel), next(right, sentinel)
        if lraw is sentinel or rraw is sentinel:
            raise ValueError('Missing decoded frame in paired comparison')
        if lraw.shape != rraw.shape or lraw.dtype != np.uint8 or rraw.dtype != np.uint8:
            raise ValueError('Paired RGB geometry/dtype mismatch')
        l, r = lraw.astype(np.float64) / 255, rraw.astype(np.float64) / 255
        mse = float(np.mean((r - l) ** 2, dtype=np.float64))
        ly, ry = [x @ np.array([0.2126, 0.7152, 0.0722]) for x in (l, r)]
        ssim = float(structural_similarity(ly, ry, data_range=1, win_size=7,
            gaussian_weights=False, use_sample_covariance=True))
        frame_rows.append({'frame_index': index, 'RGB_MSE_0to1': mse, 'luma_SSIM_win7': ssim})
        if previous_left is not None:
            dl, dr = l - previous_left, r - previous_right
            transitions.append({'ending_frame_index': index,
                'baseline_mean_abs_RGB_frame_change': float(np.mean(np.abs(dl))),
                'candidate_mean_abs_RGB_frame_change': float(np.mean(np.abs(dr))),
                'temporal_difference_MSE_0to1': float(np.mean((dr - dl) ** 2))})
        previous_left, previous_right = l, r
    if next(left, sentinel) is not sentinel or next(right, sentinel) is not sentinel:
        raise ValueError('Extra decoded frames beyond fixed protocol')
    def summarize(rows, changes):
        mse = sum(v['RGB_MSE_0to1'] for v in rows) / len(rows)
        result = {'frames': len(rows), 'RGB_MSE_0to1': mse,
            'RGB_PSNR_dB': -10 * math.log10(mse) if mse > 0 else None,
            'exact_RGB_equality': mse == 0,
            'mean_luma_SSIM_win7': sum(v['luma_SSIM_win7'] for v in rows) / len(rows),
            'transitions': len(changes)}
        if changes:
            for key in changes[0]:
                if key != 'ending_frame_index':
                    result[key] = sum(v[key] for v in changes) / len(changes)
            denominator = result['baseline_mean_abs_RGB_frame_change']
            result['candidate_over_baseline_frame_change'] = (
                result['candidate_mean_abs_RGB_frame_change'] / denominator if denominator else None)
        return result
    groups = [(name, start, stop) for name, start, stop in
              [('early', 0, 31), ('middle', 31, 62), ('late', 62, 93)]]
    return {'whole_video': summarize(frame_rows, transitions),
        'fixed_segments': {name: summarize(frame_rows[start:stop],
            [v for v in transitions if start <= v['ending_frame_index'] < stop])
            for name, start, stop in groups if start < expected_frames},
        'per_frame': frame_rows, 'per_transition': transitions}


def analyze(audit, *, dd_control_only=False):
    expected = ('DD_TWO_OUTPUT_INDEPENDENT_AUDIT_PASS_ENTIRE_CARD_PENDING' if dd_control_only
                else 'COMPLETE_SIX_OUTPUT_STRUCTURAL_DD_PROVENANCE_AUDIT_PASS')
    if audit['status'] != expected:
        raise ValueError('Required independent artifact audit not passed')
    files = audit['files']
    assert len(files) == (2 if dd_control_only else 6)
    for file in files:
        path = Path(file['path'])
        assert file['full93_decode'] and path.stat().st_size == file['bytes']
        assert sha(path) == file['sha256']
    pairs = [(files[0], files[1])] if dd_control_only else [(files[2], files[3]), (files[4], files[5])]
    results = []
    for left, right in pairs:
        with rgb_frames(left['path']) as l, rgb_frames(right['path']) as r:
            result = compare_frames(l, r, expected_frames=93)
        result.update(baseline_sha256=left['sha256'], candidate_sha256=right['sha256'],
                      sample_name=Path(left['path']).stem)
        if dd_control_only:
            values = result['whole_video']
            assert left['sha256'] == right['sha256'] and values['exact_RGB_equality']
            assert values['mean_luma_SSIM_win7'] == 1
            assert values['temporal_difference_MSE_0to1'] == 0
        results.append(result)
    return {'status': ('DD_ENCODED_VIDEO_METRIC_CONTROL_PASS' if dd_control_only
                      else 'TWO_EXPOSED_CAL_ENCODED_VIDEO_DIAGNOSTICS_COMPLETE_NOT_ACCEPTANCE'),
        'CPU_only': True, 'metric_packages': {k: importlib.metadata.version(k) for k in ['numpy', 'scikit-image']},
        'quality_acceptance': False, 'semantic_or_physics_acceptance': False,
        'clean_E2E_speed_claim': False, 'pairs': results,
        'limits': ['Encoded RGB difference from paired official WorldCache, not a native full-compute reference.',
            'Frame-change energy is a descriptive motion proxy; it does not identify physical correctness.',
            'Two previously exposed CAL scenes cannot support independent quality confirmation.',
            'PSNR is null for exactly identical RGB videos; no arbitrary cap or acceptance threshold.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dd-control-only', action='store_true')
    args = parser.parse_args()
    result = analyze(json.loads(args.audit.read_text()), dd_control_only=args.dd_control_only)
    result.update(input_audit_sha256=sha(args.audit), analysis_code_sha256=sha(Path(__file__)))
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'whole_video': [v['whole_video'] for v in result['pairs']]}))
