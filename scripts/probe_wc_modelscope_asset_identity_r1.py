#!/usr/bin/env python3
"""Inspect public ModelScope file identities; sample only a matching frozen asset."""
import hashlib
import json
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def deadline(signum, frame):
    raise TimeoutError()


def main():
    config = json.load(sys.stdin)
    signal.signal(signal.SIGALRM, deadline)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    result = dict(status='BOUNDED_MODELSCOPE_FROZEN_ASSET_IDENTITY_PROBE',
                  started_unix=time.time(), candidates=[], credentials_used=False,
                  model_files_written=0, GPU_submissions=0, ledger_written=False)
    for candidate in config['candidates']:
        model = candidate['modelscope_repo_id']
        row = dict(modelscope_repo_id=model, expected_repo=candidate['expected_repo'],
                   frozen_matches=[], missing_or_different=[], sampled=False)
        result['candidates'].append(row)
        signal.setitimer(signal.ITIMER_REAL, 12)
        try:
            url = ('https://modelscope.cn/api/v1/models/' + model +
                   '/repo/files?Revision=master&Recursive=true')
            with opener.open(url, timeout=10) as response:
                body = response.read((2 << 20) + 1)
                if len(body) > 2 << 20:
                    row['status'] = 'METADATA_SIZE_LIMIT'
                    continue
                metadata = json.loads(body)
                row['api_http_status'] = response.status
            files = (metadata.get('Data') or {}).get('Files') or []
            row.update(api_code=metadata.get('Code'), api_success=metadata.get('Success'),
                       file_entries=len(files), file_schema_keys=list(files[0]) if files else [])
            if not files:
                row['status'] = 'NO_FILE_LIST_VERIFIED'
                continue
            indexed = {x.get('Path') or x.get('Name'): x for x in files}
            for asset in candidate['expected_files']:
                actual = indexed.get(asset['path']) or {}
                digest = actual.get('Sha256') or actual.get('sha256')
                record = dict(path=asset['path'], expected_bytes=asset['size'],
                              actual_bytes=actual.get('Size'), actual_sha256=digest)
                if not asset['git_blob'] and digest == asset['digest'] and actual.get('Size') == asset['size']:
                    row['frozen_matches'].append(record)
                else:
                    record['metadata_present'] = bool(actual)
                    row['missing_or_different'].append(record)
            row['status'] = 'METADATA_IDENTITIES_COMPARED'
        except urllib.error.HTTPError as error:
            row.update(status='HTTP_ERROR', http_status=error.code)
        except urllib.error.URLError as error:
            row.update(status='TRANSPORT_ERROR', reason_type=type(error.reason).__name__)
        except Exception as error:
            row.update(status='METADATA_PROBE_ERROR', error_type=type(error).__name__)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        matched = {x['path'] for x in row['frozen_matches']}
        wanted = config['sample_asset']
        if wanted['path'] not in matched or candidate['expected_repo'] != wanted['repo_id']:
            continue
        sample = dict(requested_bytes=4 << 20, range_start=config['range_start'])
        row['sample'] = sample
        signal.setitimer(signal.ITIMER_REAL, 20)
        began = time.time()
        try:
            url = ('https://modelscope.cn/api/v1/models/' + model + '/repo?' +
                   urllib.parse.urlencode(dict(Revision='master', FilePath=wanted['path'])))
            start = config['range_start']; count = 4 << 20
            request = urllib.request.Request(url, headers={'Range': 'bytes=%d-%d' % (start, start + count - 1),
                                                          'Accept-Encoding': 'identity'})
            with opener.open(request, timeout=12) as response:
                sample.update(http_status=response.status,
                              final_host=urllib.parse.urlsplit(response.geturl()).hostname,
                              content_range=response.headers.get('Content-Range'))
                expected = 'bytes %d-%d/%d' % (start, start + count - 1, wanted['size'])
                if response.status == 206 and response.headers.get('Content-Range') == expected:
                    payload = response.read(count + 1)
                    sample.update(received_bytes=len(payload), sample_sha256=hashlib.sha256(payload).hexdigest())
                    row['sampled'] = len(payload) == count
                else:
                    sample['status'] = 'RANGE_NOT_ACCEPTED'
        except urllib.error.HTTPError as error:
            sample.update(status='HTTP_ERROR', http_status=error.code)
        except Exception as error:
            sample.update(status='SAMPLE_ERROR', error_type=type(error).__name__)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            sample['wall_seconds'] = time.time() - began
    result['ended_unix'] = time.time()
    print(json.dumps(result))


if __name__ == '__main__':
    main()
