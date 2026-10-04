"""Full native-size RGB decode with source frame timestamps, CPU only."""
from contextlib import contextmanager
from fractions import Fraction
import json
from pathlib import Path
import subprocess


def validate_probe(data):
    streams = data.get('streams', [])
    frames = data.get('frames', [])
    if len(streams) != 1 or len(frames) != 93:
        raise ValueError('Single complete93-frame video stream required')
    stream = streams[0]
    if (stream['width'], stream['height']) != (768, 432):
        raise ValueError('Original432x768 geometry required; no resizing')
    if Fraction(stream['r_frame_rate']) != 16 or Fraction(stream['avg_frame_rate']) != 16:
        raise ValueError('Frozen16fps video protocol differs')
    base = Fraction(stream['time_base'])
    if base <= 0:
        raise ValueError('Positive encoded frame time base required')
    timestamps = []
    for frame in frames:
        if (frame['width'], frame['height']) != (768, 432):
            raise ValueError('Per-frame geometry changed')
        raw = frame.get('best_effort_timestamp')
        if type(raw) is not int or raw < 0:
            raise ValueError('Original integer frame timestamp missing')
        timestamps.append(raw)
    if any((b-a)*base != Fraction(1, 16) for a, b in zip(timestamps, timestamps[1:])):
        raise ValueError('Missing/reordered/nonuniform source frames; do not resample')
    return {'frames': 93, 'HWC': [432, 768, 3], 'fps': 16,
            'pts': timestamps, 'time_base': str(base), 'resize_crop_subsample': False}


def probe_video(path):
    raw = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_frames', '-show_entries',
        'stream=width,height,r_frame_rate,avg_frame_rate,time_base:frame=width,height,best_effort_timestamp',
        '-of', 'json', str(path)], timeout=90)
    return validate_probe(json.loads(raw))


def decode_stream(stream, metadata):
    import numpy as np
    size = 432*768*3
    for pts in metadata['pts']:
        data = stream.read(size)
        if len(data) != size:
            raise ValueError('Truncated decoded RGB frame')
        yield np.frombuffer(data, dtype=np.uint8).reshape(432, 768, 3), pts, metadata['time_base']
    if stream.read(1):
        raise ValueError('Extra decoded frames beyond fixed93 denominator')


@contextmanager
def decoded_video(path):
    metadata = probe_video(Path(path))
    process = subprocess.Popen(['ffmpeg', '-v', 'error', '-threads', '1', '-filter_threads', '1',
        '-i', str(path), '-map', '0:v:0', '-an', '-fps_mode', 'passthrough',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        yield decode_stream(process.stdout, metadata)
        if process.stdout.read(1):
            raise ValueError('Video reader did not consume every full frame')
        process.stdout.close()
        error = process.stderr.read().decode(errors='replace'); process.stderr.close()
        if process.wait(timeout=30) != 0 or error.strip():
            raise ValueError('Complete video decode failed: '+error)
    finally:
        if process.poll() is None:
            process.kill(); process.wait(timeout=30)
        for stream in [process.stdout, process.stderr]:
            if not stream.closed: stream.close()
