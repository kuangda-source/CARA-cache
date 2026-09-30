"""Anonymous bounded range transfer, with rollback and full-object digest gate."""
import hashlib
import os
from pathlib import Path
import time
import urllib.request


def object_hash(path, git_blob=False):
    h = hashlib.sha1() if git_blob else hashlib.sha256()
    if git_blob:
        h.update(('blob %d\0' % path.stat().st_size).encode())
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def transfer(url, partial, blob, size, digest, *, chunk_bytes=16 << 20,
             attempts=3, socket_timeout=30, git_blob=False, progress=None):
    """Commit at most one range per request; never append unchecked responses.

    Existing prefixes are untrusted until the final object digest matches.
    A short/failed response rolls back that request, retaining earlier chunks.
    """
    partial, blob = Path(partial), Path(blob)
    if partial.is_symlink() or blob.is_symlink():
        raise ValueError('Blob and partial must be regular owned cache files')
    if blob.exists():
        if blob.stat().st_size != size or object_hash(blob, git_blob) != digest:
            raise ValueError('Existing complete blob does not match official digest')
        return {'status': 'EXISTING_BLOB_FULL_HASH_PASS', 'bytes': size, 'digest': digest}
    if not 0 < chunk_bytes <= 32 << 20 or not 1 <= attempts <= 3:
        raise ValueError('Unsupported bounded chunk/retry limits')
    partial.parent.mkdir(parents=True, exist_ok=True)
    initial = partial.stat().st_size if partial.exists() else 0
    if not 0 <= initial <= size:
        raise ValueError('Partial exceeds official file length')
    stats = {'status': 'RUNNING', 'initial_bytes': initial, 'durable_bytes': initial,
             'size': size, 'requests': 0, 'completed_chunks': 0, 'retries': 0}
    with partial.open('ab') as stream:
        while stream.tell() < size:
            start = stream.tell()
            end = min(size - 1, start + chunk_bytes - 1)
            expected = end - start + 1
            for attempt in range(attempts):
                stats['requests'] += 1
                try:
                    request = urllib.request.Request(url, headers={
                        'Range': 'bytes=%d-%d' % (start, end),
                        'Accept-Encoding': 'identity', 'User-Agent': 'worldcache-omr-cpu-assets'})
                    with urllib.request.urlopen(request, timeout=socket_timeout) as response:
                        if response.status != 206 or response.headers.get('Content-Range') != 'bytes %d-%d/%d' % (start, end, size):
                            raise ValueError('Server did not honor exact bounded range')
                        if int(response.headers.get('Content-Length', '-1')) != expected:
                            raise ValueError('Range response byte count differs')
                        received = 0
                        while received < expected:
                            block = response.read(min(1 << 20, expected - received))
                            if not block:
                                raise ValueError('Short range response')
                            stream.write(block)
                            received += len(block)
                    stream.flush()
                    os.fsync(stream.fileno())
                    stats.update(durable_bytes=end + 1, completed_chunks=stats['completed_chunks'] + 1)
                    if progress:
                        progress(dict(stats))
                    break
                except Exception as error:
                    # Never serialize signed redirect URLs, headers or tokens.
                    stream.flush()
                    stream.truncate(start)
                    stream.seek(start)
                    os.fsync(stream.fileno())
                    stats.update(durable_bytes=start, retries=stats['retries'] + 1,
                                 last_error_type=type(error).__name__)
                    if progress:
                        progress(dict(stats))
                    if attempt + 1 == attempts:
                        raise RuntimeError('Bounded range attempts exhausted at byte %d' % start) from None
                    time.sleep(.2)
    actual = object_hash(partial, git_blob)
    if actual != digest:
        raise ValueError('Full downloaded object digest differs; partial retained')
    if blob.exists():
        raise ValueError('Blob appeared concurrently; no overwrite')
    partial.rename(blob)
    stats.update(status='FULL_OBJECT_HASH_PASS', digest=actual, durable_bytes=size)
    if progress:
        progress(dict(stats))
    return stats
