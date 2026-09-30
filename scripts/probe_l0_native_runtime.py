"""Durable CPU-only check of pinned native Wan code, dependencies and interfaces.

Run under an external CPU timeout. Meta parameters test architecture only;
this probe never loads DiT/T5/VAE weights or creates a CUDA context.
"""
import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
import time


def digest(path, git_blob=False):
    data = path.read_bytes()
    return (hashlib.sha1(('blob %d\0' % len(data)).encode() + data).hexdigest()
            if git_blob else hashlib.sha256(data).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-lock', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--environment-root', type=Path, required=True)
    parser.add_argument('--environment-lock', type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('HF_HUB_OFFLINE') != '1':
        raise ValueError('Use empty CUDA visibility and offline model access')
    if args.output.exists():
        raise ValueError('Choose a new probe receipt identity')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    source = args.source.resolve()
    state = {'pid': os.getpid(), 'started_unix': time.time(), 'status': 'STARTED',
             'gpu_workload_started': False, 'python': sys.version,
             'interpreter': sys.executable, 'environment_prefix': sys.prefix,
             'scope': 'Full native package import, meta DiT architecture, real tokenizer and scoped method construction. No full weights, forward, VAE, GPU or task parity.'}

    def save():
        temp = args.output.with_suffix('.tmp')
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(args.output)

    save()
    try:
        if Path(sys.prefix).resolve() != args.environment_root.resolve() or sys.prefix == sys.base_prefix:
            raise ValueError('Use the explicitly selected isolated virtual environment')
        lock = json.loads(args.source_lock.read_text())
        if lock['upstream_commit'] != '42bf4cfaa384bc21833865abc2f9e6c0e67233dc':
            raise ValueError('Unexpected native source revision')
        expected = {r['path'] for r in lock['files']}
        if not {'wan/__init__.py', 'wan/textimage2video.py', 'wan/modules/model.py',
                'wan/modules/tokenizers.py', 'requirements.txt', 'generate.py'} <= expected:
            raise ValueError('Incomplete runtime source lock')
        for row in lock['files']:
            relative = Path(row['path'])
            if relative.is_absolute() or '..' in relative.parts or digest(source / relative) != row['sha256']:
                raise ValueError('Native source digest differs: ' + row['path'])
        from packaging.requirements import Requirement
        from importlib import metadata
        requirements = []
        for raw in (source / 'requirements.txt').read_text().splitlines():
            if not raw.strip() or raw.startswith('#'):
                continue
            req = Requirement(raw)
            try:
                version = metadata.version(req.name)
                satisfies = req.specifier.contains(version, prereleases=True)
            except metadata.PackageNotFoundError:
                version, satisfies = None, False
            requirements.append({'requirement': raw, 'version': version, 'satisfies': satisfies})
        state.update(status='SOURCE_AND_DEPENDENCIES_CHECKED', requirements=requirements,
                     source_files=len(expected), source_sha256=digest(args.source_lock))
        save()
        if not all(r['satisfies'] for r in requirements):
            raise ValueError('Official native dependency requirements are not all satisfied')
        environment = json.loads(args.environment_lock.read_text())
        pinned = []
        for raw in environment['pins'] + ['flash-attn==' + environment['flash_attention_version']]:
            req = Requirement(raw)
            version = metadata.version(req.name)
            if not req.specifier.contains(version, prereleases=True):
                raise ValueError('Selected native environment pin differs: ' + raw)
            pinned.append({'requirement': raw, 'installed_version': version})
        state.update(environment_lock_sha256=digest(args.environment_lock), pinned_packages=pinned)
        save()
        sys.path.insert(0, str(source))
        import torch
        if torch.cuda.is_initialized():
            raise ValueError('Unexpected CUDA initialization')
        if torch._C._GLIBCXX_USE_CXX11_ABI != environment['torch_cpp_abi']:
            raise ValueError('Actual Torch ABI differs from selected FlashAttention binary')
        state.update(status='TORCH_IMPORT_ABI_PASS_FULL_WAN_IMPORT_PENDING',
                     torch_version=torch.__version__, torch_cpp_abi=torch._C._GLIBCXX_USE_CXX11_ABI,
                     cuda_initialized=False)
        save()
        import wan
        from wan.textimage2video import WanTI2V
        from wan.modules.model import WanModel
        from wan.modules.tokenizers import HuggingfaceTokenizer
        from wcomr.wan_t2v_conditional import conditional_t2v_scope
        if torch.cuda.is_initialized():
            raise ValueError('Unexpected CUDA initialization')
        origins = {}
        for name, module in tuple(sys.modules.items()):
            if name == 'wan' or name.startswith('wan.'):
                path = Path(module.__file__).resolve() if getattr(module, '__file__', None) else None
                if path is None or source not in path.parents or str(path.relative_to(source)) not in expected:
                    raise ValueError('Imported native module origin differs: ' + name)
                origins[name] = str(path.relative_to(source))
        state.update(status='FULL_NATIVE_IMPORT_PASS', module_origins=origins,
                     torch_version=torch.__version__, torch_cpp_abi=torch._C._GLIBCXX_USE_CXX11_ABI,
                     cuda_initialized=False)
        save()
        protocol = json.loads(args.protocol.read_text())
        selected = {'config.json', protocol['index']} | {
            r['path'] for r in protocol['base_files'] if r['path'].startswith('google/')}
        for row in protocol['base_files']:
            if row['path'] in selected:
                path = args.base / row['path']
                want = row['lfs']['oid'] if row.get('lfs') else row['git_blob_oid']
                if path.stat().st_size != row['size'] or digest(path, not bool(row.get('lfs'))) != want:
                    raise ValueError('Selected base metadata/tokenizer digest differs: ' + row['path'])
        config = json.loads((args.base / 'config.json').read_text())
        parameters = inspect.signature(WanModel.__init__).parameters
        if any(k not in parameters and not k.startswith('_') for k in config):
            raise ValueError('Unexpected DiT config field')
        with torch.device('meta'):
            model = WanModel(**{k: v for k, v in config.items() if k in parameters})
        state_dict = model.state_dict()
        index = json.loads((args.base / protocol['index']).read_text())['weight_map']
        headers = {}
        for filename in protocol['shards']:
            with (args.base / filename).open('rb') as stream:
                length = int.from_bytes(stream.read(8), 'little')
                header = json.loads(stream.read(length))
            entries = {k: r for k, r in header.items() if k != '__metadata__'}
            if headers.keys() & entries.keys() or any(index.get(k) != filename for k in entries):
                raise ValueError('Base header shard coverage differs')
            headers.update(entries)
        if set(state_dict) != set(index) or set(state_dict) != set(headers):
            raise ValueError('Actual official meta architecture keys differ from real base')
        if any(not t.is_meta or list(t.shape) != headers[k]['shape'] for k, t in state_dict.items()):
            raise ValueError('Actual meta architecture shape/device differs')
        state.update(status='META_ARCHITECTURE_KEYS_AND_SHAPES_PASS',
                     meta_tensor_count=len(state_dict), weights_loaded=False)
        save()
        tokenizer = HuggingfaceTokenizer(str(args.base / 'google/umt5-xxl'),
                                        seq_len=512, clean='whitespace', local_files_only=True)
        ids, mask = tokenizer(['A red ball rolls across a table.'], return_mask=True)
        if ids.shape != (1, 512) or mask.shape != ids.shape or ids.device.type != 'cpu' or not mask.any():
            raise ValueError('Actual tokenizer output contract differs')
        original = WanTI2V.t2v
        with conditional_t2v_scope(WanTI2V, source / 'wan/textimage2video.py') as adaptation:
            if WanTI2V.t2v is original or inspect.signature(WanTI2V.t2v) != inspect.signature(original):
                raise ValueError('Real native method adaptation did not preserve signature')
        if WanTI2V.t2v is not original:
            raise ValueError('Real native method was not restored')
        for row in lock['files']:
            if digest(source / row['path']) != row['sha256']:
                raise ValueError('Source changed during probe')
        if torch.cuda.is_initialized():
            raise ValueError('Unexpected CUDA initialization')
        state.update(status='CPU_NATIVE_IMPORT_META_ARCHITECTURE_TOKENIZER_AND_SCOPE_PASS_NOT_MODEL_GPU',
                     finished_unix=time.time(), tokenizer_shape=list(ids.shape),
                     tokenizer_valid_tokens=int(mask.sum()), tokenizer_ids_sha256=hashlib.sha256(ids.numpy().tobytes()).hexdigest(),
                     adaptation=adaptation, source_unchanged=True, cuda_initialized=False)
        save()
    except BaseException as error:
        state.update(status='CPU_NATIVE_PROBE_FAILED_OR_INTERRUPTED', finished_unix=time.time(),
                     error_type=type(error).__name__, error=str(error))
        save()
        raise
    print(json.dumps({'status': state['status'], 'receipt': str(args.output)}))


if __name__ == '__main__':
    main()
