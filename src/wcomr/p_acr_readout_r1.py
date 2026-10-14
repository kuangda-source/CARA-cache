"""One true CFG branch with a shared paid prefix and source-preserving ACR readout.

This executor is independent of frozen H1. It supplies a diagnostic/readout
primitive, not a refreshed source or a new controller/production GPU entry.
Both source-bound shallow probes run once; cached A and one dense continuation
share their actual prefix. No current omitted-branch teacher is available here.
"""
import ast
import copy
from contextlib import nullcontext
import math
from types import SimpleNamespace

import torch

from .cfg_paired_probe_forward import _function, _find_safe, _compile, _packet, WC_PATH, WC_SHA, RF_PATH, RF_SHA, PREDICATE
from .cfg_paired_probe_production import _origin, _bindings
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .cfg_guided_w1_forward import compile_output_denoise
from .math_n2_source_readout_r1 import SourceFusionReadout

VERSION = 'CFG_SINGLE_BRANCH_ACR_READOUT_SHARED_PREFIX_R1'
CACHE_FIELDS = ('accumulated_rel_l1_distance', 'residual_cache', 'probe_residual_cache',
                'previous_internal_states', 'previous_input', 'previous_output', 'resume_flag')
WINDOW_FIELDS = ('residual_window', 'probe_residual_window')


def compensate(base_A, dense_one, *, direction, coefficient):
    """Exact post-RF branch formula, with only one supplied dense velocity."""
    if direction not in ('Pc', 'Pu') or not math.isfinite(coefficient):
        raise ValueError('Frozen direction and finite scalar coefficient required')
    if not isinstance(base_A, tuple) or len(base_A) != 2:
        raise ValueError('Both actual A branch velocities required')
    side = 0 if direction == 'Pc' else 1
    if any(v.shape != dense_one.shape or v.dtype != dense_one.dtype or v.device != dense_one.device for v in base_A):
        raise ValueError('Same-state post-RF geometry and precision required')
    innovation = dense_one - base_A[side]
    if side == 0:
        return dense_one, base_A[1] + coefficient * innovation
    return base_A[0] + coefficient * innovation, dense_one


