#!/usr/bin/env python3
"""Acquire and hash-check only the frozen public auxiliary model subset."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


DOWNLOAD = r'''
import os,sys,json
from pathlib import Path
from huggingface_hub import snapshot_download
m=json.loads(Path(sys.argv[1]).read_text()); cache=Path(sys.argv[2]); job=Path(sys.argv[3])
state=dict(status='PUBLIC_FIXED_SNAPSHOTS_DOWNLOADING',completed=[],GPU_submissions=0)
def save():
 p=job/'download-health.json.tmp';p.write_text(json.dumps(state,indent=2)+'\n');p.replace(job/'download-health.json')
save()
try:
 for item in m['sources']:
  state['current_repo']=item['repo_id'];save()
  snapshot=Path(snapshot_download(repo_id=item['repo_id'],revision=item['revision'],cache_dir=str(cache),
      allow_patterns=['*.json','*.safetensors','*.txt','*.model','*.tiktoken'],max_workers=2,token=False))
  refs=snapshot.parent.parent/'refs';refs.mkdir(exist_ok=True);(refs/'main').write_text(item['revision'])
  state['completed'].append(dict(repo_id=item['repo_id'],revision=item['revision'],snapshot=str(snapshot)));save()
 state['status']='PUBLIC_SNAPSHOTS_DOWNLOADED_HASH_CHECK_PENDING';save()
except BaseException as e:
 state.update(status='PUBLIC_ASSET_DOWNLOAD_FAILED_RETAINED',error_type=type(e).__name__);save();sys.exit(1)
'''

VERIFY = r'''
import sys,json,fnmatch,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('fixed_verifier',sys.argv[1]);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
metadata=json.loads(Path(sys.argv[2]).read_text());cache=Path(sys.argv[3]);out=Path(sys.argv[4]);results=[]
for repo,lock in metadata.items():
 root=cache/('models--'+repo.replace('/','--'))/'snapshots'/lock['revision']
 entries=[e for e in lock['files'] if any(fnmatch.fnmatch(e['path'],p) for p in v.PATTERNS)]
 files=[v.verify(root,e) for e in entries]
 results.append(dict(repo_id=repo,revision=lock['revision'],files=files,all_hashes_pass=all(x['status']=='PASS' for x in files)))
ok=bool(results) and all(x['all_hashes_pass'] for x in results)
out.write_text(json.dumps(dict(status='PUBLIC_FIXED_ASSETS_HASH_VERIFIED_NOT_FULL_MODEL_READY' if ok else 'PUBLIC_ASSET_HASH_FAILURES_RETAINED',
 results=results,model_assets_ready=False,GPU_dispatch_ready=False,GPU_submissions=0),indent=2)+'\n')
sys.exit(0 if ok else 1)
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    m = json.loads(args.manifest.read_text())
    root = Path(m['workspace'])
    job = root / 'bootstrap' / m['run_id']
    assert root == Path('/data20t/gaokuangda/worldcache_workspace')
    assert args.manifest.resolve() == job / 'manifest.json'
    assert not (job / 'result.json').exists()
    assert sha(__file__) == m['worker_sha256']
    for name, digest in m['job_files_sha256'].items():
        assert '/' not in name and sha(job / name) == digest
    sources = json.loads((job / 'sources.json').read_text())['sources']
    assert {s['repo_id'] for s in sources} == {'Qwen/Qwen3Guard-Gen-0.6B', 'google/siglip-so400m-patch14-384'}
    assert m['endpoint'] == 'https://huggingface.co'
    assert 0 < m['maximum_wall_seconds'] <= 5400
    assert 2 <= m['expected_inference_files'] <= 20
    assert os.statvfs(str(root)).f_bavail * os.statvfs(str(root)).f_frsize >= 128 * 2**30 + m['expected_bytes']
    cache = root / 'cache/huggingface/hub'
    cache.mkdir(parents=True, exist_ok=True)
    lock = (cache / '.wc-public-auxiliary-acquisition.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.time()
    state = dict(status='PUBLIC_FIXED_ASSET_ACQUISITION_RUNNING', started_unix=started,
                 source_revision=m['source_revision'], manifest_sha256=sha(args.manifest),
                 worker_sha256=sha(__file__), commands=[], GPU_submissions=0, model_weights_loaded=0,
                 CUDA_initialized=False, ledger_written=False, model_assets_ready=False,
                 production_CPU_accepted=False, GPU_dispatch_ready=False)
    env = root / 'envs/wc-cosmos-py310-cu128-r3'
    variables = dict(CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void', PYTHONDONTWRITEBYTECODE='1',
        HF_ENDPOINT=m['endpoint'], HF_HUB_DISABLE_IMPLICIT_TOKEN='1', HF_HUB_DISABLE_XET='1',
        HF_HUB_OFFLINE='0', HF_HUB_DOWNLOAD_TIMEOUT='60', HF_HUB_ETAG_TIMEOUT='30',
        HF_HOME=str(root / 'cache/huggingface'), HOME='/tmp', TMPDIR='/tmp',
        HTTP_PROXY=m['loopback_proxy'], HTTPS_PROXY=m['loopback_proxy'], ALL_PROXY='',
        OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false')
    container = ['docker', 'run', '--rm', '--read-only', '--network', 'host', '--name', m['run_id'],
        '--label', 'wcomr.manifest=' + state['manifest_sha256'],
        '--user', str(os.getuid()) + ':' + str(os.getgid()), '--cpus', '2', '--memory', '16g',
        '--tmpfs', '/tmp:rw,size=512m', '-v', str(root) + ':' + str(root) + ':ro',
        '-v', str(job) + ':' + str(job) + ':rw', '-v', str(cache) + ':' + str(cache) + ':rw', '-w', str(job)]
    for k, v in variables.items(): container += ['-e', k + '=' + v]
    container += ['--entrypoint', str(env / 'bin/python'), m['container_image_id']]
    try:
        phases = [('download-public-fixed-models', DOWNLOAD, [str(job / 'sources.json'), str(cache), str(job)]),
                  ('verify-all-selected-public-files', VERIFY, [str(job / 'verify_public_assets.py'),
                    str(job / 'integrity.json'), str(cache), str(job / 'public-asset-integrity.json')])]
        for label, code, params in phases:
            state['phase'] = label
            atomic(job / 'health.json', state)
            began = time.time()
            with (job / (label + '.log')).open('xb') as log:
                p = subprocess.run(container + ['-c', code] + params, stdout=log, stderr=subprocess.STDOUT,
                                   timeout=max(1, m['maximum_wall_seconds'] - int(time.time() - started)))
            state['commands'].append(dict(phase=label, exit_code=p.returncode, wall_seconds=time.time() - began))
            assert p.returncode == 0, label
        integrity = json.loads((job / 'public-asset-integrity.json').read_text())
        assert sum(len(x['files']) for x in integrity['results']) == m['expected_inference_files']
        assert all(x['all_hashes_pass'] for x in integrity['results'])
        state.update(status='PUBLIC_FIXED_AUXILIARY_ASSETS_ACCEPTED_NOT_FULL_MODEL_READY', integrity=integrity)
    except BaseException as e:
        state.update(status='PUBLIC_FIXED_ASSET_PREPARATION_FAILED_RETAINED', error_type=type(e).__name__)
        owned = subprocess.run(['docker', 'inspect', m['run_id'], '--format', '{{index .Config.Labels "wcomr.manifest"}}'], capture_output=True, text=True)
        if owned.returncode == 0 and owned.stdout.strip() == state['manifest_sha256']:
            subprocess.run(['docker', 'stop', '--time', '10', m['run_id']], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
    finally:
        state.update(ended_unix=time.time(), wall_seconds=time.time() - started)
        atomic(job / 'health.json', state)
        atomic(job / 'result.json', state)
    return 0 if state['status'] == 'PUBLIC_FIXED_AUXILIARY_ASSETS_ACCEPTED_NOT_FULL_MODEL_READY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
