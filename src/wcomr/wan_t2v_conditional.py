"""Scoped conditional-only adaptation of a hash-pinned native Wan T2V body.

The original source remains untouched. Guide !=1 retains the original negative
forward and CFG expression, including its arithmetic precision and order.
"""
import ast
from contextlib import contextmanager
import hashlib
import inspect
from pathlib import Path

WAN_TI2V_SOURCE_SHA256 = '228f2fabf23014ed41ec6b8cd713d5be7371bb558501c71a62a0258b491a877b'


def build_conditional_t2v(original, source_path):
    path = Path(source_path).resolve()
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != WAN_TI2V_SOURCE_SHA256:
        raise ValueError('Native Wan TI2V source differs from pinned commit42bf4cf')
    if Path(original.__code__.co_filename).resolve() != path:
        raise ValueError('Imported original T2V body is not from the verified source')
    if getattr(original, '_wcomr_conditional_t2v', False):
        raise ValueError('Refuse nested or repeated conditional T2V adaptation')
    tree = ast.parse(source)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'WanTI2V')
    function = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == 't2v')
    if original.__code__.co_firstlineno != function.lineno:
        raise ValueError('Original T2V line identity differs')
    matches = []
    for node in ast.walk(function):
        if not isinstance(node, ast.For):
            continue
        for index in range(len(node.body) - 2):
            triple = node.body[index:index + 3]
            names = [n.targets[0].id if isinstance(n, ast.Assign) and len(n.targets) == 1
                     and isinstance(n.targets[0], ast.Name) else None for n in triple]
            if names == ['noise_pred_cond', 'noise_pred_uncond', 'noise_pred']:
                matches.append((node, index, triple))
    if len(matches) != 1:
        raise ValueError('Expected one exact native T2V CFG sequence')
    loop, index, triple = matches[0]
    expected_negative = ast.parse('noise_pred_uncond = self.model(latent_model_input, t=timestep, **arg_null)[0]').body[0]
    expected_blend = ast.parse('noise_pred = noise_pred_uncond + guide_scale * (noise_pred_cond - noise_pred_uncond)').body[0]
    if (ast.dump(triple[1], include_attributes=False) != ast.dump(expected_negative, include_attributes=False)
            or ast.dump(triple[2], include_attributes=False) != ast.dump(expected_blend, include_attributes=False)):
        raise ValueError('Native negative call or CFG arithmetic differs')
    replacement = ast.If(test=ast.Compare(left=ast.Name(id='guide_scale', ctx=ast.Load()),
                                         ops=[ast.Eq()], comparators=[ast.Constant(value=1.0)]),
                         body=ast.parse('noise_pred = noise_pred_cond').body,
                         orelse=triple[1:])
    ast.copy_location(replacement, triple[1])
    loop.body[index:index + 3] = [triple[0], replacement]
    ast.fix_missing_locations(function)
    namespace = dict(original.__globals__)
    # Standalone function compilation leaves module globals/source unmodified.
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path) + '#wcomr-guide1-conditional', 'exec'), namespace)
    adapted = namespace['t2v']
    if inspect.signature(adapted) != inspect.signature(original):
        raise ValueError('Adaptation changed the native T2V signature')
    adapted.__qualname__ = original.__qualname__
    adapted._wcomr_conditional_t2v = True
    return adapted


@contextmanager
def conditional_t2v_scope(klass, source_path):
    original = klass.__dict__['t2v']
    adapted = build_conditional_t2v(original, source_path)
    klass.t2v = adapted
    try:
        yield {'status': 'SCOPED_NATIVE_T2V_GUIDE1_CONDITIONAL_ADAPTATION_NOT_GPU_PARITY',
               'source_sha256': WAN_TI2V_SOURCE_SHA256,
               'source_path': str(Path(source_path).resolve()),
               'scope': 'T2V only; original guide !=1 CFG arithmetic retained. No I2V adaptation.'}
    finally:
        if klass.__dict__['t2v'] is not adapted:
            raise RuntimeError('T2V method changed during scope; do not overwrite another adaptation')
        klass.t2v = original