def _cached_compiler(runtime, wc, rf, collector):
    """Extract source-exact cache/warp/head and native counter statements.

    The new helper stops after unpatchify, never computes a Block or increments
    the branch counter. Two branch metadata writes remain exactly those of C.
    Original dense and RF continuation bodies are not rewritten.
    """
    _origin(wc, runtime, WC_PATH, WC_SHA); _origin(rf, runtime, RF_PATH, RF_SHA)
    original = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
    cache_if = _find_safe(original, lambda n: isinstance(n, ast.If) and ast.unparse(n.test) == 'skip_forward')
    cache_nodes = copy.deepcopy(cache_if.body)
    heads = [n for n in original.body if isinstance(n, ast.Assign) and ast.unparse(n).startswith('x_B_T_H_W_O = self.final_layer(')]
    unpatch = [n for n in original.body if isinstance(n, ast.Assign) and ast.unparse(n) == 'x_B_C_Tt_Hp_Wp = self.unpatchify(x_B_T_H_W_O)']
    if len(heads) != 1 or len(unpatch) != 1:
        raise ValueError('Pinned actual head/unpatchify sites changed')
    fields = ('self', 'current_idx', 'x_B_T_H_W_D', 'ori_x', 'test_x', 'block_kwargs',
              't_embedding_B_T_D', 'adaln_lora_B_T_3D', 'T')
    helper = ast.parse('def cached(' + ','.join(fields) + '):\n    pass').body[0]
    prewarp_hits = 0
    for i, node in enumerate(cache_nodes):
        if ast.unparse(node) == 'self.previous_internal_states[current_idx] = test_x':
            cache_nodes.insert(i, ast.parse('_acr_readout.prewarp(self,current_idx,x_B_T_H_W_D)').body[0])
            prewarp_hits += 1; break
    if prewarp_hits != 1:
        raise ValueError('Pinned prewarp source location differs')
    helper.body = [ast.parse('residual_x = self.residual_cache[current_idx]').body[0], *cache_nodes,
        ast.parse('_acr_readout.semantic_hidden(self,True,current_idx,ori_x,test_x,x_B_T_H_W_D,block_kwargs,t_embedding_B_T_D,adaln_lora_B_T_3D)').body[0],
        copy.deepcopy(heads[0]), copy.deepcopy(unpatch[0]),
        ast.parse('_acr_readout.output(self,current_idx,x_B_C_Tt_Hp_Wp)').body[0],
        ast.parse('return x_B_C_Tt_Hp_Wp').body[0]]
    cached_head = _compile(helper, dict(vars(wc), _acr_readout=collector.readout), WC_PATH + '#acr-cached-prefix')
    # Native C flag and skipped-count updates, extracted rather than guessed.
    decision = _find_safe(original, lambda n: isinstance(n, ast.If) and ast.unparse(n.test) == PREDICATE)
    flag = ast.parse('def finish_cached(self,current_idx):\n    pass').body[0]
    flag.body = copy.deepcopy(decision.body[:3])
    if [ast.unparse(n) for n in flag.body] != ['skip_forward = True', 'self.worldcache_step_skipped_count += 1', 'self.resume_flag[current_idx] = False']:
        raise ValueError('Pinned cache flags differ')
    increment = next(i for i, n in enumerate(original.body) if ast.unparse(n) == 'self.cnt += 1')
    flag.body.extend(copy.deepcopy(original.body[increment:increment + 2]))
    if not isinstance(flag.body[-1], ast.If) or ast.unparse(flag.body[-1].test) != 'self.cnt >= self.worldcache_num_steps':
        raise ValueError('Pinned native70 reset block differs')
    finish_cached = _compile(flag, vars(wc), WC_PATH + '#acr-cache-counter')
    flows = [n for n in ast.walk(cache_if) if isinstance(n, ast.If) and ast.unparse(n.test) == "getattr(self, 'worldcache_flow_enabled', False) and self.previous_input[current_idx] is not None"]
    if len(flows) != 1:
        raise ValueError('Pinned flow body differs')
    warp = ast.parse('def warp(self,x_B_T_H_W_D,residual_x,T):\n    current_idx=self.cnt%2\n    return x_B_T_H_W_D').body[0]
    warp.body.insert(1, copy.deepcopy(flows[0]))
    collector.warp = _compile(warp, vars(wc), WC_PATH + '#acr-exact-warp')
    collector.to_velocity, conversion = compile_output_denoise(runtime, rf)
    return cached_head, finish_cached, {
        'WC_source_sha256': WC_SHA, 'RF_source_sha256': RF_SHA,
        'cached_branch_statements_source_exact': True, 'flow_and_head_statements_source_exact': True,
        'native_counter_reset_statements_source_exact': True, 'helper_deep_blocks': 0,
        'RF_conversion': dict(conversion), 'not_actual_model_or_speed_proof': True,
    }


