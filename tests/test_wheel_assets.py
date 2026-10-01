import hashlib
import io
import json
import urllib.error
import zipfile
import pytest
from wcomr.wheel_assets import inspect_wheel, acquire_release_asset


def wheel_bytes(name='flash_attn', version='2.7.4.post1', tag='cp311-cp311-linux_x86_64'):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('package.dist-info/METADATA', 'Name: %s\nVersion: %s\n' % (name, version))
        archive.writestr('package.dist-info/WHEEL', 'Wheel-Version: 1.0\nTag: %s\n' % tag)
        archive.writestr('package.so', b'actual-test-payload')
    return stream.getvalue()


def row(data):
    return {'package': 'flash-attn', 'version': '2.7.4.post1', 'official_sha256': None,
            'asset_id': 7, 'size': len(data), 'filename': 'flash_attn.whl',
            'url': 'https://github.com/owner/repo/releases/download/tag/flash_attn.whl',
            'release_api': 'https://api.github.com/repos/owner/repo/releases/tags/tag'}


@pytest.mark.parametrize('name,version,tag', [
    ('different-package', '2.7.4.post1', 'cp311-cp311-linux_x86_64'),
    ('flash_attn', '2.6.0', 'cp311-cp311-linux_x86_64'),
    ('flash_attn', '2.7.4.post1', 'cp312-cp312-linux_x86_64'),
])
def test_wrong_runtime_wheel_contract_rejected(tmp_path, name, version, tag):
    valid = wheel_bytes()
    path = tmp_path / 'wheel.whl'
    path.write_bytes(wheel_bytes(name, version, tag))
    with pytest.raises(ValueError):
        inspect_wheel(path, row(valid))


def test_partial_release_resume_freezes_only_local_digest_and_detects_corrupt_cache(monkeypatch, tmp_path):
    data = wheel_bytes()
    source = row(data)
    calls = []
    class Response(io.BytesIO):
        def __init__(self, payload, start=0, fail=False):
            super().__init__(payload)
            self.status = 206
            self.headers = {'Content-Range': 'bytes %d-%d/%d' % (start, len(data)-1, len(data)), 'Content-Length': str(len(data)-start)}
            self.fail, self.reads = fail, 0
        def read(self, count=-1):
            self.reads += 1
            if self.fail and self.reads == 1:
                return super().read(1)
            if self.fail:
                raise urllib.error.URLError('simulated dropped stream')
            return super().read(count)
    def open_url(request, timeout):
        if request.full_url == source['release_api']:
            return io.BytesIO(json.dumps({'assets': [{'id': 7, 'name': source['filename'], 'size': len(data), 'browser_download_url': source['url']}]}).encode())
        start = int(request.headers['Range'].split('=')[1].split('-')[0])
        calls.append(start)
        return Response(data[start:], start, fail=len(calls)==1)
    monkeypatch.setattr('urllib.request.urlopen', open_url)
    result = acquire_release_asset(source, tmp_path)
    assert calls == [0, 1] and result['official_sha256'] is None
    assert result['actual_sha256'] == hashlib.sha256(data).hexdigest()
    assert result['metadata']['crc_checked'] and (tmp_path/source['filename']).read_bytes() == data
    assert acquire_release_asset(source, tmp_path)['cache_hit']
    path = tmp_path/source['filename']
    path.write_bytes(bytes([data[0]^1])+data[1:])
    with pytest.raises(ValueError, match='matching frozen digest'):
        acquire_release_asset(source, tmp_path)


def test_changed_official_asset_identity_rejected_before_cache_write(monkeypatch, tmp_path):
    source = row(wheel_bytes())
    monkeypatch.setattr('urllib.request.urlopen', lambda *a, **k: io.BytesIO(json.dumps({'assets': []}).encode()))
    with pytest.raises(ValueError, match='asset identity changed'):
        acquire_release_asset(source, tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('package,version,actual,expected,passes', [
    ('nvidia-cublas-cu12', '12.1.3.1', 'py3-none-manylinux1_x86_64',
     ['py3-none-manylinux1_x86_64'], True),
    ('triton', '3.0.0', 'cp311-cp311-manylinux2014_x86_64\nTag: cp311-cp311-manylinux_2_17_x86_64',
     ['cp311-cp311-manylinux2014_x86_64', 'cp311-cp311-manylinux_2_17_x86_64'], True),
    ('nvidia-cublas-cu12', '12.1.3.1', 'py3-none-win_amd64',
     ['py3-none-manylinux1_x86_64'], False),
    ('nvidia-cublas-cu12', '12.1.3.1', 'py3-none-manylinux1_x86_64\nTag: py3-none-win_amd64',
     ['py3-none-manylinux1_x86_64'], False),
])
def test_frozen_vendor_tag_set(tmp_path, package, version, actual, expected, passes):
    path = tmp_path / 'wheel.whl'
    path.write_bytes(wheel_bytes(package, version, actual))
    manifest = {'package': package, 'version': version, 'required_tags': expected}
    if passes:
        assert set(inspect_wheel(path, manifest)['tags']) == set(expected)
    else:
        with pytest.raises(ValueError, match='Frozen wheel tag'):
            inspect_wheel(path, manifest)
