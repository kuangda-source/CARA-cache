"""Source-pinned, generator-based two-prefix CPU prototype.

No runtime forward installation, risk fitting, CUDA admission or arbitrary-fault
rollback is provided. Outer net hooks are unsupported and rejected. Blocks still
use their normal Module.__call__. A failed executor must be discarded as a whole.
"""
import ast
import copy
from dataclasses import dataclass
import hashlib
from pathlib import Path
from types import MappingProxyType


WC_PATH = 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
WC_SHA = 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903'
RF_PATH = 'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
RF_SHA = '9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8'
PREDICATE = 'self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh'


@dataclass(frozen=True)
class PaidProbe:
    slot: int
    counter: int
    native_cache: bool
    delta_x: float
    delta_y: float
    dynamic_threshold: float


def _packet(slot, counter, native_cache, delta_x, delta_y, threshold):
    import math
    values = [float(delta_x), float(delta_y), float(threshold)]
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Nonfinite paid probe')
    return PaidProbe(int(slot), int(counter), bool(native_cache), *values)


def _function(runtime, relative, digest, name):
    path = Path(runtime) / relative
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('Pinned source changed: ' + relative)
    nodes = [n for n in ast.walk(ast.parse(raw))
             if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(nodes) != 1:
        raise ValueError('Ambiguous pinned function: ' + name)
    if nodes[0].decorator_list:
        raise ValueError('Decorated function is outside this prototype')
    return copy.deepcopy(nodes[0])


def _compile(node, namespace, label):
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    body = ast.fix_missing_locations(ast.Module(body=[future, node], type_ignores=[]))
    scope = dict(namespace)
    exec(compile(body, label, 'exec'), scope)
    return scope[node.name]


def _find_safe(root, predicate):
    found = []
    def visit(node, ancestors):
        if predicate(node):
            if any(isinstance(n, (ast.With, ast.AsyncWith, ast.Try)) for n in ancestors):
                raise ValueError('Context manager/try crosses pause boundary')
            found.append(node)
        for child in ast.iter_child_nodes(node):
            visit(child, ancestors + [node])
    visit(root, [])
    if len(found) != 1:
        raise ValueError('Expected one exact pause boundary')
    return found[0]


def compile_core(runtime, namespace):
    """Keep both source bodies; replace just one predicate and one net call."""
    original = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
    node = copy.deepcopy(original)
    decision = _find_safe(node, lambda n: isinstance(n, ast.If) and
                          ast.unparse(n.test) == PREDICATE)
    saved = copy.deepcopy(decision.test)
    packet = ast.Call(func=ast.Name(id='_paid_probe', ctx=ast.Load()), args=[
        ast.Name(id='current_idx', ctx=ast.Load()),
        ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='cnt', ctx=ast.Load()),
        saved, ast.Name(id='delta_x', ctx=ast.Load()), ast.Name(id='delta_y', ctx=ast.Load()),
        ast.Name(id='dynamic_thresh', ctx=ast.Load())], keywords=[])
    decision.test = ast.Yield(value=packet)
    # Check the exact inverse before compiling rather than trusting an edit count.
    inverse = copy.deepcopy(node)
    changed = [n for n in ast.walk(inverse) if isinstance(n, ast.If) and isinstance(n.test, ast.Yield)]
    if len(changed) != 1:
        raise ValueError('Unexpected WorldCache transformation')
    changed[0].test = copy.deepcopy(saved)
    if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('WorldCache body changed outside the predicate')
    net_forward = _compile(node, dict(namespace, _paid_probe=_packet), WC_PATH + '#paired-prefix')

    denoise_original = _function(runtime, RF_PATH, RF_SHA, 'denoise')
    denoise_node = copy.deepcopy(denoise_original)
    call = _find_safe(denoise_node, lambda n: isinstance(n, ast.Call) and
        isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and
        n.func.value.id == 'self' and n.func.attr == 'net')
    net_call = copy.deepcopy(call)
    class ReplaceNet(ast.NodeTransformer):
        def visit_Call(self, n):
            if n is call:
                return ast.YieldFrom(value=ast.Call(func=ast.Name(id='_paired_net', ctx=ast.Load()),
                    args=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='net', ctx=ast.Load())] + n.args,
                    keywords=n.keywords))
            return self.generic_visit(n)
    denoise_node = ReplaceNet().visit(denoise_node)
    denoise_inverse = copy.deepcopy(denoise_node)
    class RestoreNet(ast.NodeTransformer):
        def visit_YieldFrom(self, n):
            return copy.deepcopy(net_call)
    denoise_inverse = RestoreNet().visit(denoise_inverse)
    if ast.dump(denoise_inverse, include_attributes=False) != ast.dump(denoise_original, include_attributes=False):
        raise ValueError('RF body changed outside its net call')
    denoise = _compile(denoise_node, dict(namespace, _paired_net=net_forward), RF_PATH + '#paired-prefix')
    return net_forward, denoise, MappingProxyType({
        'WC_source_sha256': WC_SHA, 'RF_source_sha256': RF_SHA,
        'WC_inverse_AST_equal': True, 'RF_inverse_AST_equal': True,
        'WC_original_body_sha256': hashlib.sha256(ast.dump(original, include_attributes=False).encode()).hexdigest(),
        'RF_original_body_sha256': hashlib.sha256(ast.dump(denoise_original, include_attributes=False).encode()).hexdigest()})


