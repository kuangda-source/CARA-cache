"""Wheel metadata checks and an explicitly provenance-bound unhashed asset fetch."""
import email
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request
import zipfile
from wcomr.ranged_download import object_hash


def inspect_wheel(path, row, check_crc=False):
    with zipfile.ZipFile(path) as archive:
        metadata = [x for x in archive.infolist() if x.filename.endswith('.dist-info/METADATA')]
        wheels = [x for x in archive.infolist() if x.filename.endswith('.dist-info/WHEEL')]
        if len(metadata) != 1 or len(wheels) != 1 or any(x.file_size > 256 << 10 for x in metadata + wheels):
            raise ValueError('Invalid wheel metadata layout')
        info = email.message_from_bytes(archive.read(metadata[0]))
        wheel = email.message_from_bytes(archive.read(wheels[0]))
        canonical = lambda x: x.lower().replace('_', '-')
        version = info['Version']
        matches = version == row['version'] or (row['package'] == 'flash-attn' and version.split('+')[0] == row['version'])
        if canonical(info['Name']) != canonical(row['package']) or not matches:
            raise ValueError('Wheel package/version differs')
        if 'cp311-cp311-linux_x86_64' not in wheel.get_all('Tag', []):
            raise ValueError('Wheel Python/platform tag differs')
        if check_crc:
            if sum(x.file_size for x in archive.infolist()) > 4 << 30 or archive.testzip() is not None:
                raise ValueError('Unhashed release wheel CRC/layout failed')
        return {'package': info['Name'], 'version': version, 'tags': wheel.get_all('Tag', []),
                'requires_dist': info.get_all('Requires-Dist', []), 'crc_checked': check_crc}


def acquire_release_asset(row, cache, progress=None):
    """Keep unknown official SHA explicit; authenticate source, freeze local SHA.

    A durable prefix remains untrusted until full size, ZIP CRC and metadata
    validation. No cache hit is accepted without its frozen payload digest.
    """
    if row['package'] != 'flash-attn' or row['official_sha256'] is not None:
        raise ValueError('Use official digest transfer for hashed sources')
    request = urllib.request.Request(row['release_api'], headers={'User-Agent': 'worldcache-omr-cpu-assets'})
    with urllib.request.urlopen(request, timeout=30) as response:
        release = json.load(response)
    assets = [a for a in release['assets'] if a['id'] == row['asset_id']]
    if len(assets) != 1 or assets[0]['name'] != row['filename'] or assets[0]['size'] != row['size'] or assets[0]['browser_download_url'] != row['url']:
        raise ValueError('Official release asset identity changed')
    cache = Path(cache)
    blob = cache / row['filename']
    partial = blob.with_name(blob.name + '.incomplete')
    binding = blob.with_name(blob.name + '.source.json')
    frozen = blob.with_name(blob.name + '.identity.json')
    if any(p.is_symlink() for p in [blob, partial, binding, frozen]):
        raise ValueError('Owned wheel cache files must be regular')
    identity = {k: row[k] for k in ['url', 'asset_id', 'filename', 'size', 'package', 'version']}
    cache.mkdir(parents=True, exist_ok=True)
    if binding.exists():
        if json.loads(binding.read_text()) != identity:
            raise ValueError('Partial source binding differs')
    else:
        binding.open('x').write(json.dumps(identity, indent=2) + '\n')
    if blob.exists():
        if not frozen.exists() or blob.stat().st_size != row['size']:
            raise ValueError('Existing release wheel lacks matching frozen digest')
        saved = json.loads(frozen.read_text())
        if saved['source_identity'] != identity or object_hash(blob) != saved['actual_sha256']:
            raise ValueError('Existing release wheel lacks matching frozen digest')
        inspect_wheel(blob, row, check_crc=True)
        return dict(saved, cache_hit=True)
    start = partial.stat().st_size if partial.exists() else 0
    if not 0 <= start <= row['size']:
        raise ValueError('Release partial exceeds expected length')
    stats = {'initial_bytes': start, 'durable_bytes': start, 'requests': 0, 'retries': 0,
             'size': row['size'], 'official_sha256': None}
    with partial.open('ab') as stream:
        for attempt in range(3):
            start = stream.tell()
            if start == row['size']:
                break
            stats['requests'] += 1
            try:
                request = urllib.request.Request(row['url'], headers={'Range': 'bytes=%d-%d' % (start, row['size'] - 1), 'Accept-Encoding': 'identity'})
                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status != 206 or response.headers.get('Content-Range') != 'bytes %d-%d/%d' % (start, row['size'] - 1, row['size']) or int(response.headers.get('Content-Length', '-1')) != row['size'] - start:
                        raise ValueError('Release server did not honor exact remaining range')
                    while stream.tell() < row['size']:
                        data = response.read(min(1 << 20, row['size'] - stream.tell()))
                        if not data:
                            raise ValueError('Short release response')
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                        stats['durable_bytes'] = stream.tell()
                        if progress:
                            progress(dict(stats))
                break
            except Exception as error:
                stream.flush()
                stream.truncate(stats['durable_bytes'])
                stream.seek(stats['durable_bytes'])
                os.fsync(stream.fileno())
                stats.update(retries=stats['retries'] + 1, last_error_type=type(error).__name__)
                if progress:
                    progress(dict(stats))
                if attempt == 2:
                    raise RuntimeError('Release transfer failed; inspect sanitized receipt') from None
                time.sleep(.2)
    if partial.stat().st_size != row['size']:
        raise ValueError('Full release byte count differs')
    metadata = inspect_wheel(partial, row, check_crc=True)
    actual = object_hash(partial)
    if frozen.exists() and json.loads(frozen.read_text())['actual_sha256'] != actual:
        raise ValueError('Recovered release differs from frozen identity')
    result = dict(stats, status='AUTHENTICATED_RELEASE_ASSET_LOCAL_SHA_FROZEN_NOT_OFFICIAL_DIGEST',
                  actual_sha256=actual, source_identity=identity, metadata=metadata)
    temp = frozen.with_suffix('.tmp')
    temp.write_text(json.dumps(result, indent=2) + '\n')
    temp.replace(frozen)
    if blob.exists():
        raise ValueError('Release wheel appeared concurrently')
    partial.rename(blob)
    return result
