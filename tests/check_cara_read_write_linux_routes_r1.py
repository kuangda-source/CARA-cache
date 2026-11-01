"""Use actual target WC/RF module globals with the accepted tiny test setup."""
import inspect
from pathlib import Path
from textwrap import dedent

from check_cara_read_write_suffix_cpu_r1 import body, load


def run(runtime, artifact_root):
    old = load('check_partial_mlp_guided_sampling_cpu_r1')
    source = dedent(inspect.getsource(old.exercise))
    start = source.index('    results=[]\n    try:')
    end = source.index('\n    finally:\n', start)+1
    source = source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    namespace = {**vars(old), '_body': body}
    exec(compile(source, __file__+'#actual-import-tiny-setup', 'exec'), namespace)
    return load('check_full_sampling').run(runtime, exercise=lambda **kwargs: namespace['exercise'](
        runtime=Path(runtime), tensor_loader=None, artifact_root=artifact_root, **kwargs))