def forced_reference(runtime, namespace, action):
    """Original-order same-action control, not the original threshold policy."""
    if action not in ('CC', 'DD'):
        raise ValueError('Reference action must be joint')
    node = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
    decision = _find_safe(node, lambda n: isinstance(n, ast.If) and ast.unparse(n.test) == PREDICATE)
    decision.test = ast.Constant(value=action == 'CC')
    return _compile(node, namespace, WC_PATH + '#original-order-' + action)


class PairedProbeExecutor:
    """One instance is tied to one model/net; poison on any failed pair."""
    def __init__(self, model, denoise, torch):
        self.model, self.net, self.denoise, self.torch = model, model.net, denoise, torch
        self.poisoned = False
        self.running = False
        self.last = None

    def _preflight(self):
        if self.model.net is not self.net or self.torch.is_grad_enabled():
            raise ValueError('Bound net identity and ambient no_grad are required')
        if any(m.training for m in self.net.modules()):
            raise ValueError('All modules must already be eval')
        if int(self.net.cnt) % 2:
            raise ValueError('Pair must begin at conditional even counter')
        for key in ('_forward_hooks', '_forward_pre_hooks', '_backward_hooks', '_backward_pre_hooks'):
            if getattr(self.net, key, {}):
                raise ValueError('Outer net hook is unsupported')
        module = self.torch.nn.modules.module
        for key in ('_global_forward_hooks', '_global_forward_pre_hooks', '_global_backward_hooks', '_global_backward_pre_hooks'):
            if getattr(module, key, {}):
                raise ValueError('Global net hook is unsupported')

    @staticmethod
    def _drain(gen):
        try:
            item = next(gen)
            while True:
                if not isinstance(item, PaidProbe):
                    raise ValueError('Unexpected protected-pair yield')
                item = gen.send(False)
        except StopIteration as done:
            return done.value

    @staticmethod
    def _finish(gen, skip):
        try:
            gen.send(skip)
        except StopIteration as done:
            return done.value
        raise ValueError('Forward yielded more than once')

    def pair(self, noise, xt, timestep, conditions, choose):
        if self.poisoned:
            raise ValueError('Poisoned executor cannot continue')
        if self.running:
            self.poisoned = True
            raise ValueError('Nested pair is unsupported')
        generators = []
        self.running = True
        try:
            self._preflight()
            if len(conditions) != 2:
                raise ValueError('Both conditions are required')
            count = int(self.net.cnt)
            horizon = int(self.net.worldcache_num_steps)
            warmup = int(horizon * self.net.worldcache_ret_ratio)
            ready = all(self.net.previous_input[s] is not None and
                        self.net.previous_internal_states[s] is not None and
                        self.net.residual_cache[s] is not None for s in (0, 1))
            eligible = count >= warmup and count + 1 < horizon - 1 and ready
            generators = [self.denoise(self.model, noise, xt, timestep, c) for c in conditions]
            if not eligible:
                outputs = []
                for slot, gen in enumerate(generators):
                    outputs.append(self._drain(gen))
                    expected = (count + slot + 1) % horizon
                    if self.net.cnt != expected:
                        raise ValueError('Protected-pair counter mismatch')
                self.last = {'action': 'DD', 'paid_probes': [], 'protected': True}
                return tuple(outputs)
            first = next(generators[0])
            if not isinstance(first, PaidProbe) or first.slot != 0 or first.counter != count or self.net.cnt != count:
                raise ValueError('Conditional pause/counter mismatch')
            self.net.cnt = count + 1
            second = next(generators[1])
            if not isinstance(second, PaidProbe) or second.slot != 1 or second.counter != count + 1 or self.net.cnt != count + 1:
                raise ValueError('Unconditional pause/counter mismatch')
            self.net.cnt = count
            rng_before = self.torch.get_rng_state().clone()
            action = choose((first, second))
            if self.net.cnt != count or not self.torch.equal(rng_before, self.torch.get_rng_state()):
                raise ValueError('Selector changed counter or CPU RNG')
            if action not in ('CC', 'DD'):
                raise ValueError('Only joint CC/DD are allowed')
            outputs = []
            for slot, gen in enumerate(generators):
                outputs.append(self._finish(gen, action == 'CC'))
                if self.net.cnt != count + slot + 1:
                    raise ValueError('Continuation counter mismatch')
            self.last = {'action': action, 'paid_probes': [first, second], 'protected': False}
            return tuple(outputs)
        except BaseException:
            self.poisoned = True
            raise
        finally:
            for gen in generators:
                gen.close()
            self.running = False
