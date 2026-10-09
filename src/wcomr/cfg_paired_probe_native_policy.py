"""Independent four-action controller with the complete native-policy horizon.

Only the action alphabet, per-slot continuation, tail eligibility and modulo
counter check differ from the pinned base method. Old controllers stay intact.
The inverse AST proof is a source check, not a model or policy-benefit result.
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


def compile_native_policy_pair():
    if hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest() != BASE_SOURCE_SHA:
        raise ValueError('Pinned paired controller source differs')
    original = ast.parse(dedent(inspect.getsource(base.PairedProbeExecutor.pair))).body[0]
    replacements = [
        ("action not in ('CC', 'DD')", 'action not in '+repr(MODES)),
        ("self._finish(gen, action == 'CC')", "self._finish(gen, action[slot] == 'C')"),
        (repr('Only joint CC/DD are allowed'), repr('Explicit CC/DC/CD/DD action required')),
        ('count + 1 < horizon - 1', 'count + 1 < horizon'),
        ('self.net.cnt != count + slot + 1', 'self.net.cnt != (count + slot + 1) % horizon'),
    ]
    def dump(node):
        return ast.dump(node, include_attributes=False)
    def transform(root, pairs):
        patterns = [(dump(ast.parse(a, mode='eval').body), ast.parse(b, mode='eval').body)
                    for a, b in pairs]
        counts = [0] * len(patterns)
        class Replace(ast.NodeTransformer):
            def generic_visit(self, node):
                for i, (pattern, value) in enumerate(patterns):
                    if dump(node) == pattern:
                        counts[i] += 1
                        return copy.deepcopy(value)
                return super().generic_visit(node)
        result = Replace().visit(copy.deepcopy(root))
        if counts != [1]*len(patterns):
            raise ValueError('Expected exactly five source-bound transformation sites: '+repr(counts))
        return result
    node = transform(original, replacements)
    inverse = transform(node, [(b, a) for a, b in replacements])
    if dump(inverse) != dump(original):
        raise ValueError('Native-policy controller changed outside five registered sites')
    function = base._compile(node, base.PairedProbeExecutor.pair.__globals__,
                             str(Path(__file__))+'#native-policy-controller')
    function.__module__ = __name__
    proof = MappingProxyType({
        'base_source_sha256': BASE_SOURCE_SHA,
        'base_method_AST_sha256': hashlib.sha256(dump(original).encode()).hexdigest(),
        'native_policy_method_AST_sha256': hashlib.sha256(dump(node).encode()).hexdigest(),
        'inverse_AST_equal': True, 'registered_transformation_sites': 5,
        'allowed_actions': MODES, 'tail_pair_eligible_before_cycle_reset': True,
        'continuation_counter_checked_modulo_horizon': True,
        'initialization_warmup_no_history_new_cycle_and_poison_logic_unchanged': True,
        'actual_model_or_full_sampler_parity_verified': False})
    return function, proof


_pair, NATIVE_POLICY_COMPILER_PROOF = compile_native_policy_pair()


class NativePolicyPairedExecutor(ProductionPairedExecutor):
    """Both prefixes paid before any of four actions, including the tail pair."""
    pair = _pair