def _prefix_compiler(runtime, wc, rf, observe):
    original = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
    node = copy.deepcopy(original)
    target = _find_safe(node, lambda n: isinstance(n, ast.If) and ast.unparse(n.test) == PREDICATE)
    predicate = copy.deepcopy(target.test)
    arguments = 'self,current_idx,x_B_T_H_W_D,ori_x,test_x,block_kwargs,t_embedding_B_T_D,adaln_lora_B_T_3D,T'
    before = ast.parse('_acr_prefix(' + arguments + ')').body[0]
    target.test = ast.Yield(value=ast.Call(func=ast.Name(id='_paid_probe', ctx=ast.Load()), args=[
        ast.Name(id='current_idx', ctx=ast.Load()), ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='cnt', ctx=ast.Load()),
        predicate, ast.Name(id='delta_x', ctx=ast.Load()), ast.Name(id='delta_y', ctx=ast.Load()), ast.Name(id='dynamic_thresh', ctx=ast.Load())], keywords=[]))
    class Insert(ast.NodeTransformer):
        def visit_If(self, n):
            return [copy.deepcopy(before), n] if n is target else self.generic_visit(n)
    node = Insert().visit(node)
    inverse = copy.deepcopy(node)
    class Undo(ast.NodeTransformer):
        def visit_Expr(self, n):
            if isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == '_acr_prefix':
                return None
            return self.generic_visit(n)
        def visit_If(self, n):
            if isinstance(n.test, ast.Yield): n.test = copy.deepcopy(predicate)
            return self.generic_visit(n)
    inverse = Undo().visit(inverse)
    if ast.dump(inverse, include_attributes=False) != ast.dump(original, include_attributes=False):
        raise ValueError('ACR prefix changed original WC outside observer/pause')
    net = _compile(node, dict(vars(wc), _acr_prefix=observe, _paid_probe=_packet), WC_PATH + '#acr-paid-prefix')
    rf_original = _function(runtime, RF_PATH, RF_SHA, 'denoise')
    rf_node = copy.deepcopy(rf_original)
    call = _find_safe(rf_node, lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                      and isinstance(n.func.value, ast.Name) and n.func.value.id == 'self' and n.func.attr == 'net')
    saved = copy.deepcopy(call)
    class Pair(ast.NodeTransformer):
        def visit_Call(self, n):
            return ast.YieldFrom(value=ast.Call(func=ast.Name(id='_paired_net', ctx=ast.Load()),
                args=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='net', ctx=ast.Load())] + n.args, keywords=n.keywords)) if n is call else self.generic_visit(n)
    rf_node = Pair().visit(rf_node)
    rf_inverse = copy.deepcopy(rf_node)
    class Restore(ast.NodeTransformer):
        def visit_YieldFrom(self, n): return copy.deepcopy(saved)
    rf_inverse = Restore().visit(rf_inverse)
    if ast.dump(rf_inverse, include_attributes=False) != ast.dump(rf_original, include_attributes=False):
        raise ValueError('ACR changed RF beyond paired net call')
    denoise = _compile(rf_node, dict(vars(rf), _paired_net=net), RF_PATH + '#acr-paired-denoise')
    _bindings(net, vars(wc), {'_acr_prefix': observe, '_paid_probe': _packet})
    _bindings(denoise, vars(rf), {'_paired_net': net})
    return denoise, {'WC_prefix_inverse_AST_equal': True, 'RF_inverse_AST_equal': True,
                     'dense_continuation_body_unchanged': True, 'two_prefixes_shared': True}


