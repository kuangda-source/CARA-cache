"""Download pinned auxiliary weights to an explicitly supplied project cache.

No GPU work. Existing shared caches are never written. The caller supplies a
wall-clock timeout. Snapshot manifests preserve sizes/hashes via HF blob names.
"""
import argparse
import json
import os
from pathlib import Path
import time

parser = argparse.ArgumentParser()
parser.add_argument('--manifest', type=Path, required=True)
parser.add_argument('--cache', type=Path, required=True)
parser.add_argument('--receipt', type=Path, required=True)
parser.add_argument('--endpoint', default=None)
parser.add_argument('--authenticated', action='store_true', help='Use existing HF login, official endpoint only')
args = parser.parse_args()
lock = json.loads(args.manifest.read_text())
os.environ['CUDA_VISIBLE_DEVICES'] = ''
endpoint = args.endpoint or lock['endpoint']
if args.authenticated and endpoint.rstrip('/') != 'https://huggingface.co':
    raise SystemExit('Authenticated access is allowed only to the official Hugging Face endpoint')
os.environ['HF_ENDPOINT'] = endpoint
os.environ['HF_HUB_CACHE'] = str(args.cache)
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
from huggingface_hub import snapshot_download

args.cache.mkdir(parents=True, exist_ok=True)
args.receipt.parent.mkdir(parents=True, exist_ok=True)
state = {'stage': 'F0_AUXILIARY_DOWNLOAD', 'pid': os.getpid(), 'started_unix': time.time(),
         'gpu_workload_started': False, 'status': 'RUNNING', 'completed': []}
def save():
    tmp = args.receipt.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n')
    tmp.replace(args.receipt)
save()
try:
    for item in lock['sources']:
        state['current'] = item['repo_id']; save()
        patterns = (['blocklist/**', 'face_blur_filter/**', 'video_content_safety_filter/safety_filter.pt', 'README.md']
                    if item['repo_id'] == 'nvidia/Cosmos-Guardrail1'
                    else ['*.json', '*.safetensors', '*.txt', '*.model', '*.tiktoken'])
        path = Path(snapshot_download(repo_id=item['repo_id'], revision=item['revision'],
                                     cache_dir=args.cache, allow_patterns=patterns, max_workers=2, token=True if args.authenticated else False))
        files = [{'path': str(p.relative_to(path)), 'bytes': p.stat().st_size,
                  'blob': p.resolve().name} for p in sorted(path.rglob('*')) if p.is_file()]
        if not files: raise RuntimeError('Empty snapshot: '+item['repo_id'])
        # Offline name-based loading uses this project-local pinned main ref.
        refs = path.parent.parent / 'refs'; refs.mkdir(exist_ok=True)
        (refs / 'main').write_text(item['revision'])
        state['completed'].append({'repo_id': item['repo_id'], 'revision': item['revision'],
                                    'snapshot': str(path), 'files': files}); save()
    state['status'] = 'DOWNLOADED_NOT_LOAD_VALIDATED'
except Exception as exc:
    state['status'] = 'RESOURCE_BLOCKED'; state['error'] = str(exc)
    raise
finally:
    state['ended_unix'] = time.time(); save()
