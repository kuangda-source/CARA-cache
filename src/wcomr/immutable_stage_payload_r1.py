"""Git-bound source overlays onto an unchanged, registered base stage.

Only declared configuration references/input files and local Python imports
are expanded. Historical receipt metadata and remote artifact paths are not
silently treated as current workspace files. This module starts no process.
"""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile


def relative(name):
    value = PurePosixPath(name)
    if (not isinstance(name, str) or not name or value.is_absolute() or '..' in value.parts
            or str(value) != name or name in ('.', 'registration.json')):
        raise ValueError('Normalized stage-relative regular payload path required')
    return name


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def registered_base_reference(registration_stage, original_absolute_stage):
    """Keep project-relative identity without resolving a remote alias locally."""
    original, label = PurePosixPath(original_absolute_stage), PurePosixPath(registration_stage)
    if (not original.is_absolute() or '..' in original.parts or '..' in label.parts
            or len(original.parts) < 3 or original.parts[-2] != '.sync'
            or label.parts[-2:] != original.parts[-2:]
            or (not label.is_absolute() and len(label.parts) != 2)):
        raise ValueError('Original registered stage must be one .sync child; remote aliases are not local paths')
    return dict(project_relative=str(PurePosixPath(*original.parts[-2:])),
                original_absolute=str(original))


def source_bytes(root, name):
    name = relative(name); root = Path(root).resolve(); path = root / name
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError('Missing or escaped source file: ' + name)
    return path.read_bytes()


def local_python_closure(root, entrypoints):
    """Follow static local wcomr imports, including nested function imports."""
    pending = [relative(n) for n in entrypoints]
    pending.append('src/wcomr/__init__.py')
    found = {}
    while pending:
        name = pending.pop()
        if name in found: continue
        if not name.endswith('.py'): raise ValueError('Python entrypoint required')
        raw = source_bytes(root, name); found[name] = digest(raw)
        module = name[4:-3].replace('/', '.') if name.startswith('src/') else None
        package = module.rsplit('.', 1)[0] if module else None
        for node in ast.walk(ast.parse(raw.decode(), filename=name)):
            modules = []
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    if not package: raise ValueError('Relative import in an unbound script package')
                    parts = package.split('.')
                    if node.level > len(parts): raise ValueError('Relative import escapes local package')
                    base = '.'.join(parts[:len(parts) - node.level + 1])
                    modules = [base + '.' + node.module] if node.module else [base + '.' + a.name for a in node.names]
                elif node.module == 'wcomr':
                    modules = ['wcomr.' + a.name for a in node.names]
                elif node.module and node.module.startswith('wcomr.'):
                    modules = [node.module]
            elif isinstance(node, ast.Import):
                modules = [a.name for a in node.names if a.name.startswith('wcomr.')]
            for imported in modules:
                if not imported.startswith('wcomr.'): continue
                target = 'src/' + imported.replace('.', '/') + '.py'
                if not (Path(root) / target).is_file():
                    raise ValueError('Declared local import is not packaged: ' + imported)
                pending.append(target)
    return found


def configuration_closure(root, config_roots):
    """Expand only the production config's explicit stage-local bindings."""
    pending = [relative(n) for n in config_roots]
    found = {}
    while pending:
        name = pending.pop()
        if name in found: continue
        raw = source_bytes(root, name); found[name] = digest(raw)
        # Receipts may describe historical files or absolute raw tensor paths;
        # their contents are evidence, not another current packaging manifest.
        if not (name.startswith('configs/') and name.endswith('.json')): continue
        config = json.loads(raw)
        for key in ('references', 'input_files'):
            for role, binding in config.get(key, {}).items():
                ref = relative(binding['ref']); data = source_bytes(root, ref)
                if digest(data) != binding['sha256']:
                    raise ValueError('Frozen config reference SHA differs: ' + name + ':' + role)
                pending.append(ref)
    return found


def plan(root, *, config_roots, python_entrypoints, extra_files, base_registration_sha256,
         base_source_revision, numeric_sources):
    # CPU test files are executed too. Copying their own bytes without their
    # imports can pass in the workspace and fail in an isolated source stage.
    extra_files = list(extra_files)
    python_extra_roots = [relative(n) for n in extra_files if n.endswith('.py')]
    found = local_python_closure(root, list(python_entrypoints) + python_extra_roots)
    found.update(configuration_closure(root, config_roots))
    for name in extra_files:
        name = relative(name); found[name] = digest(source_bytes(root, name))
    for name, expected in numeric_sources.items():
        name = relative(name); actual = digest(source_bytes(root, name))
        if actual != expected: raise ValueError('Accepted numerical source changed: ' + name)
        found[name] = actual
    if (len(base_registration_sha256) != 64 or not base_source_revision or not found
            or any(c not in '0123456789abcdef' for c in base_registration_sha256)):
        raise ValueError('Explicit unchanged base identity required')
    return dict(status='IMMUTABLE_STAGE_OVERLAY_PLAN_NOT_DEPLOYED', overlay_sha256=dict(sorted(found.items())),
        base_registration_sha256=base_registration_sha256, base_source_revision=base_source_revision,
        config_roots=list(config_roots), python_entrypoints=list(python_entrypoints),
        python_extra_dependency_roots=python_extra_roots,
        numerical_sources_verified=len(numeric_sources),
        GPU_submissions=0, shared_runtime_written=False, final_input_or_method_selection=False)