class ACRReadoutExecutor(NativePolicyPairedExecutor):
    """A single non-committing primitive, with C-compatible legacy source state.

    Parent controller/working/true-D histories are READ ONLY. Caller owns the
    full diagnostic snapshot/restore. Runtime source windows stay old, while
    ordinary C input/probe bookkeeping advances; cycle70 reset remains exact.
    """
    def __init__(self, model, *, runtime, wc, rf, context, dense, working, gamma,
                 direction, coefficient, step, projection_readonly=nullcontext):
        if (direction not in ('Pc', 'Pu') or not math.isfinite(coefficient)
                or not 8 <= step <= 35 or model.net.cnt != 2 * (step - 1)
                or len(dense) != 2 or len(working) != 2 or any(v is None for v in working)):
            raise ValueError('Actual eligible two-source step, frozen scalar/direction and past D bank required')
        net = model.net
        if (int(net.worldcache_num_steps) != 70 or net.cnt < int(70 * net.worldcache_ret_ratio)
                or any(getattr(net, field)[b] is None for field in
                       ('previous_input', 'previous_internal_states', 'residual_cache', 'probe_residual_cache') for b in (0, 1))
                or any(c.context != context or not c.anchors or c.anchors[-1].step >= step for c in dense)
                or any(w['kind'] not in ('D', 'P') or w['created_step'] >= step for w in working)):
            raise ValueError('ACR rejects cold/protected/future sources before any model execution')
        self.direction, self.coefficient, self.step = direction, float(coefficient), step
        self.side = 0 if direction == 'Pc' else 1
        self.prefix, self.cached_v = {}, {}
        self.reference = SimpleNamespace(model=model, net=model.net, context=context, dense=dense,
            working=working, current={'action': 'C', 'source_choice': SimpleNamespace(reason='MATH_ACR:A')},
            warp=None, to_velocity=None)
        self.readout = SourceFusionReadout(self.reference, method='BETA1_ONE_PHASE', gamma=gamma, mode='FUSION')
        self.readout.completed = step - 1
        self.reference.readout = self.readout
        self.cached_head, self.finish_cached, self.cached_proof = _cached_compiler(runtime, wc, rf, self.reference)
        self.readout.warp, self.readout.to_velocity = self.reference.warp, self.reference.to_velocity
        denoise, self.prefix_proof = _prefix_compiler(runtime, wc, rf, self._observe_prefix)
        super().__init__(model, denoise, torch, wc_forward=wc.worldcache_mini_train_dit_forward,
                         rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
        self.projection_readonly = projection_readonly
        self.used = False

    def _observe_prefix(self, net, slot, *values):
        if net is not self.net or slot in self.prefix:
            raise ValueError('Exactly one actual prefix per CFG branch required')
        self.prefix[slot] = (net, slot, *values)

    def _select(self, packets):
        if set(self.prefix) != {0, 1} or [p.slot for p in packets] != [0, 1]:
            raise ValueError('Both paid prefixes must precede ACR choice')
        count = 2 * (self.step - 1)
        for slot in (0, 1):
            self.net.cnt = count + slot
            head = self.cached_head(*self.prefix[slot])
            cur = self.readout.current
            self.cached_v[slot] = self.reference.to_velocity(self.model, cur['noise'], cur['latent'], cur['timestep'],
                cur['conditions'][slot], _supplied_net_output=head)
        self.net.cnt = count
        return 'DC' if self.side == 0 else 'CD'

    def _finish(self, gen, skip):
        slot = int(self.net.cnt) % 2
        if skip:
            gen.close()
            value = self.cached_v[slot]
            self.finish_cached(self.net, slot)
            return value
        # The normal dense branch replaces cache fields/windows. Retain the
        # current C-compatible bookkeeping and strictly old working source.
        saved = {field: getattr(self.net, field)[slot] for field in CACHE_FIELDS}
        windows = {field: (getattr(self.net, field)[slot], tuple(getattr(self.net, field)[slot])) for field in WINDOW_FIELDS}
        value = super()._finish(gen, False)
        if self.net.cnt != 0:
            for field, old in saved.items(): getattr(self.net, field)[slot] = old
            self.net.resume_flag[slot] = False
            for field, (container, entries) in windows.items():
                container[:] = entries; getattr(self.net, field)[slot] = container
        return value

    @torch.no_grad()
    def execute(self, noise, latent, timestep, conditions):
        if self.used:
            raise ValueError('One origin/one ACR execution per primitive instance')
        self.used = True
        before = copy.deepcopy([c.receipt() for c in self.reference.dense])
        self.readout.begin(noise, latent, timestep, conditions)
        try:
            with self.projection_readonly():
                physical = self.pair(noise, latent, timestep, conditions, self._select)
            if self.last['protected'] or self.last['action'] not in ('DC', 'CD'):
                raise ValueError('No asymmetric primitive at protected/no-source boundary')
            base_A = self.readout.end(tuple(self.cached_v[b] for b in (0, 1)), 'CC')
            result = compensate(base_A, physical[self.side], direction=self.direction, coefficient=self.coefficient)
            if [c.receipt() for c in self.reference.dense] != before:
                raise ValueError('ACR updated trusted true-D history')
            self.last.update(version=VERSION, semantic_action=self.direction, coefficient=self.coefficient,
                paid_prefixes=2, actual_dense_branches=1, actual_omitted_branch_teacher_calls=0,
                source_kind='ACR_READOUT_NOT_REFRESH', working_source_updated=False,
                true_D_updated=False, base_A_readout=self.readout.history[-1])
            return result, base_A, physical[self.side]
        except BaseException:
            self.poisoned = self.readout.poisoned = True
            raise
