"""Four-action extension of the unchanged, source-bound paired controller.

Adds per-slot CC/DC/CD/DD continuation only. No policy, model installation,
GPU admission or arbitrary-failure rollback is supplied. Existing CC/DD code
is left unchanged, including a running source-bound experiment.
"""
import ast
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent
from types import MappingProxyType

from . import cfg_paired_probe_forward as base
from .cfg_paired_probe_production import ProductionPairedExecutor


BASE_SOURCE_SHA = 'e240851429f72336038ecfcdd1fdf60614e17b2fbe2a1bd8af42d71562e9db2b'
MODES = ('CC', 'DC', 'CD', 'DD')


def compile_mixed_pair():
    """Extend two exact AST sites; require an exact inverse to the base method."""
    if hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest() != BASE_SOURCE_SHA:
        raise ValueError('Pinned paired controller source differs')
    original = ast.parse(dedent(inspect.getsource(base.PairedProbeExecutor.pair))).body[0]
    node = copy.deepcopy(original)
    predicates = [n for n in ast.walk(node) if isinstance(n, ast.Compare)
                  and ast.dump(n, include_attributes=False) == ast.dump(ast.parse("action not in ('CC', 'DD')", mode='eval').body, include_attributes=False)]
    finish = [n for n in ast.walk(node) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
              and n.func.value.id == 'self' and n.func.attr == '_finish']
    messages = [n for n in ast.walk(node) if isinstance(n, ast.Constant) and n.value == 'Only joint CC/DD are allowed']
    if len(predicates) != 1 or len(finish) != 1 or len(messages) != 1:
        raise ValueError('Expected exact paired action-validation/continuation sites')
    if len(finish[0].args) != 2 or ast.dump(finish[0].args[1], include_attributes=False) != ast.dump(ast.parse("action == 'CC'", mode='eval').body, include_attributes=False):
        raise ValueError('Original paired continuation differs')
    predicates[0].comparators[0] = ast.parse(repr(MODES), mode='eval').body
    finish[0].args[1] = ast.parse("action[slot] == 'C'", mode='eval').body
    messages[0].value = 'Explicit CC/DC/CD/DD action required'
    inverse = copy.deepcopy(node)
    for n in ast.walk(inverse):
        if isinstance(n, ast.Compare) and ast.dump(n, include_attributes=False) == ast.dump(ast.parse('action not in '+repr(MODES), mode='eval').body, include_attributes=False):
            n.comparators[0] = ast.parse("('CC', 'DD')", mode='eval').body
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == '_finish':
            n.args[1] = ast.parse("action == 'CC'", mode='eval').body
        if isinstance(n, ast.Constant) and n.value == 'Explicit CC/DC/CD/DD action required':
            n.value = 'Only joint CC/DD are allowed'
    if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('Mixed controller changed outside action validation/slot continuation')
    function = base._compile(node, base.PairedProbeExecutor.pair.__globals__, str(Path(__file__))+'#mixed-controller')
    function.__module__ = __name__
    proof = MappingProxyType({'base_source_sha256': BASE_SOURCE_SHA,
        'base_method_AST_sha256': hashlib.sha256(ast.dump(original, include_attributes=False).encode()).hexdigest(),
        'mixed_method_AST_sha256': hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
        'inverse_AST_equal': True, 'allowed_actions': MODES,
        'protected_initialization_tail_and_poison_logic_unchanged': True,
        'actual_model_or_full_sampler_parity_verified': False})
    return function, proof


_pair, MIXED_COMPILER_PROOF = compile_mixed_pair()


class MixedProductionPairedExecutor(ProductionPairedExecutor):
    """Both prefixes precede a single decision; each slot gets its own action."""
    pair = _pair


def mixed_forced_reference(runtime, namespace, mode):
    """Original execution order with the same explicit per-slot action tuple."""
    if mode not in MODES:
        raise ValueError('Explicit original-order CC/DC/CD/DD mode required')
    original = base._function(runtime, base.WC_PATH, base.WC_SHA, 'worldcache_mini_train_dit_forward')
    node = copy.deepcopy(original)
    decision = base._find_safe(node, lambda n: isinstance(n, ast.If) and ast.unparse(n.test) == base.PREDICATE)
    saved = copy.deepcopy(decision.test)
    decision.test = ast.parse(repr(mode)+"[self.cnt % 2] == 'C'", mode='eval').body
    inverse = copy.deepcopy(node)
    restored = base._find_safe(inverse, lambda n: isinstance(n, ast.If) and ast.dump(n.test, include_attributes=False) == ast.dump(decision.test, include_attributes=False))
    restored.test = saved
    if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('Mixed original-order reference changed outside predicate')
    return base._compile(node, namespace, base.WC_PATH+'#original-order-'+mode)
