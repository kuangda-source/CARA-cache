"""CPU-probe-only guard for the pinned T5 import-time CUDA device default."""
import ast
from contextlib import contextmanager
import hashlib
import inspect
from pathlib import Path


@contextmanager
def native_cpu_import_guard(torch, source, expected_t5_sha256):
    """Substitute CPU only at the attested T5EncoderModel default expression.

    This changes that constructor default in this probe process. It does not
    establish an unmodified import, model forward or GPU runtime result.
    """
    path = (Path(source) / 'wan/modules/t5.py').resolve()
    original_bytes = path.read_bytes()
    if hashlib.sha256(original_bytes).hexdigest() != expected_t5_sha256:
        raise ValueError('Pinned T5 source differs')
    tree = ast.parse(original_bytes)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'T5EncoderModel')
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
    calls = [n for default in init.args.defaults for n in ast.walk(default)
             if isinstance(n, ast.Call) and ast.unparse(n.func) == 'torch.cuda.current_device']
    if len(calls) != 1 or torch.cuda.is_initialized():
        raise ValueError('Unexpected T5 default or CUDA state')
    original = torch.cuda.current_device
    if getattr(original, '_wcomr_cpu_guard', False):
        raise ValueError('Nested CPU import guard')
    receipt = {'scope': 'CPU probe only; T5 constructor default substituted with CPU in this process',
               't5_sha256': expected_t5_sha256, 'allowed_line': calls[0].lineno,
               'current_device_calls': 0, 'original_query_restored': False}

    def guarded_current_device():
        caller = inspect.currentframe().f_back
        if (Path(caller.f_code.co_filename).resolve() != path
                or caller.f_code.co_name != 'T5EncoderModel'
                or caller.f_lineno != calls[0].lineno
                or receipt['current_device_calls']):
            raise ValueError('CUDA device query outside attested import default')
        receipt['current_device_calls'] += 1
        return torch.device('cpu')

    guarded_current_device._wcomr_cpu_guard = True
    torch.cuda.current_device = guarded_current_device
    try:
        yield receipt
        if receipt['current_device_calls'] != 1 or torch.cuda.is_initialized():
            raise ValueError('Native import guard coverage or CUDA state differs')
    finally:
        torch.cuda.current_device = original
        receipt['original_query_restored'] = True
        if path.read_bytes() != original_bytes:
            raise ValueError('Pinned T5 source changed during CPU import')
