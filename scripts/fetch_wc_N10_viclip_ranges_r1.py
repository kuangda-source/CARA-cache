#!/usr/bin/env python3
"""Fetch fixed public checkpoint ranges; preserve failures and verify whole SHA."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

URL = ('https://huggingface.co/OpenGVLab/VBench_Used_Models/resolve/'
       '83290ee59b4e2c0a4d198857edbc79dd186b8d44/ViClip-InternVid-10M-FLT.pth')
SHA = '7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56'
SIZE = 1710545812
NAME = 'ViClip-InternVid-10M-FLT.pth'
CHUNK = 8 * 1024 * 1024
ATTEMPTS = 6


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(8*1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value, *, exclusive=False):
    path = Path(path)
    if exclusive:
        with path.open('x') as handle:
            json.dump(value, handle, indent=2, allow_nan=False)
        return
    temporary = path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    with temporary.open('x') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
    os.replace(temporary, path)


def last_response_headers(text):
    responses = []
    for line in text.splitlines():
        if line.startswith('HTTP/'):
            responses.append(dict(status=int(line.split()[1]), headers={}))
        elif responses and ':' in line:
            key, value = line.split(':', 1)
            responses[-1]['headers'][key.strip().lower()] = value.strip()
    if not responses:
        raise ValueError('No original HTTP response headers')
    return responses[-1]


def one_range(stage, registration, start, end, attempt):
    prefix = stage/'ranges'/('range_'+str(start)+'_'+str(end)+'_attempt'+str(attempt))
    body, headers, receipt = (prefix.with_suffix(suffix) for suffix in ('.bin', '.headers', '.json'))
    assert not any(p.exists() for p in (body, headers, receipt))
    command = [registration['curl_executable'], '--location', '--fail', '--silent', '--show-error',
        '--proxy', 'http://127.0.0.1:7897', '--connect-timeout', '15',
        '--speed-limit', '1024', '--speed-time', '60', '--max-filesize', str(end-start+1),
        '--range', str(start)+'-'+str(end), '-H', 'Accept-Encoding: identity',
        '--dump-header', str(headers), '--output', str(body),
        '--write-out', '%{http_code}\n%{size_download}\n', URL]
    began = time.time()
    result = dict(start=start, end=end, attempt=attempt, accepted=False, started_unix=began,
                  body_ref=str(body.relative_to(stage)), headers_ref=str(headers.relative_to(stage)))
    try:
        call = subprocess.run(command, capture_output=True, text=True)
        response = last_response_headers(headers.read_text(errors='replace')) if headers.is_file() else None
        result.update(curl_exit=call.returncode, stdout=call.stdout, stderr=call.stderr,
            response_status=response['status'] if response else None,
            response_headers={k:v for k,v in response['headers'].items()
                if k in ('etag', 'content-range', 'content-length', 'content-encoding')} if response else {})
        if call.returncode or not response or response['status'] != 206:
            raise ValueError('Original range transport did not complete with HTTP206')
        h = response['headers']
        if (h.get('content-range') != 'bytes '+str(start)+'-'+str(end)+'/'+str(SIZE)
                or h.get('etag') != registration['expected_range_ETag']
                or h.get('content-encoding', 'identity').lower() != 'identity'
                or ('content-length' in h and h['content-length'] != str(end-start+1))
                or not body.is_file() or body.stat().st_size != end-start+1):
            raise ValueError('Original range/length/object identity differs from the pinned resource')
        result.update(accepted=True, body_bytes=body.stat().st_size, body_sha256=sha(body))
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error),
            body_bytes=body.stat().st_size if body.is_file() else 0,
            body_sha256=sha(body) if body.is_file() else None)
    result['wall_seconds'] = time.time()-began
    write(receipt, result, exclusive=True)
    return result, body


def download(stage):
    stage = Path(stage).resolve()
    reg = json.loads((stage/'registration.json').read_text())
    assert reg['purpose'] == 'N10_PINNED_PUBLIC_RESOURCE_ONLY_NO_MODEL_OR_GPU'
    assert reg['expected_weight'] == dict(url=URL, sha256=SHA, bytes=SIZE, name=NAME)
    assert reg['worker_sha256'] == sha(__file__)
    assert reg['chunk_bytes'] == CHUNK and reg['attempts_per_range'] == ATTEMPTS
    assert reg['expected_range_ETag'] and Path(reg['curl_executable']).is_absolute()
    target, partial, resultpath = stage/NAME, stage/(NAME+'.part'), stage/'resource-result.json'
    assert not any(p.exists() for p in (target, partial, resultpath, stage/'ranges'))
    write(stage/'resource-fetch-fence.json', dict(source_revision=reg['source_revision'], unix=time.time()), exclusive=True)
    (stage/'ranges').mkdir()
    started = time.time(); completed = 0; attempts = 0; errors = 0; digest = hashlib.sha256()
    value = dict(status='N10_PINNED_VICLIP_RESOURCE_DOWNLOAD_FAILED_OR_INCOMPLETE_RETAINED',
        exit_code=1, source_revision=reg['source_revision'], started_unix=started, target=str(target),
        public_url=URL, expected_bytes=SIZE, expected_sha256=SHA, chunk_bytes=CHUNK,
        expected_range_count=(SIZE+CHUNK-1)//CHUNK, expected_range_ETag=reg['expected_range_ETag'],
        acquisition='ORIGINAL_CURL_EXACT_HTTP206_RANGES', GPU_submissions=0,
        models_imported=False, weights_loaded=0, ledger_written=False)
    try:
        with partial.open('xb') as handle:
            for start in range(0, SIZE, CHUNK):
                end = min(SIZE-1, start+CHUNK-1)
                assert handle.tell() == completed == start
                accepted = None
                for attempt in range(1, ATTEMPTS+1):
                    disk = os.statvfs(stage)
                    if disk.f_bavail*disk.f_frsize < end-start+1+(1<<30):
                        raise RuntimeError('Preserve received files; insufficient remaining local disk for another range')
                    attempts += 1
                    row, body = one_range(stage, reg, start, end, attempt)
                    if row['accepted']:
                        accepted = row; break
                    errors += 1
                    write(stage/'range-progress.json', dict(status='RANGE_ATTEMPT_FAILED_RETAINED',
                        committed_bytes=completed, completed_ranges=(completed+CHUNK-1)//CHUNK,
                        HTTP_attempts=attempts, failed_HTTP_attempts=errors, current_range=[start,end],
                        current_attempt=attempt, observed_unix=time.time(), last_error=row))
                    if attempt < ATTEMPTS: time.sleep(min(2*attempt, 10))
                if accepted is None:
                    raise RuntimeError('Original range exhausted its registered known-terminal request attempts; no job restart')
                data = body.read_bytes()
                if len(data) != end-start+1 or hashlib.sha256(data).hexdigest() != accepted['body_sha256']:
                    raise ValueError('Completed range changed before ordered assembly')
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
                digest.update(data); completed += len(data)
                write(stage/'range-progress.json', dict(status='ORDERED_RANGES_COMMITTED',
                    committed_bytes=completed, completed_ranges=(completed+CHUNK-1)//CHUNK,
                    expected_bytes=SIZE, expected_ranges=(SIZE+CHUNK-1)//CHUNK,
                    HTTP_attempts=attempts, failed_HTTP_attempts=errors,
                    prefix_sha256=digest.hexdigest(), observed_unix=time.time()))
        if completed != SIZE or partial.stat().st_size != SIZE or digest.hexdigest() != SHA:
            raise ValueError('Whole checkpoint bytes or SHA differs after complete range assembly')
        assert not target.exists()
        partial.rename(target)
        value.update(status='N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME',
                     exit_code=0, actual_bytes=completed, actual_sha256=digest.hexdigest())
    except Exception as error:
        value.update(error_type=type(error).__name__, error=str(error),
            partial_file_preserved=partial.is_file(), actual_bytes_received=completed,
            partial_sha256=digest.hexdigest())
    finally:
        value.update(HTTP_attempts=attempts, failed_HTTP_attempts=errors,
                     completed_ranges=(completed+CHUNK-1)//CHUNK,
                     ended_unix=time.time(), wall_seconds=time.time()-started)
        write(resultpath, value, exclusive=True)
    return value['exit_code']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    raise SystemExit(download(parser.parse_args().stage))
