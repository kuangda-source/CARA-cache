import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

import pytest
from wcomr.ranged_download import transfer


@pytest.fixture
def server():
    data = b'0123456789abcdef'
    settings = {'mode': 'normal', 'requests': [], 'once': True}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            value = self.headers['Range']; settings['requests'].append(value)
            start, end = map(int, value.removeprefix('bytes=').split('-'))
            block = data[start:end + 1]
            if settings['mode'] == 'corrupt': block = bytes([block[0] ^ 1]) + block[1:]
            self.send_response(200 if settings['mode'] == 'ignore' else 206)
            self.send_header('Content-Range', f'bytes {start}-{end}/{len(data)}')
            self.send_header('Content-Length', str(len(block)))
            self.end_headers()
            if settings['mode'] == 'short_once' and settings['once']:
                settings['once'] = False; block = block[:1]
            self.wfile.write(block)
            self.close_connection = True
    http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
    yield f'http://127.0.0.1:{http.server_port}/object', settings, data
    http.shutdown(); thread.join(); http.server_close()


def paths(tmp_path):
    return tmp_path / 'object.incomplete', tmp_path / 'object'


def test_resume_commits_exact_ranges_and_full_digest(server, tmp_path):
    url, settings, data = server; partial, blob = paths(tmp_path)
    partial.write_bytes(data[:3]); records = []
    result = transfer(url, partial, blob, len(data), hashlib.sha256(data).hexdigest(),
                      chunk_bytes=4, progress=records.append)
    assert result['initial_bytes'] == 3 and blob.read_bytes() == data and not partial.exists()
    assert settings['requests'] == ['bytes=3-6', 'bytes=7-10', 'bytes=11-14', 'bytes=15-15']
    assert result['status'] == 'FULL_OBJECT_HASH_PASS' and records[-1]['durable_bytes'] == 16


def test_ignored_range_never_appends_unchecked_response(server, tmp_path):
    url, settings, data = server; settings['mode'] = 'ignore'; partial, blob = paths(tmp_path)
    partial.write_bytes(data[:3])
    with pytest.raises(RuntimeError, match='exhausted at byte 3'):
        transfer(url, partial, blob, len(data), hashlib.sha256(data).hexdigest(), chunk_bytes=4, attempts=2)
    assert partial.read_bytes() == data[:3] and not blob.exists() and len(settings['requests']) == 2


def test_short_response_rolls_back_request_then_retries_same_offset(server, tmp_path):
    url, settings, data = server; settings['mode'] = 'short_once'; partial, blob = paths(tmp_path)
    partial.write_bytes(data[:3]); records = []
    result = transfer(url, partial, blob, len(data), hashlib.sha256(data).hexdigest(),
                      chunk_bytes=4, attempts=2, progress=records.append)
    assert settings['requests'][:2] == ['bytes=3-6'] * 2 and blob.read_bytes() == data
    assert records[0]['durable_bytes'] == 3 and result['retries'] == 1


def test_full_hash_failure_keeps_partial_unpublished(server, tmp_path):
    url, settings, data = server; settings['mode'] = 'corrupt'; partial, blob = paths(tmp_path)
    with pytest.raises(ValueError, match='digest differs'):
        transfer(url, partial, blob, len(data), hashlib.sha256(data).hexdigest(), chunk_bytes=4)
    assert partial.stat().st_size == len(data) and not blob.exists()


def test_existing_valid_blob_skips_network(server, tmp_path):
    url, settings, data = server; partial, blob = paths(tmp_path); blob.write_bytes(data)
    result = transfer(url, partial, blob, len(data), hashlib.sha256(data).hexdigest())
    assert result['status'] == 'EXISTING_BLOB_FULL_HASH_PASS' and not settings['requests']


def test_git_blob_identity_supported(server, tmp_path):
    url, settings, data = server; partial, blob = paths(tmp_path)
    digest = hashlib.sha1(('blob %d\0' % len(data)).encode() + data).hexdigest()
    transfer(url, partial, blob, len(data), digest, chunk_bytes=4, git_blob=True)
    assert blob.read_bytes() == data
