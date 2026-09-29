import hashlib
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('verify_public_assets', Path(__file__).resolve().parents[1]/'scripts/verify_public_assets.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def test_same_size_corruption_is_detected_for_git_and_lfs(tmp_path):
    data = b'original bytes'
    path = tmp_path/'config.json'; path.write_bytes(data)
    for lfs in (True, False):
        entry = {'path': path.name, 'size': len(data),
                 'git_blob_oid': hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest(),
                 'lfs': {'oid': hashlib.sha256(data).hexdigest()} if lfs else None}
        assert module.verify(tmp_path, entry)['status'] == 'PASS'
        path.write_bytes(b'x'*len(data))
        assert module.verify(tmp_path, entry)['status'] == 'HASH_MISMATCH'
        path.write_bytes(data)


def test_paths_cannot_escape_snapshot(tmp_path):
    for path in ('../token', '/etc/passwd'):
        with pytest.raises(ValueError, match='Unsafe'):
            module.verify(tmp_path, {'path': path})
