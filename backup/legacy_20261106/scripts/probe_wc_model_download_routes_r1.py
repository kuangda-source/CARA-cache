#!/usr/bin/env python3
"""Bounded, anonymous model-byte route comparison; never writes model files."""
import hashlib
import json
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


class ProbeDeadline(Exception):
    pass


def deadline(signum, frame):
    raise ProbeDeadline()


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, events):
        self.events = events

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlsplit(newurl)
        if target.scheme != 'https':
            raise ValueError('NON_HTTPS_REDIRECT')
        self.events.append(dict(status=code, destination_host=target.hostname))
        return super().redirect_request(req, fp, 307 if code == 308 else code,
                                        msg, headers, newurl)

    http_error_308 = urllib.request.HTTPRedirectHandler.http_error_302


def probe(asset, route, start, count, request_seconds):
    began = time.time()
    result = dict(repo_id=asset['repo_id'], revision=asset['source_revision'],
                  path=asset['path'], route=route, range_start=start,
                  requested_bytes=count, redirect_chain=[], received_bytes=0,
                  credentials_used=False, model_files_written=0)
    domain = 'hf-mirror.com' if route == 'server_direct_hf_mirror' else 'huggingface.co'
    url = ('https://' + domain + '/' + asset['repo_id'] + '/resolve/' +
           asset['source_revision'] + '/' + urllib.parse.quote(asset['path'], safe='/') +
           '?download=true&wc_route_probe=' + str(int(time.time() * 1e9)))
    proxy = {'https': 'http://127.0.0.1:17897'} if route == 'server_via_existing_Mac_proxy' else {}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxy),
                                         Redirects(result['redirect_chain']))
    signal.setitimer(signal.ITIMER_REAL, request_seconds)
    try:
        req = urllib.request.Request(url, headers={
            'Range': 'bytes=%d-%d' % (start, start + count - 1),
            'Accept-Encoding': 'identity', 'User-Agent': 'CARA-cache-bounded-route-probe-r1'})
        with opener.open(req, timeout=min(12, request_seconds)) as response:
            result.update(http_status=response.status,
                          final_host=urllib.parse.urlsplit(response.geturl()).hostname,
                          header_seconds=time.time() - began,
                          content_range=response.headers.get('Content-Range'))
            expected = 'bytes %d-%d/%d' % (start, start + count - 1, asset['size'])
            if response.status != 206 or response.headers.get('Content-Range') != expected:
                result['status'] = 'REJECTED_HTTP_OR_CONTENT_RANGE'
                return result
            if response.headers.get('Content-Length') != str(count):
                result['status'] = 'REJECTED_CONTENT_LENGTH'
                return result
            hasher = hashlib.sha256()
            while result['received_bytes'] < count:
                block = response.read(min(65536, count - result['received_bytes']))
                if not block:
                    break
                hasher.update(block)
                result['received_bytes'] += len(block)
            result['status'] = 'EXACT_BOUNDED_RANGE_RECEIVED' if result['received_bytes'] == count else 'SHORT_RESPONSE'
            result['sample_sha256'] = hasher.hexdigest()
    except urllib.error.HTTPError as error:
        result.update(status='HTTP_ERROR', http_status=error.code)
    except urllib.error.URLError as error:
        result.update(status='TRANSPORT_ERROR', reason_type=type(error.reason).__name__)
    except ProbeDeadline:
        result['status'] = 'BOUNDED_REQUEST_DEADLINE'
    except Exception as error:
        result.update(status='LOCAL_OR_TRANSPORT_ERROR', error_type=type(error).__name__)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        result['wall_seconds'] = time.time() - began
        if result.get('status') == 'EXACT_BOUNDED_RANGE_RECEIVED':
            result['effective_MiB_per_second_including_headers'] = count / 2**20 / result['wall_seconds']
    return result


def main():
    request = json.load(sys.stdin)
    assert request['kind'] == 'WC_ANONYMOUS_SERVER_MODEL_ROUTE_COMPARISON_R1'
    assets = request['assets']
    assert {x['repo_id'] for x in assets} == {
        'nvidia/Cosmos-Reason1-7B', 'nvidia/Cosmos-Predict2.5-2B', 'nvidia/Cosmos-Guardrail1'}
    assert request['sample_bytes'] == 4 << 20
    assert request['request_seconds'] == 20
    signal.signal(signal.SIGALRM, deadline)
    began = time.time()
    result = dict(status='BOUNDED_SERVER_MODEL_ROUTE_COMPARISON',
                  started_unix=began, request=request, observations=[],
                  full_model_files_downloaded=0, full_model_hash_acceptance=False,
                  credentials_used=False, model_files_written=0,
                  original_worker_changed=False, CUDA_initialized=False,
                  model_weights_loaded=0, GPU_submissions=0, ledger_written=False)
    reason = next(x for x in assets if x['repo_id'] == 'nvidia/Cosmos-Reason1-7B')
    routes = ['server_direct_hf_mirror', 'server_direct_HF', 'server_via_existing_Mac_proxy']
    for round_index in range(2):
        for route in routes if round_index == 0 else list(reversed(routes)):
            if time.time() - began > 170:
                break
            row = probe(reason, route, request['reason_range_start'],
                        request['sample_bytes'], request['request_seconds'])
            row['round'] = round_index + 1
            result['observations'].append(row)
            print(json.dumps(dict(event='bounded_sample', **row)), flush=True)
    for asset in assets:
        if asset['repo_id'] == reason['repo_id'] or time.time() - began > 170:
            continue
        row = probe(asset, 'server_direct_hf_mirror', 0, 1 << 20,
                    request['request_seconds'])
        row['round'] = 'other_fixed_asset_access'
        result['observations'].append(row)
        print(json.dumps(dict(event='bounded_sample', **row)), flush=True)
    result.update(ended_unix=time.time(), wall_seconds=time.time() - began)
    print('ROUTE_PROBE_FINAL_JSON_START', flush=True)
    print(json.dumps(result), flush=True)
    print('ROUTE_PROBE_FINAL_JSON_END', flush=True)


if __name__ == '__main__':
    main()
