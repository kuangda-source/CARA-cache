"""Full93 RGB on the original private volume; evict only this test's file pages."""
import argparse
import ctypes
import gc
import hashlib
import json
import mmap
import os
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path('/data20t/gaokuangda/worldcache_workspace')
PROVISION = ROOT/'.sync/storage-reservations/budget-calibration-r1/provision.json'
RUN = 'cara-budget-calibration-14gpuh-r1-20261030'


def cached_pages(path):
    """Linux mincore observes residency without reading the mapped file."""
    library = ctypes.CDLL(None, use_errno=True)
    library.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte)]
    library.mincore.restype = ctypes.c_int
    with Path(path).open('rb') as stream:
        size = os.fstat(stream.fileno()).st_size
        with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_COPY) as mapping:
            pages = (size+mmap.PAGESIZE-1)//mmap.PAGESIZE
            vector = (ctypes.c_ubyte*pages)()
            pointer = ctypes.c_char.from_buffer(mapping)
            try:
                if library.mincore(ctypes.addressof(pointer), size, vector) != 0:
                    raise OSError(ctypes.get_errno(), 'mincore failed for the private test file')
                resident = sum(bool(value & 1) for value in vector)
            finally:
                del pointer
    return dict(total_pages=pages, resident_pages=resident, page_bytes=mmap.PAGESIZE)


def main():
    parser = argparse.ArgumentParser()
    for name in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert args.host == 'two_card' and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    signal.alarm(180)
    started = time.time()
    sys.path.insert(0, str(args.stage/'src'))
    import numpy as np
    from wcomr.cara_budget_rgb_objective_r1 import save_endpoint, read_endpoint, full_rgb_mse, file_sha
    from wcomr.history104_storage_r2 import StorageGuard
    registration = json.loads((args.stage/'registration.json').read_text())
    assert all(file_sha(args.stage/n) == h for n, h in registration['payload_sha256'].items())
    assert file_sha(PROVISION) == '6f0e02cbc722ed85d312adae957079026fd78ecd6888bca632399e9d4bf60484'
    provision = json.loads(PROVISION.read_text())
    assert provision['status'] == 'TWO_CARD_PRIVATE64_STORAGE_PROVISIONED_NO_GPU'
    config = provision['storage_contract']
    guard = StorageGuard(config)
    assert guard.output == ROOT/'outputs'/RUN and config['image_bytes'] == 64*2**30
    initial_storage = guard.check()
    directory = guard.output/'CPU-storage-probe-r1-20261031'
    directory.mkdir(mode=0o700)
    shape = [3, 93, 432, 768]
    identity = dict(CPU_fixture_only=True, member='SYNTHETIC_PRIVATE_VOLUME', RGB_shape=shape, kind='NATIVE')
    candidate_identity = dict(identity, kind='CANDIDATE')
    rgb = np.full(shape, .5, dtype=np.float32)
    t = time.monotonic()
    native = save_endpoint(directory/'native', identity, rgb)
    native_save = time.monotonic()-t
    rgb[2, 92, -1, -1] = .75
    t = time.monotonic()
    candidate = save_endpoint(directory/'candidate', candidate_identity, rgb)
    candidate_save = time.monotonic()-t
    del rgb
    t = time.monotonic()
    reference, _ = read_endpoint(directory/'native', identity)
    value, _ = read_endpoint(directory/'candidate', candidate_identity)
    warm_read = time.monotonic()-t
    t = time.monotonic()
    warm_mse = full_rgb_mse(value, reference)
    warm_objective = time.monotonic()-t
    reference._mmap.close()
    value._mmap.close()
    del reference, value
    gc.collect()
    files = [directory/'native/RGB.npy', directory/'candidate/RGB.npy']
    # The backing image belongs only to this newly provisioned, unused volume.
    # No global drop_caches, model files or other users' files are touched.
    for path in [*files, Path(config['image_path'])]:
        with path.open('rb') as stream:
            os.fsync(stream.fileno())
            os.posix_fadvise(stream.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
    residency = {str(p): cached_pages(p) for p in files}
    assert all(row['resident_pages'] == 0 for row in residency.values())
    image_residency = cached_pages(config['image_path'])
    read_io_before = Path('/proc/self/io').read_text()
    t = time.monotonic()
    reference, _ = read_endpoint(directory/'native', identity)
    value, _ = read_endpoint(directory/'candidate', candidate_identity)
    cold_read = time.monotonic()-t
    t = time.monotonic()
    cold_mse = full_rgb_mse(value, reference)
    cold_objective = time.monotonic()-t
    assert warm_mse == cold_mse == .25**2/int(np.prod(shape))
    proof = dict(status='PRIVATE64_FULL93_RGB_CACHE_CONTROLLED_CPU_COMPLETE_NOT_GPU', host=args.host,
        started_unix=started, ended_unix=time.time(), registration_sha256=file_sha(args.stage/'registration.json'),
        source_revision=registration['parent_git_revision'], provision_sha256=file_sha(PROVISION),
        storage_contract=config, initial_storage=initial_storage, final_storage=guard.check(),
        RGB_shape=shape, original_artifacts={'native': native, 'candidate': candidate},
        fixture_directory=str(directory), retained_NPY_bytes=native['bytes']+candidate['bytes'],
        native_save_fsync_hash_seconds=native_save, candidate_save_fsync_hash_seconds=candidate_save,
        warm_read_hash_validate_two_arrays_seconds=warm_read, warm_full_MSE_seconds=warm_objective,
        cold_read_hash_validate_two_arrays_seconds=cold_read, cold_full_MSE_seconds=cold_objective,
        NPY_residency_before_cold_read=residency, image_residency_before_cold_read=image_residency,
        private_file_cache_eviction_only=True, read_io_before=read_io_before,
        read_io_after=Path('/proc/self/io').read_text(), synthetic_RGB_MSE=cold_mse,
        peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        cold_file_pages_established=True, universal_cold_disk_bound_established=False,
        real_model_output=False, GPU_to_CPU_copy_measured=False, GPU_submissions=0,
        ledger_written=False, whole_GPU_quote_accepted=False)
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    signal.alarm(30)
    print(json.dumps({k: proof[k] for k in ('status', 'cold_read_hash_validate_two_arrays_seconds',
                                           'cold_full_MSE_seconds', 'image_residency_before_cold_read')}), flush=True)


if __name__ == '__main__':
    main()
