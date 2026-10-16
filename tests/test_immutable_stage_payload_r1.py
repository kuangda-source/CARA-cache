"""Real temporary Git blobs/archives/files; no remote process or GPU staging."""
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

from wcomr.immutable_stage_payload_r1 import (
    configuration_closure, digest, git_archive, install, local_python_closure, overlay_bytes, plan,
    registered_base_reference,
)


def write(root, name, raw):
    path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw); return digest(raw)


def fixture(parent):
    root = parent / 'workspace'; root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True, capture_output=True)
    write(root, 'src/wcomr/__init__.py', b'')
    write(root, 'src/wcomr/b.py', b'VALUE = 7\n')
    write(root, 'src/wcomr/a.py', b'def run():\n from .b import VALUE\n return VALUE\n')
    write(root, 'scripts/entry.py', b'from wcomr import a\n')
    manifest = write(root, 'manifests/control.json', json.dumps(dict(
        historical_reference=dict(ref='DO_NOT_REPACKAGE_PAST_FILE.pt', sha256='0' * 64))).encode())
    source = write(root, 'inputs/one.json', b'{"prompt":"SYNTHETIC_NOT_SELECTED"}\n')
    physical = write(root, 'configs/physical.json', json.dumps(dict(
        references={'control': dict(ref='manifests/control.json', sha256=manifest)})).encode())
    write(root, 'configs/final.json', json.dumps(dict(
        references={'physical': dict(ref='configs/physical.json', sha256=physical)},
        input_files={'synthetic': dict(ref='inputs/one.json', sha256=source)})).encode())
    subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
    subprocess.run(['git', '-c', 'user.name=Synthetic CPU Control', '-c', 'user.email=synthetic@invalid',
                    'commit', '-qm', 'Synthetic source fixture only'], cwd=root, check=True, capture_output=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    base = parent / 'stages/base'; base.mkdir(parents=True)
    old = write(base, 'src/wcomr/a.py', b'# OLD_SYNTHETIC_BASE\n')
    keep = write(base, 'manifests/keep.json', b'{"preserve":true}\n')
    registration = dict(source_revision='SYNTHETIC_BASE_REVISION',
                        payload_sha256={'src/wcomr/a.py': old, 'manifests/keep.json': keep},
                        runtime_source_sha256={'SYNTHETIC_RUNTIME_UNTOUCHED.py': '1' * 64})
    registration_raw = (json.dumps(registration, indent=2) + '\n').encode()
    write(base, 'registration.json', registration_raw)
    value = plan(root, config_roots=['configs/final.json'], python_entrypoints=['scripts/entry.py'],
        extra_files=[], base_registration_sha256=digest(registration_raw),
        base_source_revision=registration['source_revision'],
        numeric_sources={'src/wcomr/b.py': digest((root / 'src/wcomr/b.py').read_bytes())})
    return root, base, value, revision


class ImmutablePayloadControls(unittest.TestCase):
    def test_extra_executed_cpu_fixture_imports_exist_in_isolated_git_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root, base, original, _ = fixture(Path(directory))
            write(root, 'src/wcomr/only_test_dependency.py', b'VALUE = 17\n')
            write(root, 'tests/cpu_fixture.py',
                  b'from wcomr.only_test_dependency import VALUE\nassert VALUE == 17\n')
            subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', '-c', 'user.name=Synthetic CPU Control',
                            '-c', 'user.email=synthetic@invalid', 'commit', '-qm',
                            'Synthetic executed test dependency'], cwd=root, check=True, capture_output=True)
            revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
            value = plan(root, config_roots=['configs/final.json'],
                python_entrypoints=['scripts/entry.py'], extra_files=['tests/cpu_fixture.py'],
                base_registration_sha256=original['base_registration_sha256'],
                base_source_revision=original['base_source_revision'],
                numeric_sources={'src/wcomr/b.py': digest((root/'src/wcomr/b.py').read_bytes())})
            self.assertIn('src/wcomr/only_test_dependency.py', value['overlay_sha256'])
            stage = base.parent/'with-executed-test-imports'
            install(base, stage, git_archive(root, value, revision), value, source_revision=revision)
            command = ('import sys; from pathlib import Path; '
                       'sys.path.insert(0, ' + repr(str(stage/'src')) + '); '
                       'exec(compile(Path(' + repr(str(stage/'tests/cpu_fixture.py')) +
                       ').read_bytes(), "ISOLATED_TEST_ONLY", "exec"))')
            subprocess.run([sys.executable, '-I', '-c', command], cwd=stage,
                           check=True, capture_output=True)

    def test_remote_base_alias_uses_registered_relative_identity(self):
        canonical = '/media/SYNTHETIC_MOUNT/gkd/worldcache_omr/.sync/base-r2'
        logical = '/home/SYNTHETIC_USER/data/gkd/worldcache_omr/.sync/base-r2'
        for label in ('.sync/base-r2', logical):
            value = registered_base_reference(label, canonical)
            self.assertEqual(value['project_relative'], '.sync/base-r2')
            self.assertEqual(value['original_absolute'], canonical)
        with self.assertRaises(ValueError): registered_base_reference('.sync/another', canonical)
        with self.assertRaises(ValueError): registered_base_reference('../.sync/base-r2', canonical)

    def test_nested_config_inputs_static_imports_and_history_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, value, _ = fixture(Path(directory))
            self.assertEqual(len(local_python_closure(root, ['scripts/entry.py'])), 4)
            self.assertEqual(len(configuration_closure(root, ['configs/final.json'])), 4)
            self.assertEqual(len(value['overlay_sha256']), 8)
            self.assertNotIn('DO_NOT_REPACKAGE_PAST_FILE.pt', value['overlay_sha256'])

    def test_committed_archive_fresh_stage_and_unchanged_original_base(self):
        with tempfile.TemporaryDirectory() as directory:
            root, base, value, revision = fixture(Path(directory))
            before = {str(p.relative_to(base)): p.read_bytes() for p in base.rglob('*') if p.is_file()}
            raw = git_archive(root, value, revision); stage = base.parent / 'new-source'
            registered = install(base, stage, raw, value, source_revision=revision)
            self.assertEqual(len(registered['payload_sha256']), 9)
            self.assertEqual((stage / 'src/wcomr/a.py').read_bytes(), (root / 'src/wcomr/a.py').read_bytes())
            self.assertEqual((stage / 'manifests/keep.json').read_bytes(), before['manifests/keep.json'])
            self.assertEqual(before, {str(p.relative_to(base)): p.read_bytes() for p in base.rglob('*') if p.is_file()})
            self.assertEqual(registered['GPU_submissions_by_installer'], 0)
            with self.assertRaises(ValueError): install(base, stage, raw, value, source_revision=revision)
            with self.assertRaises(ValueError): install(base, base, raw, value, source_revision=revision)

    def test_missing_changed_numeric_or_config_reference_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, value, _ = fixture(Path(directory))
            (root / 'inputs/one.json').unlink()
            with self.assertRaises(ValueError): configuration_closure(root, ['configs/final.json'])
            write(root, 'inputs/one.json', b'changed')
            with self.assertRaises(ValueError): configuration_closure(root, ['configs/final.json'])
            with self.assertRaises(ValueError): plan(root, config_roots=[], python_entrypoints=['scripts/entry.py'],
                extra_files=[], base_registration_sha256=value['base_registration_sha256'],
                base_source_revision=value['base_source_revision'], numeric_sources={'src/wcomr/b.py': '0' * 64})

    def test_N08_cpu_scope_explicit_and_original_N07_default_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root, base, value, revision = fixture(Path(directory)); raw = git_archive(root, value, revision)
            before = {str(p.relative_to(base)): p.read_bytes() for p in base.rglob('*') if p.is_file()}
            first = install(base, base.parent / 'original-n07-default', raw, value, source_revision=revision)
            second = install(base, base.parent / 'explicit-n08', raw, value, source_revision=revision,
                cpu_scope='FROZEN_N08_PRODUCTION_CPU_PREPARATION_NO_GPU')
            third = install(base, base.parent / 'explicit-n09', raw, value, source_revision=revision,
                cpu_scope='FROZEN_N09_PRODUCTION_CPU_PREPARATION_NO_GPU')
            self.assertEqual(first['CPU_scope'], 'FROZEN_N07_PRODUCTION_CPU_PREPARATION_NO_GPU')
            self.assertEqual(second['CPU_scope'], 'FROZEN_N08_PRODUCTION_CPU_PREPARATION_NO_GPU')
            self.assertEqual(third['CPU_scope'], 'FROZEN_N09_PRODUCTION_CPU_PREPARATION_NO_GPU')
            self.assertEqual(first['payload_sha256'], second['payload_sha256'])
            self.assertEqual(first['payload_sha256'], third['payload_sha256'])
            with self.assertRaises(ValueError): install(base, base.parent / 'bad-scope', raw, value,
                source_revision=revision, cpu_scope='SYNTHETIC_GPU_OR_UNBOUND')
            self.assertFalse((base.parent / 'bad-scope').exists())
            self.assertEqual({str(p.relative_to(base)): p.read_bytes() for p in base.rglob('*') if p.is_file()}, before)

    def test_uncommitted_bytes_and_missing_git_blob_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, value, revision = fixture(Path(directory))
            write(root, 'src/wcomr/b.py', b'VALUE = 99\n')
            with self.assertRaises(ValueError): git_archive(root, value, revision)
            changed = copy.deepcopy(value); changed['overlay_sha256']['not-committed.py'] = digest(b'pass\n')
            write(root, 'not-committed.py', b'pass\n')
            # Restore the original tracked byte so the missing blob itself is reached.
            write(root, 'src/wcomr/b.py', b'VALUE = 7\n')
            with self.assertRaises(ValueError): git_archive(root, changed, revision)

    def test_duplicate_missing_extra_link_and_traversal_archive_members_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root, _, value, revision = fixture(Path(directory))
            good = overlay_bytes(git_archive(root, value, revision), value)
            for kind in ('duplicate', 'missing', 'extra', 'link', 'escape'):
                stream = io.BytesIO()
                with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                    values = list(good.items())
                    if kind == 'missing': values.pop()
                    if kind == 'duplicate': values.append(values[0])
                    if kind == 'extra': values.append(('UNDECLARED.py', b'pass\n'))
                    if kind == 'escape': values.append(('../ESCAPE.py', b'pass\n'))
                    for i, (name, data) in enumerate(values):
                        member = tarfile.TarInfo(name); member.size = len(data)
                        if kind == 'link' and i == 0:
                            member.type = tarfile.SYMTYPE; member.linkname = '/FOREIGN'; member.size = 0
                            archive.addfile(member)
                        else: archive.addfile(member, io.BytesIO(data))
                with self.assertRaises(ValueError): overlay_bytes(stream.getvalue(), value)

    def test_changed_base_and_non_sibling_or_broken_stage_link_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root, base, value, revision = fixture(Path(directory)); raw = git_archive(root, value, revision)
            with self.assertRaises(ValueError): install(base, Path(directory) / 'outside', raw, value, source_revision=revision)
            link = base.parent / 'new-link'; link.symlink_to(base.parent / 'missing-target')
            with self.assertRaises(ValueError): install(base, link, raw, value, source_revision=revision)
            write(base, 'src/wcomr/a.py', b'changed old base')
            with self.assertRaises(ValueError): install(base, base.parent / 'fresh', raw, value, source_revision=revision)
            self.assertFalse((base.parent / 'fresh').exists())


if __name__ == '__main__': unittest.main()
