"""Bounded CPU resolution/install into the already-created isolated L0 venv.

Use an external timeout and a new output directory per phase. The four
provenance-audited binary wheels are always explicit local requirements.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def inventory(python):
    command = [str(python), '-I', '-c',
               'import sys,json;from importlib.metadata import distributions;print(json.dumps({"prefix":sys.prefix,"base_prefix":sys.base_prefix,"packages":sorted((d.metadata["Name"],d.version) for d in distributions())}))']
    return json.loads(subprocess.check_output(command, text=True, timeout=20))


def main():
    started = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--wheel-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=['resolve', 'install'], required=True)
    parser.add_argument('--resolution', type=Path)
    parser.add_argument('--allow-pure-antlr-source', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    environment = root / '.sync/l0-native-env-r1'
    python = environment / 'bin/python'
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or args.output.exists():
        raise ValueError('Use CPU-only visibility and a new phase identity')
    if args.output.resolve().parent != root / 'outputs':
        raise ValueError('Output must be a direct child of the L0 outputs directory')
    lock = (root / '.sync/l0-native-env.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    args.output.mkdir()
    before = inventory(python)
    if Path(before['prefix']).resolve() != environment or before['prefix'] == before['base_prefix']:
        raise ValueError('Wrong isolated interpreter')
    budget = (root / 'reports/budget.json').read_bytes()
    fixed = [Path(__file__).resolve(), args.pins, args.wheel_audit]
    sources = {str(p): sha(p) for p in fixed}
    state = {'pid': os.getpid(), 'started_unix': started, 'status': 'PREPARING',
             'mode': args.mode, 'source_sha256': sources, 'environment_root': str(environment),
             'inventory_before': before, 'gpu_workload_started': False,
             'cpu_max_wall_seconds': 600 if args.mode == 'resolve' else 1800}

    def save():
        target = args.output / 'receipt.json'
        temp = target.with_suffix('.tmp')
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(target)

    save()
    child = None

    def interrupted(signum, frame):
        raise InterruptedError('Owned phase received termination')

    signal.signal(signal.SIGTERM, interrupted)
    try:
        pins = json.loads(args.pins.read_text())
        audit = json.loads(args.wheel_audit.read_text())
        if audit['status'] != 'ALL4_FRESH_PAYLOAD_AUDIT_PASS_NOT_INSTALLED_OR_IMPORTED' or len(audit['files']) != 4:
            raise ValueError('Complete binary payload audit required')
        cache = root / '.sync/l0-native-wheel-cache'
        binaries = {}
        for row in audit['files']:
            path = cache / row['filename']
            if not path.is_file() or path.is_symlink() or path.stat().st_size != row['size'] or sha(path) != row['actual_sha256']:
                raise ValueError('Audited binary bytes differ')
            binaries[row['metadata']['package'].lower().replace('_', '-')] = path
        if set(binaries) != {'torch', 'torchvision', 'torchaudio', 'flash-attn'}:
            raise ValueError('Binary scope differs')
        uv = '/home/gaokuangda/.local/bin/uv'
        binary_options = ['--only-binary=:all:']
        if args.allow_pure_antlr_source:
            binary_options += ['--no-binary=antlr4-python3-runtime']
        if args.mode == 'resolve':
            if before['packages']:
                raise ValueError('Resolution must preserve the empty environment')
            lines = [p for p in pins['pins'] if p.split('==')[0] not in binaries]
            lines += [name + ' @ ' + path.as_uri() for name, path in binaries.items()]
            source = args.output / 'requirements.in'
            source.write_text('\n'.join(lines) + '\n')
            result = args.output / 'requirements.txt'
            command = [uv, 'pip', 'compile', str(source), '--python', str(python),
                       '--no-config', '--generate-hashes', '--no-header', '--no-annotate', '--no-python-downloads',
                       '--default-index', 'https://pypi.org/simple', '--output-file', str(result)] + binary_options
        else:
            if args.resolution is None:
                raise ValueError('Frozen dependency resolution receipt required')
            resolved = json.loads((args.resolution / 'receipt.json').read_text())
            result = args.resolution / 'requirements.txt'
            if resolved['status'] != 'RESOLVED_HASH_LOCK_NOT_INSTALLED' or sha(result) != resolved['requirements_sha256']:
                raise ValueError('Resolution identity differs')
            if resolved['source_sha256'][str(args.pins)] != sources[str(args.pins)] or resolved['source_sha256'][str(args.wheel_audit)] != sources[str(args.wheel_audit)]:
                raise ValueError('Resolution inputs differ')
            command = [uv, 'pip', 'sync', str(result), '--python', str(python), '--require-hashes',
                       '--no-config', '--no-python-downloads', '--default-index', 'https://pypi.org/simple', '--link-mode', 'copy'] + binary_options
        state.update(command=command, status='RUNNING', pure_antlr_source_allowed=args.allow_pure_antlr_source)
        env = {k: v for k, v in os.environ.items() if not k.startswith(('UV_', 'PIP_'))}
        env.update(UV_NO_PROGRESS='1', UV_HTTP_TIMEOUT='30', UV_HTTP_RETRIES='2',
                   UV_PYTHON_DOWNLOADS='never', PIP_DISABLE_PIP_VERSION_CHECK='1')
        with (args.output / 'phase.log').open('x') as log:
            child = subprocess.Popen(command, cwd=args.output, env=env, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                                     pass_fds=(lock.fileno(),))
            state['child_pid'] = child.pid
            save()
            child.wait(timeout=max(1, state['cpu_max_wall_seconds'] - (time.time() - started) - 45))
        state['exit_code'] = child.returncode
        if child.returncode:
            raise RuntimeError('Bounded dependency phase failed; inspect durable phase log')
        state['requirements_sha256'] = sha(result)
        state['status'] = 'RESOLVED_HASH_LOCK_NOT_INSTALLED' if args.mode == 'resolve' else 'INSTALLED_HASH_LOCK_NATIVE_IMPORT_ABI_PENDING'
    except BaseException as error:
        state.update(status='DEPENDENCY_PHASE_FAILED_OR_INTERRUPTED', error_type=type(error).__name__)
    finally:
        if child is not None and child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        state.update(exit_code=child.returncode if child else None, ended_unix=time.time(),
                     wall_seconds=time.time() - started, inventory_after=inventory(python), budget_unchanged=budget == (root / 'reports/budget.json').read_bytes(),
                     source_unchanged=all(sha(Path(p)) == h for p, h in sources.items()))
        state['environment_unchanged'] = state['inventory_before'] == state['inventory_after']
        if not state['budget_unchanged'] or not state['source_unchanged'] or (args.mode == 'resolve' and not state['environment_unchanged']):
            state['status'] = 'DEPENDENCY_PHASE_FAILED_IDENTITY_OR_STATE_CHANGED'
        save()
    if state['status'].startswith('DEPENDENCY_PHASE_FAILED'):
        raise SystemExit(1)
    print(json.dumps({'status': state['status'], 'receipt': str(args.output / 'receipt.json')}))


if __name__ == '__main__':
    main()
