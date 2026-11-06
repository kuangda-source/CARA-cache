#!/usr/bin/env python3
"""Explicitly authorized home-storage maintenance; never imports a model or CUDA.

The only destructive sources are the five pinned user-owned paths below.
Model copies are fully hashed before an atomic directory/symlink exchange.
Private per-file manifests remain on the server, outside Git.
"""
import argparse
import ctypes
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import time

HOME = Path('/home/gaokuangda')
DATA = HOME / 'data/gkd'
STORE = DATA / 'home_storage'
PROJECT = DATA / 'worldcache_omr'
NANO = HOME / 'cosmos3_nano/models'
CACHES = {'pip': HOME / '.cache/pip', 'uv': HOME / '.cache/uv'}
MODELS = {'huggingface': HOME / '.cache/huggingface', 'wan': HOME / 'da_str_assets'}
SOURCES = [NANO] + list(CACHES.values()) + list(MODELS.values())


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.writing')
    with temp.open('w') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
    temp.chmod(0o600)
    temp.replace(path)


def capacity():
    out = {}
    for p in [HOME, DATA]:
        s = os.statvfs(p)
        out[str(p)] = dict(available_bytes=s.f_bavail*s.f_frsize,
                           used_bytes=(s.f_blocks-s.f_bfree)*s.f_frsize)
    return out


def du(path):
    p = subprocess.run(['du', '-x', '-B1', '-s', '--', str(path)],
                       capture_output=True, text=True, check=True)
    return int(p.stdout.split('\t', 1)[0])


def exchange(left, right):
    libc = ctypes.CDLL(None, use_errno=True)
    fn = libc.renameat2
    fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    fn.restype = ctypes.c_int
    if fn(-100, os.fsencode(left), -100, os.fsencode(right), 2):
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e), str(left))


def manifest(base, progress=None):
    result = {}
    for dp, dirs, files in os.walk(base, followlinks=False):
        for n in sorted(dirs + files):
            p = Path(dp) / n
            s = p.lstat()
            key = str(p.relative_to(base))
            if stat.S_ISLNK(s.st_mode):
                value = dict(type='symlink', target=os.readlink(p))
            elif stat.S_ISDIR(s.st_mode):
                value = dict(type='directory', mode=stat.S_IMODE(s.st_mode))
            elif stat.S_ISREG(s.st_mode):
                before = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
                value = dict(type='file', mode=stat.S_IMODE(s.st_mode),
                             bytes=s.st_size, sha256=digest(p))
                t = p.stat()
                if before != (t.st_dev, t.st_ino, t.st_size, t.st_mtime_ns):
                    raise RuntimeError('Source/destination changed during hashing: ' + key)
                if progress:
                    progress(s.st_size)
            else:
                raise RuntimeError('Unexpected special file in model assets: ' + key)
            result[key] = value
        dirs[:] = [d for d in dirs if not (Path(dp) / d).is_symlink()]
    return result


