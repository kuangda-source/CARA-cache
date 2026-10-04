"""One diagnostic C/D decision; original adaptive WorldCache suffix afterwards.

No budget-matched policy, learned router, teacher labels or production CLI.
"""
import ast
import copy
from dataclasses import dataclass, asdict
import hashlib
import inspect
import math
import types

import torch

from .rv0_fork import SamplerSuffixControl

WC_SHA = 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903'


@dataclass(frozen=True)
class OneAction:
    action: str
    target_call: int
    cfg_slot: int
    maximum_age_solver_steps: int

    def validate(self):
        if (self.action not in ('OFF', 'C', 'D') or type(self.target_call) is not int
                or not 15 <= self.target_call <= 68 or type(self.cfg_slot) is not int
                or self.cfg_slot not in (0, 1) or self.cfg_slot != (self.target_call - 1) % 2
                or type(self.maximum_age_solver_steps) is not int
                or not 1 <= self.maximum_age_solver_steps <= 33):
            raise ValueError('Explicit one-action CFG/protected-window/age plan differs')


class OneActionRouter:
    def __init__(self, context):
        if type(context) is not tuple or len(context) != 3 or any(type(x) is not str or not x for x in context):
            raise ValueError('One-action request/model/condition context missing')
        self.context = context
        self.calls, self.epoch, self.pending = 0, 0, None
        self.history, self.events, self.plan, self.consumed = [[], []], [], None, 0
        self.net = None

    def install(self, net, wc, source_path):
        if self.net is not None or hasattr(net, '_wc_rv0_router'):
            raise ValueError('One-action router already installed')
        self.net = net
        self.model_key = (id(net), getattr(net, '_w1_expert_key', None))
        self.original_forward = net.forward
        self.owned_forward = 'forward' in vars(net)
        try:
            fn = build_one_action_forward(wc.worldcache_mini_train_dit_forward, self, source_path)
            net.forward = types.MethodType(fn, net)
            net._wc_rv0_router = self
        except BaseException:
            self.net = None
            raise

    def check_context(self, net):
        if (net is not self.net or getattr(net, '_wc_rv0_router', None) is not self
                or self.model_key != (id(net), getattr(net, '_w1_expert_key', None))
                or net.worldcache_num_steps != 70
                or any(m.training for m in net.modules())
                or getattr(net, '_wc_refresh_adapter', None) is not None):
            raise ValueError('One-action model/expert/WC/source context changed')

    def begin(self, net, branch):
        self.check_context(net)
        if self.pending is not None or net.cnt != self.calls % 70 or branch != self.calls % 2:
            raise ValueError('One-action nested call or CFG/counter drift')
        self.calls += 1
        self.pending = {'call': self.calls, 'cfg_slot': branch,
            'solver_step': (self.calls - 1) // 2 + 1, 'epoch': self.epoch,
            'paid_probe': False, 'native_skip': None, 'requested': None,
            'selected_skip': False, 'current_deep_truth_used': False}

    def decide(self, net, branch, native_skip, original, probe, delta_x, delta_y, threshold):
        self.check_context(net)
        row = self.pending
        if row is None or branch != row['cfg_slot']:
            raise ValueError('One-action missing current call')
        row.update(paid_probe=True, native_skip=bool(native_skip), selected_skip=bool(native_skip))
        if self.plan is None or row['call'] != self.plan.target_call:
            return native_skip
        self.plan.validate()
        if branch != self.plan.cfg_slot:
            raise ValueError('One-action target CFG differs')
        if self.plan.action == 'OFF':
            return native_skip
        if (self.consumed or net.cnt < int(net.worldcache_num_steps * net.worldcache_ret_ratio)
                or row['call'] >= 69 or len(self.history[branch]) < 2
                or len(net.residual_window[branch]) < 2
                or len(net.probe_residual_window[branch]) < 2
                or net.residual_cache[branch] is None):
            raise ValueError('C/D target lacks protected-window or same-CFG true-full history')
        for tensor in (original, probe, net.residual_cache[branch]):
            if not bool(torch.isfinite(tensor).all()):
                raise ValueError('Nonfinite C/D decision state')
        scalars = [float(v) for v in (delta_x, delta_y, threshold,
                   net.accumulated_rel_l1_distance[branch])]
        if any(not math.isfinite(v) for v in scalars):
            raise ValueError('Nonfinite paid-probe C/D signal')
        age = row['solver_step'] - self.history[branch][-1]
        if not 1 <= age <= self.plan.maximum_age_solver_steps:
            raise ValueError('C/D current source age infeasible')
        row.update(requested=self.plan.action, selected_skip=self.plan.action == 'C',
                   age_solver_steps=age, paid_input_drift=scalars[0], paid_probe_drift=scalars[1],
                   dynamic_threshold=scalars[2], accumulator_before_action=scalars[3])
        self.consumed += 1
        return row['selected_skip']

    def finish(self, net, branch, skipped):
        self.check_context(net)
        row = self.pending
        if row is None or branch != row['cfg_slot'] or bool(skipped) != row['selected_skip']:
            raise ValueError('C/D executed branch differs from selected decision')
        if self.plan and row['call'] == self.plan.target_call and self.plan.action != 'OFF' and row['requested'] is None:
            raise ValueError('C/D target has no legal paid-probe decision')
        if not skipped:
            self.history[branch].append(row['solver_step'])
            self.history[branch] = self.history[branch][-2:]
        row.update(actual_action='C' if skipped else 'D', true_full_history=copy.deepcopy(self.history),
                   native_cycle_reset=net.cnt == 69)
        self.events.append(row)
        self.pending = None
        if net.cnt == 69:
            self.history = [[], []]; self.epoch += 1

    def arm(self, plan):
        if type(plan) is not OneAction:
            raise ValueError('Immutable one-action plan required')
        plan.validate()
        if self.pending or self.plan is not None or self.calls % 2 or plan.target_call not in (self.calls+1, self.calls+2):
            raise ValueError('One action must target the next complete CFG step')
        self.plan, self.consumed = plan, 0

    def snapshot(self):
        if self.pending is not None:
            raise ValueError('Cannot capture a partial C/D call')
        return copy.deepcopy({'context': self.context, 'calls': self.calls, 'epoch': self.epoch,
            'history': self.history, 'events': self.events, 'plan': self.plan, 'consumed': self.consumed})

    def restore(self, state):
        if state['context'] != self.context:
            raise ValueError('C/D metadata restored into another request')
        for key in ('calls', 'epoch', 'history', 'events', 'plan', 'consumed'):
            setattr(self, key, copy.deepcopy(state[key]))
        self.pending = None

    def completed_report(self, prefix_calls):
        if not self.plan or self.calls != 72 or self.pending or self.consumed != int(self.plan.action != 'OFF'):
            raise ValueError('Planned C/D suffix target/coverage incomplete')
        return {'plan': asdict(self.plan), 'suffix_events': copy.deepcopy(self.events[prefix_calls:]),
                'decision_interventions': self.consumed, 'remaining_policy': 'ORIGINAL_WC_ADAPTIVE',
                'same_remaining_policy_function_not_same_future_action_mask': True,
                'budget_matched': False, 'current_truth_used_for_decision': False,
                'RV_label': False}

    def close(self):
        if self.net is None: return
        if self.owned_forward: self.net.forward = self.original_forward
        else: delattr(self.net, 'forward')
        delattr(self.net, '_wc_rv0_router')
        self.net = None


