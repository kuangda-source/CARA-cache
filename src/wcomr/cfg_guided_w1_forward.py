"""Pinned inside-forward observations and actual RF output-coordinate conversion.

The hooks never choose a cache action or replace deployment outputs. Their
source inverse is checked separately from the existing paired compiler proof.
"""
import ast
import copy
from types import MappingProxyType

from .cfg_paired_probe_forward import (
    _function, _compile, _find_safe, _packet, WC_PATH, WC_SHA, RF_PATH, RF_SHA, PREDICATE,
)
from .cfg_paired_probe_production import _origin, _bindings


def compile_output_denoise(runtime, rf_module):
    """Run the unchanged RF condition body using an explicitly supplied head.

    This has no net invocation, generation side effect or independent teacher.
    The current noise, latent, time and branch condition must come from the
    actual pair that produced the supplied head output.
    """
    _origin(rf_module, runtime, RF_PATH, RF_SHA)
    original = _function(runtime, RF_PATH, RF_SHA, 'denoise')
    node = copy.deepcopy(original)
    call = _find_safe(node, lambda n: isinstance(n, ast.Call) and
        isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and
        n.func.value.id == 'self' and n.func.attr == 'net')
    saved = copy.deepcopy(call)
    class Substitute(ast.NodeTransformer):
        def visit_Call(self, n):
            return ast.Name(id='_supplied_net_output', ctx=ast.Load()) if n is call else self.generic_visit(n)
    node = Substitute().visit(node)
    if any(a.arg == '_supplied_net_output' for a in node.args.args):
        raise ValueError('RF supplied-output argument already exists')
    node.args.kwonlyargs.append(ast.arg(arg='_supplied_net_output'))
    node.args.kw_defaults.append(None)
    inverse = copy.deepcopy(node)
    class Restore(ast.NodeTransformer):
        def visit_Name(self, n):
            return copy.deepcopy(saved) if n.id == '_supplied_net_output' else n
    inverse = Restore().visit(inverse)
    inverse.args.kwonlyargs.pop(); inverse.args.kw_defaults.pop()
    if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('RF output conversion changed condition processing')
    function = _compile(node, vars(rf_module), RF_PATH+'#supplied-output-denoise')
    bindings = _bindings(function, vars(rf_module), {})
    return function, MappingProxyType({'RF_source_sha256': RF_SHA,
        'supplied_output_inverse_AST_equal': True, 'actual_RF_globals': bindings,
        'net_calls': 0, 'teacher_or_same_state_proof': False})


