#!/usr/bin/env python3
"""Acquire one public pinned CPU scoring resource; never import metric models."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

URL = ('https://huggingface.co/OpenGVLab/VBench_Used_Models/resolve/'
       '83290ee59b4e2c0a4d198857edbc79dd186b8d44/ViClip-InternVid-10M-FLT.pth')
SHA = '7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56'
SIZE = 1710545812
NAME = 'ViClip-InternVid-10M-FLT.pth'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    args = parser.parse_args()
    stage = args.stage.resolve()
    registration = json.loads((stage/'registration.json').read_text())
    assert registration['purpose'] == 'N10_PINNED_PUBLIC_RESOURCE_ONLY_NO_MODEL_OR_GPU'
    assert registration['expected_weight'] == dict(url=URL,sha256=SHA,bytes=SIZE,name=NAME)
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == registration['worker_sha256']
    target, partial, result = stage/NAME, stage/(NAME+'.part'), stage/'resource-result.json'
    assert not any(p.exists() for p in (target, partial, result))
    started = time.time(); count = 0; value = hashlib.sha256(); exit_code = 1
    observation = dict(status='N10_PUBLIC_PINNED_RESOURCE_DOWNLOAD_RUNNING',
        source_revision=registration['source_revision'],started_unix=started,
        public_url=URL,expected_sha256=SHA,expected_bytes=SIZE,target=str(target),
        weights_loaded=0,models_imported=False,GPU_submissions=0,ledger_written=False)
    try:
        request = urllib.request.Request(URL, headers={'User-Agent':'WorldCache-metric-resource-preparation/1'})
        with urllib.request.urlopen(request,timeout=60) as response,partial.open('xb') as handle:
            observation['response_status'] = response.status
            observation['content_length_header'] = response.headers.get('Content-Length')
            while True:
                block = response.read(4*1024*1024)
                if not block:break
                count += len(block)
                if count > SIZE:raise ValueError('Public checkpoint response exceeds registered exact size')
                value.update(block);handle.write(block)
            handle.flush();os.fsync(handle.fileno())
        if count != SIZE or value.hexdigest() != SHA:
            raise ValueError('Public checkpoint bytes or whole SHA differ from the registered original resource')
        partial.rename(target)
        observation.update(status='N10_PINNED_VICLIP_RESOURCE_BYTES_ACCEPTED_NOT_MODEL_RUNTIME',
                           actual_bytes=count,actual_sha256=value.hexdigest(),exit_code=0)
        exit_code = 0
    except Exception as error:
        observation.update(status='N10_PINNED_VICLIP_RESOURCE_DOWNLOAD_FAILED_OR_INCOMPLETE_RETAINED',
            error_type=type(error).__name__,error=str(error),partial_file_preserved=partial.exists(),
            actual_bytes_received=count,partial_sha256=value.hexdigest(),exit_code=1)
    finally:
        observation['ended_unix']=time.time();observation['wall_seconds']=time.time()-started
        with result.open('x') as handle:json.dump(observation,handle,indent=2,allow_nan=False)
    raise SystemExit(exit_code)


if __name__ == '__main__':main()
