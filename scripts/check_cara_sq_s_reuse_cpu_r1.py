"""One GPU-hidden, single-read audit of the retained Shared25-C witness."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]


def require(value, message):
    if not value:
        raise ValueError(message)


def identity(path):
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]


def main():
    parser = argparse.ArgumentParser()
    for name in ('assets', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    for name in ('profile', 'scope', 'manifest-sha256'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Retain the original CPU audit')
    require(args.profile == 'two_card' and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
            and os.environ.get('NVIDIA_VISIBLE_DEVICES') == 'void', 'Original host and hidden GPU required')
    started, cpu = time.monotonic(), time.process_time()
    import torch
    original_load = torch.load
    def forbidden(*a, **kw):
        raise RuntimeError('Reuse audit cannot initialize CUDA, load weights or download')
    torch.cuda._lazy_init = forbidden
    torch.load = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)
    os.nice(10)
    scope = json.loads((ROOT/args.scope).read_text())
    require(scope['host'] == args.profile and scope['GPU_authorized'] is False,
            'Frozen CPU-only host scope required')
    project = args.assets.parents[2]
    observed = {}
    def read_once(ref):
        path = Path(ref['path'])
        require(path.is_absolute() and path.is_relative_to(project) and not path.is_symlink(),
                'Only the registered original regular files')
        before = identity(path)
        require(before[2] == ref['bytes'] <= scope['maximum_input_file_bytes'], 'Original file size differs')
        t = time.monotonic()
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == ref['sha256'] and identity(path) == before,
                'Original file SHA or identity differs')
        observed[str(path)] = dict(sha256=ref['sha256'], identity=before,
                                  single_read_seconds=time.monotonic()-t)
        return raw
    # Source/config/request originals are checked before any large tensor read.
    for ref in scope['metadata_files']:
        read_once(ref)
    for name, expected in scope['current_source_sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected,
                'Proposed numerical source differs: '+name)
    for name, expected in scope['runtime_source_sha256'].items():
        require(hashlib.sha256((project/'runtime'/name).read_bytes()).hexdigest() == expected,
                'Original pinned runtime differs: '+name)
    checkpoint = scope['previously_verified_checkpoint']
    checkpoint_path = Path(checkpoint['path'])
    require(identity(checkpoint_path) == checkpoint['identity'], 'Previously SHA-verified checkpoint changed')
    checks = scope['artifact_checks']
    request = json.loads(read_once(checks['request_artifact']))
    require(request == scope['original_request'], 'Retained request metadata differs')
    guided_raw = read_once(checks['guided_artifact'])
    guided = original_load(io.BytesIO(guided_raw), map_location='cpu', weights_only=True)
    del guided_raw
    latent_raw = read_once(checks['final_latent_artifact'])
    latent = original_load(io.BytesIO(latent_raw), map_location='cpu', weights_only=True)
    del latent_raw
    from wcomr.sq_s_reuse_r1 import trajectory_bridge, decoded_rgb_signature
    signatures = trajectory_bridge(guided['guided'], latent['final_latent'], checks)
    del guided, latent
    # The small encoded file is SHA-checked first; decoding is a separate object.
    read_once(checks['video_artifact'])
    video_path = Path(checks['video_artifact']['path'])
    video_identity = identity(video_path)
    rgb = decoded_rgb_signature(video_path)
    require(rgb == scope['decoded_RGB93'] and identity(video_path) == video_identity,
            'Retained decoded RGB or video identity differs')
    import test_sq_s_reuse_r1 as units
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(units))
    require(tests.wasSuccessful() and tests.testsRun == 5 and not tests.skipped,
            'Legacy/new hash bridge controls failed: '+log.getvalue())
    require(not torch.cuda.is_initialized(), 'CPU audit initialized CUDA')
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = dict(status='S_LEGACY_WITNESS_CPU_BYTES_AND_SIGNATURES_VERIFIED', profile=args.profile,
        scope=scope, files=observed, signatures=signatures, decoded_RGB93=rgb,
        checkpoint_identity_unchanged=True, checkpoint_SHA_recomputed=False,
        unit_controls=dict(tests=tests.testsRun, skipped=len(tests.skipped), log=log.getvalue()),
        old_OFF_candidate_verified=True, new_ON_equivalence_accepted=False,
        actual_Cosmos_weights=False, real_generated_video=False, S_labels_collected=0,
        CUDA_initialized=False, GPU_submissions=0, new_GPUh=0, ledger_writes=0,
        CPU_wall_seconds=time.monotonic()-started, CPU_seconds=time.process_time()-cpu,
        reaped_child_CPU_seconds=child_usage.ru_utime+child_usage.ru_stime,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        actual_platform=dict(system=platform.system(), machine=platform.machine()), torch_version=torch.__version__)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(result['status'])


if __name__ == '__main__':
    main()
