#!/usr/bin/env python3
"""Read-only local integrity, import-path and navigation checks; no experiments."""
import ast
import hashlib
import json
from pathlib import Path
import re
import stat
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'backup/ARCHIVE_MANIFEST.json'
REPO_PATH = re.compile(
    r'(?<![\w/])(?:plans|reports|configs|manifests|scripts|tests|inputs|cards|src)/'
    r'[A-Za-z0-9_./+@-]+'
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    manifest = json.loads(MANIFEST.read_text())
    original = {entry['original_path']: entry for entry in manifest['entries']}
    errors = []
    for entry in manifest['entries']:
        path = ROOT / entry['path']
        if not path.is_file():
            errors.append(f"Missing original: {entry['path']}")
            continue
        if path.stat().st_size != entry['bytes'] or sha256(path) != entry['sha256']:
            errors.append(f"Original bytes changed: {entry['path']}")
        executable = bool(path.stat().st_mode & stat.S_IXUSR)
        if executable != (entry['git_mode'] == '100755'):
            errors.append(f"Executable mode changed: {entry['path']}")

    active = [path for path in ROOT.rglob('*') if path.is_file()
              and path.relative_to(ROOT).parts[0] not in ('backup', '.git')
              and '__pycache__' not in path.parts]
    python_files = [path for path in active if path.suffix == '.py']
    local_modules = {Path(path).stem: path for path in original
                     if path.startswith(('scripts/', 'tests/')) and path.endswith('.py')}
    for path in python_files:
        name = path.relative_to(ROOT).as_posix()
        text = path.read_text()
        try:
            tree = ast.parse(text, filename=name)
        except SyntaxError as exc:
            errors.append(f'Python syntax: {name}:{exc.lineno}: {exc.msg}')
            continue
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                modules = [node.module]
                if node.module == 'wcomr':
                    modules += ['wcomr.' + alias.name for alias in node.names]
            for module in modules:
                if module.startswith('wcomr.'):
                    base = 'src/' + module.replace('.', '/')
                    candidates = [base + '.py', base + '/__init__.py']
                    # Attributes exported by wcomr need not themselves be modules.
                    known = any(candidate in original for candidate in candidates)
                    if known and not any((ROOT / candidate).is_file() for candidate in candidates):
                        errors.append(f'Import moved: {name} -> {module}')
                elif module.split('.')[0] in local_modules:
                    target = local_modules[module.split('.')[0]]
                    if not (ROOT / target).is_file():
                        errors.append(f'Local helper moved: {name} -> {target}')
        for reference in REPO_PATH.findall(text):
            reference = reference.rstrip('.,;:')
            if reference in original and not (ROOT / reference).is_file():
                errors.append(f'Explicit original path moved: {name} -> {reference}')

    markdown_files = [path for path in active if path.suffix == '.md']
    for path in markdown_files:
        name = path.relative_to(ROOT).as_posix()
        for destination in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            destination = unquote(destination.split('#')[0].split(' "')[0].strip('<>'))
            if not destination or '://' in destination or destination.startswith('mailto:'):
                continue
            target = (ROOT / destination[5:] if destination.startswith('repo:')
                      else path.parent / destination)
            if not target.exists():
                errors.append(f'Broken local link: {name} -> {destination}')

    result = dict(
        passed=not errors,
        source_commit=manifest['source_commit'],
        original_files_checked=len(original),
        archived_files=manifest['archived_files'],
        retained_original_files=manifest['retained_original_files'],
        active_python_files_checked=len(python_files),
        active_markdown_files_checked=len(markdown_files),
        original_runtime_bytes_unchanged=not any('Original bytes changed' in e for e in errors),
        network_calls=0, model_loads=0, experiment_dispatches=0,
        errors=sorted(set(errors)),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