def compile_collection(runtime, wc_module, rf_module, collector):
    """Three read-only observation sites; one paired predicate and RF net pause."""
    _origin(wc_module, runtime, WC_PATH, WC_SHA); _origin(rf_module, runtime, RF_PATH, RF_SHA)
    original = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
    node = copy.deepcopy(original)
    decision = _find_safe(node, lambda n: isinstance(n, ast.If) and ast.unparse(n.test) == PREDICATE)
    saved = copy.deepcopy(decision.test)
    decision.test = ast.Yield(value=ast.Call(func=ast.Name(id='_paid_probe', ctx=ast.Load()), args=[
        ast.Name(id='current_idx', ctx=ast.Load()),
        ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='cnt', ctx=ast.Load()),
        saved, ast.Name(id='delta_x', ctx=ast.Load()), ast.Name(id='delta_y', ctx=ast.Load()),
        ast.Name(id='dynamic_thresh', ctx=ast.Load())], keywords=[]))
    hits = {'prewarp': 0, 'hidden': 0, 'output': 0}
    targets = {
        'prewarp': 'self.previous_internal_states[current_idx] = test_x',
        'hidden': 'x_B_T_H_W_O = self.final_layer(x_B_T_H_W_D, t_embedding_B_T_D, adaln_lora_B_T_3D=adaln_lora_B_T_3D)',
        'output': 'x_B_C_Tt_Hp_Wp = self.unpatchify(x_B_T_H_W_O)',
    }
    hooks = {
        'prewarp': '_mf_a_prewarp(self, current_idx, x_B_T_H_W_D)',
        'hidden': '_mf_a_hidden(self, skip_forward, current_idx, ori_x, test_x, x_B_T_H_W_D, block_kwargs, t_embedding_B_T_D, adaln_lora_B_T_3D)',
        'output': '_mf_a_output(self, current_idx, x_B_C_Tt_Hp_Wp)',
    }
    class Observe(ast.NodeTransformer):
        def visit_Assign(self, n):
            for name, source in targets.items():
                if ast.unparse(n) == source:
                    hits[name] += 1; hook = ast.parse(hooks[name]).body[0]
                    return [n, hook] if name == 'output' else [hook, n]
            return self.generic_visit(n)
    node = Observe().visit(node)
    if hits != {'prewarp': 1, 'hidden': 1, 'output': 1}:
        raise ValueError('Pinned internal collection sites differ: '+str(hits))
    inverse = copy.deepcopy(node)
    class Undo(ast.NodeTransformer):
        def visit_Expr(self, n):
            if isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id.startswith('_mf_a_'):
                return None
            return self.generic_visit(n)
        def visit_If(self, n):
            if isinstance(n.test, ast.Yield): n.test = copy.deepcopy(saved)
            return self.generic_visit(n)
    inverse = Undo().visit(inverse)
    if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('Collection changed WC outside registered observations/predicate')
    helpers = {'_paid_probe': _packet, '_mf_a_prewarp': collector.prewarp,
               '_mf_a_hidden': collector.hidden, '_mf_a_output': collector.output}
    net = _compile(node, dict(vars(wc_module), **helpers), WC_PATH+'#guided-W1-collection')
    net_bindings = _bindings(net, vars(wc_module), helpers)

    rf_original = _function(runtime, RF_PATH, RF_SHA, 'denoise')
    rf_node = copy.deepcopy(rf_original)
    call = _find_safe(rf_node, lambda n: isinstance(n, ast.Call) and
        isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and
        n.func.value.id == 'self' and n.func.attr == 'net')
    net_call = copy.deepcopy(call)
    class Pair(ast.NodeTransformer):
        def visit_Call(self, n):
            if n is call:
                return ast.YieldFrom(value=ast.Call(func=ast.Name(id='_paired_net', ctx=ast.Load()),
                    args=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='net', ctx=ast.Load())]+n.args,
                    keywords=n.keywords))
            return self.generic_visit(n)
    rf_node = Pair().visit(rf_node)
    rf_inverse = copy.deepcopy(rf_node)
    class Unpair(ast.NodeTransformer):
        def visit_YieldFrom(self, n): return copy.deepcopy(net_call)
    rf_inverse = Unpair().visit(rf_inverse)
    if ast.dump(rf_inverse, include_attributes=False) != ast.dump(rf_original, include_attributes=False):
        raise ValueError('Collection changed RF outside paired net call')
    denoise = _compile(rf_node, dict(vars(rf_module), _paired_net=net), RF_PATH+'#guided-W1-collection')
    rf_bindings = _bindings(denoise, vars(rf_module), {'_paired_net': net})

    # Reuse the exact Flow-Warped Scaling statements on candidate prewarp output.
    warp_nodes = [n for n in ast.walk(original) if isinstance(n, ast.If) and
        ast.unparse(n.test) == "getattr(self, 'worldcache_flow_enabled', False) and self.previous_input[current_idx] is not None"]
    if len(warp_nodes) != 1: raise ValueError('Ambiguous pinned flow warp')
    warp = ast.parse('def _candidate_warp(self, x_B_T_H_W_D, residual_x, T):\n    current_idx = self.cnt % 2\n    return x_B_T_H_W_D').body[0]
    warp.body.insert(1, copy.deepcopy(warp_nodes[0]))
    warp_function = _compile(warp, vars(wc_module), WC_PATH+'#guided-W1-exact-warp')
    collector.warp = warp_function
    collector.to_velocity, conversion = compile_output_denoise(runtime, rf_module)
    return net, denoise, MappingProxyType({'WC_source_sha256': WC_SHA, 'RF_source_sha256': RF_SHA,
        'WC_collection_inverse_AST_equal': True, 'RF_collection_inverse_AST_equal': True,
        'explicit_observation_sites': hits, 'production_WC_globals': net_bindings,
        'production_RF_globals': rf_bindings, 'RF_output_conversion': dict(conversion),
        'warp_statements_are_source_exact': True, 'real_model_teacher_or_parity_claim': False})