def build_one_action_forward(original, router, source_path):
    raw = source_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != WC_SHA:
        raise ValueError('One-action pinned WorldCache source differs')
    pinned = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == original.__name__)
    actual = ast.parse(inspect.getsource(original)).body[0]
    if ast.dump(pinned, include_attributes=False) != ast.dump(actual, include_attributes=False):
        raise ValueError('One-action original forward body differs')
    node = copy.deepcopy(pinned); counts = [0, 0, 0]
    predicate = ast.dump(ast.parse('self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh', mode='eval').body)
    class Instrument(ast.NodeTransformer):
        def visit_Assign(self, value):
            if len(value.targets) == 1 and isinstance(value.targets[0], ast.Name) and value.targets[0].id == 'current_idx':
                counts[0] += 1
                return [value, ast.parse('_rv0_router.begin(self, current_idx)').body[0]]
            return self.generic_visit(value)
        def visit_If(self, value):
            if ast.dump(value.test) == predicate:
                counts[1] += 1
                value.test = ast.Call(func=ast.Attribute(ast.Name('_rv0_router', ast.Load()), 'decide', ast.Load()),
                    args=[ast.Name('self', ast.Load()), ast.Name('current_idx', ast.Load()), value.test]
                         + [ast.Name(n, ast.Load()) for n in ('ori_x', 'test_x', 'delta_x', 'delta_y', 'dynamic_thresh')], keywords=[])
            return self.generic_visit(value)
        def visit_AugAssign(self, value):
            if (isinstance(value.target, ast.Attribute) and isinstance(value.target.value, ast.Name)
                    and value.target.value.id == 'self' and value.target.attr == 'cnt'):
                counts[2] += 1
                return [ast.parse('_rv0_router.finish(self, current_idx, skip_forward)').body[0], value]
            return self.generic_visit(value)
    node = Instrument().visit(node)
    if counts != [1, 1, 1]: raise ValueError('One-action pinned decision anchors differ')
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, node], type_ignores=[]))
    namespace = {**original.__globals__, '_rv0_router': router}
    exec(compile(module, str(source_path)+'#rv0-one-action', 'exec'), namespace)
    fn = namespace[original.__name__]
    fn.routing_ast_sha256 = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
    return fn


class OneActionSuffixControl(SamplerSuffixControl):
    def __init__(self, *args, router, **kwargs):
        self.router = router
        super().__init__(*args, **kwargs)
        router.check_context(self.net)
        if router.context != self.context or router.calls != 2*self.completed or router.plan:
            raise ValueError('C/D fork context or prefix ledger differs')
        self.router_parent = router.snapshot()

    def restore_parent(self):
        self.router.restore(self.router_parent)
        return super().restore_parent()

    def run_action(self, label, plan):
        if type(plan) is not OneAction: raise ValueError('Immutable one-action plan required')
        plan.validate()
        return self._execute_suffix(label,
            before=lambda: self.router.arm(plan),
            after=lambda: {'action_report': self.router.completed_report(2*self.completed)},
            metadata={'current_action_intervention': plan.action != 'OFF',
                      'counterfactual_label': False,
                      'protocol': 'ONE_CURRENT_ACTION_SHARED_ADAPTIVE_SUFFIX_NOT_BUDGET_MATCHED'},
            status='C_D_SUFFIX_COMPLETE_INTERFACE_ONLY_NOT_RV_LABEL')
