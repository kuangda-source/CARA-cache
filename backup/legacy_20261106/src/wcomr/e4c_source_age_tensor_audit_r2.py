"""Read-only CPU reader: allow FP64 reduction ordering, preserve exact tensors."""
import ast
import inspect
from textwrap import dedent

from . import e4c_source_age_tensor_audit_r1 as original


def scalar_equal(left, right):
    return original.math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-15)


def compile_reader():
    source = dedent(inspect.getsource(original.audit))
    before = "or branch_mse != saved['diagnostics']['original_branch_MSE']"
    after = ("or len(saved['diagnostics']['original_branch_MSE']) != 2"
        " or any(not _scalar_equal(a, b) for a, b in zip("
        "branch_mse, saved['diagnostics']['original_branch_MSE']))")
    if source.count(before) != 1:
        raise ValueError('Pinned exact branch-reduction comparison changed')
    changed = source.replace(before, after)
    inverse = changed.replace(after, before)
    if inverse != source or ast.dump(ast.parse(inverse)) != ast.dump(ast.parse(source)):
        raise ValueError('Only CPU/GPU scalar reduction comparison may differ')
    namespace = {**vars(original), '_scalar_equal': scalar_equal}
    exec(compile(changed, __file__+'#CPU-FP64-reduction-reader', 'exec'), namespace)
    return namespace['audit']


audit = compile_reader()