def git_archive(root, value, revision):
    """Bind every overlay byte to one committed Git tree before transport."""
    root = Path(root)
    files = value['overlay_sha256']
    queries = ''.join(revision + ':' + name + '\n' for name in files)
    result = subprocess.run(['git', 'cat-file', '--batch'], input=queries.encode(),
        cwd=root, capture_output=True, check=True)
    original = io.BytesIO(result.stdout); stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as archive:
        for name, expected in files.items():
            header = original.readline().decode().rstrip('\n').split()
            if len(header) != 3 or header[1] != 'blob': raise ValueError('Overlay file absent from frozen Git tree: ' + name)
            size = int(header[2]); raw = original.read(size)
            if original.read(1) != b'\n' or len(raw) != size: raise ValueError('Truncated Git blob stream')
            if digest(raw) != expected or raw != source_bytes(root, name):
                raise ValueError('Uncommitted or changed overlay byte: ' + name)
            info = tarfile.TarInfo(name); info.size = len(raw); info.mode = 0o644
            archive.addfile(info, io.BytesIO(raw))
    if original.read(1): raise ValueError('Unexpected extra Git object output')
    return stream.getvalue()


def overlay_bytes(archive_raw, value):
    expected, found = value['overlay_sha256'], {}
    with tarfile.open(fileobj=io.BytesIO(archive_raw), mode='r:gz') as archive:
        for member in archive:
            name = relative(member.name)
            if not member.isfile() or name not in expected or name in found:
                raise ValueError('Unexpected, duplicate or nonregular overlay member')
            raw = archive.extractfile(member).read()
            if digest(raw) != expected[name]: raise ValueError('Transported overlay SHA differs: ' + name)
            found[name] = raw
    if set(found) != set(expected): raise ValueError('Transport omitted declared overlay files')
    return found


def install(base, stage, archive_raw, value, *, source_revision,
            cpu_scope='FROZEN_N07_PRODUCTION_CPU_PREPARATION_NO_GPU'):
    """Copy registered base bytes read-only into one fresh independent stage."""
    base, original_stage = Path(base).resolve(), Path(stage)
    stage = original_stage.resolve()
    if cpu_scope not in ('FROZEN_N07_PRODUCTION_CPU_PREPARATION_NO_GPU',
                         'FROZEN_N08_PRODUCTION_CPU_PREPARATION_NO_GPU',
                         'FROZEN_N09_PRODUCTION_CPU_PREPARATION_NO_GPU',
                         'FULL24_REAL_PRODUCTION_WITH_UNCHANGED_COMPLETE88'):
        raise ValueError('Explicit supported no-GPU CPU stage scope required')
    if (original_stage.is_symlink() or stage.exists() or stage.parent != base.parent
            or stage.is_relative_to(base) or base.is_relative_to(stage)):
        raise ValueError('Fresh independent sibling stage required; never overwrite an old stage')
    registration_raw = (base / 'registration.json').read_bytes()
    registration = json.loads(registration_raw)
    if (digest(registration_raw) != value['base_registration_sha256']
            or registration['source_revision'] != value['base_source_revision'] or not source_revision):
        raise ValueError('Original base registration or revision differs')
    for name, expected in registration['payload_sha256'].items():
        if digest(source_bytes(base, name)) != expected: raise ValueError('Original registered base file changed: ' + name)
    overlay = overlay_bytes(archive_raw, value)
    stage.mkdir(parents=True, exist_ok=False)
    # A failure preserves the fresh partial stage for diagnosis. It never
    # overwrites the base, an earlier stage or an original server task.
    for name in registration['payload_sha256']:
        path = stage / name; path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base / name, path)
    for name, raw in overlay.items():
        path = stage / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    combined = {**registration['payload_sha256'], **value['overlay_sha256']}
    if any(digest(source_bytes(stage, name)) != expected for name, expected in combined.items()):
        raise ValueError('Complete installed payload differs')
    if (base / 'registration.json').read_bytes() != registration_raw:
        raise ValueError('Original base registration changed during source copy')
    new = copy.deepcopy(registration)
    new.update(source_revision=source_revision, stage=str(stage), base_stage=str(base),
        read_only_base_registration_sha256=value['base_registration_sha256'],
        payload_sha256=combined, CPU_scope=cpu_scope,
        overlay_plan=value, GPU_submissions_by_installer=0, shared_runtime_written=False)
    with (stage / 'registration.json').open('x') as handle:
        json.dump(new, handle, indent=2, allow_nan=False); handle.write('\n')
    return new