def live_cache_users():
    hits = []
    prefixes = tuple(str(p) + '/' for p in CACHES.values())
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():
            continue
        try:
            if p.stat().st_uid != os.getuid():
                continue
            args = (p / 'cmdline').read_bytes().split(b'\0')
            package = any(a in (b'pip', b'pip3', b'uv') or a.endswith((b'/pip', b'/pip3', b'/uv'))
                          for a in args)
            if package:
                hits.append(dict(pid=int(p.name), reason='package manager active'))
            for fd in (p / 'fd').iterdir():
                try:
                    if os.readlink(fd).startswith(prefixes):
                        hits.append(dict(pid=int(p.name), reason='open package cache'))
                except OSError:
                    pass
            for line in (p / 'maps').read_text().splitlines():
                a = line.split(None, 5)
                if len(a) == 6 and a[5].startswith(prefixes):
                    hits.append(dict(pid=int(p.name), reason='mapped package cache'))
        except (OSError, ProcessLookupError):
            continue
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ops-dir', type=Path, required=True)
    ap.add_argument('--authorization', type=Path, required=True)
    a = ap.parse_args()
    ops = a.ops_dir.resolve()
    assert ops.parent == (PROJECT / '.sync').resolve() and ops.name.startswith('storage-maintenance-')
    ops.mkdir(mode=0o700, exist_ok=True)
    authorization = json.loads(a.authorization.read_text())
    assert authorization['status'] == 'HUMAN_AUTHORIZED_STORAGE_MAINTENANCE'
    assert authorization['sources'] == [str(p) for p in SOURCES]
    assert authorization['no_new_GPU_until_storage_acceptance'] is True
    pre = authorization['preflight']
    assert pre['user'] == 'gaokuangda' and pre['uid'] == os.getuid()
    assert not pre['cache_references'] and not pre['active_cache_or_package_processes']
    assert not pre['relevant_environment_scan_errors']
    assert Path(__file__).resolve() == ops / 'maintain_wc_user_storage_r1.py'
    assert digest(__file__) == authorization['script_sha256']
    lock = (ops / 'maintenance.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with (ops / 'execution.fence').open('x') as f:
        f.write(authorization['run_id'] + '\n')
    result = dict(status='RUNNING', started_unix=time.time(), pid=os.getpid(),
                  run_id=authorization['run_id'], script_sha256=digest(__file__),
                  original_experiment_processes_touched=False, new_GPU_submissions=0,
                  generator_or_environment_reinstalled=False, actions=[], hashed_bytes=0)
    def update(phase):
        result.update(phase=phase, updated_unix=time.time())
        write(ops / 'result.json', result)
    def progress(n):
        result['hashed_bytes'] += n
        write(ops / 'result.json', result)
    try:
        update('FRESH_SOURCE_AND_SAFETY_CHECKS')
        for p in SOURCES:
            s = p.lstat(); registered = pre['sources'][str(p)]
            assert stat.S_ISDIR(s.st_mode) and not p.is_symlink() and s.st_uid == os.getuid()
            assert (s.st_dev, s.st_ino) == (registered['device'], registered['inode'])
        assert NANO.resolve() == NANO
        assert STORE.resolve().is_relative_to(DATA.resolve())
        assert HOME.stat().st_dev != DATA.stat().st_dev
        assert not live_cache_users(), 'An active package operation must finish first'
        for pid, ticks in authorization['original_handles']:
            path = Path('/proc') / str(pid) / 'stat'
            if path.exists():
                fields = path.read_text().rsplit(')', 1)[1].split()
                assert int(fields[19]) != ticks or fields[0] in ('Z', 'X'), 'Original task still live'
        result['capacity_before'] = capacity()
        result['home_allocated_before'] = du(HOME)
        result['source_allocated_before'] = {str(p): du(p) for p in SOURCES}
        required = sum(result['source_allocated_before'][str(p)] for p in MODELS.values())
        assert os.statvfs(DATA).f_bavail * os.statvfs(DATA).f_frsize > required + 20*1024**3
        for name in CACHES:
            assert not (STORE / 'cache' / name).exists()
        for name in MODELS:
            assert not (STORE / 'models' / name).exists()
        preserved = [HOME / '.local/bin/uv', HOME / '.local/bin/uvx']
        for env in pre['environment_roots_checked']:
            if env.startswith((str(HOME) + '/', str(DATA.resolve()) + '/')):
                preserved += [Path(env) / 'bin/python', Path(env) / 'bin/python3', Path(env) / 'pyvenv.cfg']
        preserved = [p for p in preserved if p.is_file()]
        fingerprints = {str(p): digest(p) for p in preserved}
        result['preserved_runtime_files_before'] = fingerprints
        STORE.mkdir(mode=0o755, exist_ok=True)
        assert STORE.stat().st_uid == os.getuid()
        # A bounded same-filesystem fixture proves atomic exchange before any deletion.
        test = HOME / '.cache' / ('.storage-exchange-test-' + authorization['run_id'])
        test.mkdir(); (test / 'dir').mkdir(); (test / 'dir/file').write_bytes(b'proof')
        (test / 'link').symlink_to('verified-target')
        exchange(test / 'dir', test / 'link')
        assert (test / 'dir').is_symlink() and (test / 'link/file').read_bytes() == b'proof'
        shutil.rmtree(test)
        result['atomic_exchange_fixture_passed'] = True

        update('DELETE_AUTHORIZED_INCOMPLETE_NANO_MODEL_DIRECTORY')
        nano_meta = {str(p.relative_to(NANO)): p.read_text() for p in NANO.rglob('*.index.json')}
        write(ops / 'nano-index-metadata-retained.json', nano_meta)
        shutil.rmtree(NANO)
        assert not NANO.exists()
        result['actions'].append(dict(kind='DELETE_INCOMPLETE_NANO_MODELS', source=str(NANO),
                                      download_scripts_and_records_retained=True))

        update('REBUILD_PACKAGE_CACHES_ON_DATA_DISK')
        for name, source in CACHES.items():
            assert not live_cache_users()
            target = STORE / 'cache' / name
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            target.mkdir(mode=stat.S_IMODE(source.stat().st_mode))
            probe = target / '.write-probe'; probe.write_bytes(b'ok'); probe.unlink()
            backup = source.with_name(source.name + '.pre-maintenance-' + authorization['run_id'])
            assert not backup.exists() and not backup.is_symlink()
            backup.symlink_to(target, target_is_directory=True)
            exchange(source, backup)
            assert source.is_symlink() and os.path.samefile(source, target)
            shutil.rmtree(backup)
            result['actions'].append(dict(kind='EMPTY_PACKAGE_CACHE_REBUILT', source=str(source),
                                          target=str(target), source_is_compatible_symlink=True))
            update('REBUILT_' + name.upper())

        for name, source in MODELS.items():
            update('COPY_' + name.upper())
            target = STORE / 'models' / name
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            incoming = target.with_name(name + '.incoming-' + authorization['run_id'])
            assert not target.exists() and not target.is_symlink() and not incoming.exists()
            incoming.mkdir(mode=0o700)
            cmd = ['rsync', '-aH', '--stats', '--', str(source) + '/', str(incoming) + '/']
            with (ops / ('rsync-' + name + '.log')).open('wb') as log:
                p = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
            assert p.returncode == 0, 'Model asset copy failed; original remains intact'
            update('HASH_SOURCE_' + name.upper()); before = manifest(source, progress)
            update('HASH_DESTINATION_' + name.upper()); after = manifest(incoming, progress)
            assert before == after, 'Copied model tree differs; original remains intact'
            write(ops / (name + '-private-file-manifest.json'), before)
            incoming.replace(target)
            backup = source.with_name(source.name + '.pre-maintenance-' + authorization['run_id'])
            assert not backup.exists() and not backup.is_symlink()
            backup.symlink_to(target, target_is_directory=True)
            update('ATOMIC_PATH_EXCHANGE_' + name.upper()); exchange(source, backup)
            assert source.is_symlink() and os.path.samefile(source, target)
            for rel, meta in before.items():
                old_path = source / rel; new_path = target / rel
                assert old_path.lstat().st_ino == new_path.lstat().st_ino
                assert old_path.lstat().st_dev == new_path.lstat().st_dev
                if meta['type'] == 'symlink':
                    assert os.readlink(old_path) == meta['target']
                    assert old_path.exists() == (backup / rel).exists()
            for alias in pre.get('model_aliases', []):
                old_real = Path(alias['realpath'])
                if old_real == source or old_real.is_relative_to(source):
                    p = Path(alias['path'])
                    assert os.readlink(p) == alias['link_text'] and p.exists()
                    assert p.resolve() == (target / old_real.relative_to(source)).resolve()
            shutil.rmtree(backup)
            result['actions'].append(dict(kind='MODEL_TREE_COPIED_HASHED_AND_MIGRATED', source=str(source),
                target=str(target), entries=len(before), files=sum(v['type']=='file' for v in before.values()),
                logical_file_bytes=sum(v.get('bytes', 0) for v in before.values()),
                private_manifest_sha256=digest(ops / (name + '-private-file-manifest.json')),
                full_SHA256_tree_match=True, old_path_samefile_verified=True, relative_symlinks_preserved=True))
            update('MIGRATED_' + name.upper())
        result['capacity_after'] = capacity()
        result['home_allocated_after'] = du(HOME)
        result['home_allocated_reduction'] = result['home_allocated_before'] - result['home_allocated_after']
        result['original_path_bindings'] = {str(p): dict(symlink=p.is_symlink(), target=os.readlink(p),
            realpath=str(p.resolve()), target_on_data_filesystem=p.stat().st_dev == DATA.stat().st_dev)
            for p in list(CACHES.values()) + list(MODELS.values())}
        assert all(v['target_on_data_filesystem'] for v in result['original_path_bindings'].values())
        assert not NANO.exists() and (HOME / 'cosmos3_nano/download').is_dir()
        assert {str(p): digest(p) for p in preserved} == fingerprints
        result['installed_runtime_fingerprints_unchanged'] = True
        result.update(status='COMPLETED_STORAGE_MIGRATION_VERIFIED', ended_unix=time.time())
        update('ALL_AUTHORIZED_ACTIONS_VERIFIED')
    except BaseException as e:
        result.update(status='FAILED_RETAIN_ORIGINALS_AND_STOP', ended_unix=time.time(),
                      error_type=type(e).__name__, error=str(e))
        update('STOPPED_' + result.get('phase', 'UNKNOWN'))
        raise


if __name__ == '__main__':
    main()
