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
    def exercise(**kwargs):
        net = kwargs['inference'].pipe.model.net
        original_forward = net.forward
        try:
            return namespace['exercise'](runtime=Path(runtime), tensor_loader=None,
                                         artifact_root=artifact_root, **kwargs)
        finally:
            # Real apply_worldcache binds its own module function. The tiny
            # fixture starts with a separate source-extracted function, so its
            # caller's binding must be restored as well as the value state.
            net.forward = original_forward
    return load('check_full_sampling').run(runtime, exercise=exercise)
