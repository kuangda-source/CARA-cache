import hashlib
from types import SimpleNamespace
import pytest
from wcomr.native_cpu_import import native_cpu_import_guard


def fixture(tmp_path):
    source = tmp_path / 'wan/modules/t5.py'
    source.parent.mkdir(parents=True)
    text = 'class T5EncoderModel:\n    def __init__(self, device=torch.cuda.current_device()):\n        self.device=device\n'
    source.write_text(text)
    def forbidden():
        raise AssertionError('Actual CUDA query must never run')
    torch = SimpleNamespace(cuda=SimpleNamespace(current_device=forbidden, is_initialized=lambda: False), device=lambda x: x)
    return source, text, torch, hashlib.sha256(text.encode()).hexdigest(), forbidden


def test_attested_default_and_query_restoration(tmp_path):
    source, text, torch, sha, original = fixture(tmp_path)
    with native_cpu_import_guard(torch, tmp_path, sha) as receipt:
        namespace = {'torch': torch}
        exec(compile(text, str(source), 'exec'), namespace)
        assert namespace['T5EncoderModel']().device == 'cpu'
    assert receipt['current_device_calls'] == 1 and receipt['original_query_restored']
    assert torch.cuda.current_device is original and source.read_text() == text


def test_unattested_query_rejected_and_restored(tmp_path):
    source, text, torch, sha, original = fixture(tmp_path)
    with pytest.raises(ValueError, match='outside attested'):
        with native_cpu_import_guard(torch, tmp_path, sha):
            torch.cuda.current_device()
    assert torch.cuda.current_device is original


def test_hash_rejection_before_substitution(tmp_path):
    source, text, torch, sha, original = fixture(tmp_path)
    with pytest.raises(ValueError, match='source differs'):
        with native_cpu_import_guard(torch, tmp_path, '0' * 64):
            pass
    assert torch.cuda.current_device is original


def test_import_failure_restores_query(tmp_path):
    source, text, torch, sha, original = fixture(tmp_path)
    with pytest.raises(ImportError):
        with native_cpu_import_guard(torch, tmp_path, sha):
            raise ImportError('Expected CPU import failure')
    assert torch.cuda.current_device is original
