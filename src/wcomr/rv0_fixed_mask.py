"""Fixed offline suffix actions with own-state feasibility and no fallback.

Reuse the pinned official forward's decision hook and original side effects.
The original one-action/adaptive control is unchanged. No sparse attention,
teacher features, learned policy, GPU launcher or video scorer is added here.
"""
import copy
from dataclasses import asdict
import math

import torch

from .rv0_actions import OneActionRouter, OneActionSuffixControl
from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256


class FixedMaskRouter(OneActionRouter):
    def check_context(self, net):
        super().check_context(net)
        if int(net.worldcache_num_steps * net.worldcache_ret_ratio) != 14:
            raise ValueError('Fixed-mask requires the audited 14-call initialization')

    def arm(self, plan):
        if type(plan) is not FixedMaskPlan:
            raise ValueError('Immutable fixed-mask plan required')
        plan.validate()
        if (self.pending is not None or self.plan is not None
                or self.calls != plan.prefix_calls or self.calls % 2
                or len(self.events) != self.calls
                or tuple(e['actual_action'] for e in self.events) != plan.parent_mask[:self.calls]):
            raise ValueError('Fixed-mask parent prefix or CFG boundary differs')
        self.plan, self.consumed = plan, 0

    def decide(self, net, branch, native_skip, original, probe, delta_x, delta_y, threshold):
        self.check_context(net)
        row = self.pending
        if row is None or branch != row['cfg_slot']:
            raise ValueError('Fixed-mask missing current call')
        row.update(paid_probe=True, native_skip=bool(native_skip), selected_skip=bool(native_skip))
        if self.plan is None:
            return native_skip
        expected = self.plan.action_mask()[row['call']-1]
        protected = row['call'] >= 69 or net.cnt < 14
        row.update(planned_action=expected, protected_native_action=protected)
        if protected and ('C' if native_skip else 'D') != expected:
            raise ValueError('Protected native action differs; swap infeasible without fallback')
        if expected == 'C' or row['call'] in self.plan.swap_calls:
            if (len(self.history[branch]) < 2 or len(net.residual_window[branch]) < 2
                    or len(net.probe_residual_window[branch]) < 2
                    or net.residual_cache[branch] is None):
                raise ValueError('Fixed-mask C/D pair lacks own-CFG true-full cache history')
            age = row['solver_step'] - self.history[branch][-1]
            if not 1 <= age <= self.plan.maximum_age_solver_steps:
                raise ValueError('Fixed-mask current source age infeasible')
            row['age_solver_steps'] = age
        for tensor in (original, probe, net.residual_cache[branch]):
            if tensor is not None and not bool(torch.isfinite(tensor).all()):
                raise ValueError('Nonfinite fixed-mask decision state')
        scalars = [float(v) for v in (delta_x, delta_y, threshold,
                                      net.accumulated_rel_l1_distance[branch])]
        if any(not math.isfinite(v) for v in scalars):
            raise ValueError('Nonfinite fixed-mask paid-probe signal')
        row.update(requested=expected, selected_skip=bool(native_skip) if protected else expected == 'C',
                   actual_native_override=(expected == 'C') != bool(native_skip),
                   paid_input_drift=scalars[0], paid_probe_drift=scalars[1],
                   dynamic_threshold=scalars[2], accumulator_before_action=scalars[3])
        self.consumed += 1
        return row['selected_skip']

    def finish(self, net, branch, skipped):
        if self.plan is not None:
            row = self.pending
            if row is None:
                raise ValueError('Fixed-mask missing finish event')
            expected = self.plan.action_mask()[row['call']-1]
            if ('C' if skipped else 'D') != expected:
                raise ValueError('Executed fixed-mask differs; no quota-changing fallback allowed')
            if (expected == 'C' or row['call'] in self.plan.swap_calls) and not row['paid_probe']:
                raise ValueError('Fixed-mask C/D pair has no legal paid-probe decision')
            row.update(planned_action=expected, protected_native_action=row['call'] >= 69 or net.cnt < 14)
        # Leave history bookkeeping/reset exactly as in the unchanged observer.
        # Its single-target assertions are bypassed only for this distinct plan.
        plan = self.plan
        self.plan = None
        try:
            super().finish(net, branch, skipped)
        finally:
            self.plan = plan

    def completed_report(self, prefix_calls):
        if (type(self.plan) is not FixedMaskPlan or prefix_calls != self.plan.prefix_calls
                or self.calls != 72 or self.pending is not None or len(self.events) != 72):
            raise ValueError('Fixed-mask suffix coverage incomplete')
        actual = tuple(e['actual_action'] for e in self.events)
        expected = self.plan.action_mask()
        counts = cfg_full_counts(actual)
        if actual != expected or counts != cfg_full_counts(self.plan.parent_mask):
            raise ValueError('Actual full mask or separate CFG quota differs')
        return {'plan': asdict(self.plan), 'parent_mask_sha256': mask_sha256(self.plan.parent_mask),
                'actual_mask_sha256': mask_sha256(actual), 'actual_actions': list(actual),
                'suffix_events': copy.deepcopy(self.events[prefix_calls:]),
                'per_CFG_full_counts': list(counts), 'quota_matched_per_CFG': True,
                'planned_action_changes': len(self.plan.swap_calls),
                'native_decision_overrides': sum(bool(e.get('actual_native_override')) for e in self.events),
                'protected_calls_preserved_without_override': True,
                'remaining_policy': 'OFFLINE_FIXED_PARENT_MASK_WITH_OPTIONAL_TWO_POSITION_SWAP',
                'states_evolve_independently': True, 'current_truth_used_for_decision': False,
                'equal_runtime': False, 'online_policy': False, 'single_step_RV_label': False,
                'GPU_method_result': False}


class FixedMaskSuffixControl(OneActionSuffixControl):
    def run_mask(self, label, plan):
        if type(plan) is not FixedMaskPlan:
            raise ValueError('Immutable fixed-mask plan required')
        plan.validate()
        if 2*self.completed != plan.prefix_calls:
            raise ValueError('Fixed-mask fork is outside the audited step22 window')
        return self._execute_suffix(label,
            before=lambda: self.router.arm(plan),
            after=lambda: {'action_report': self.router.completed_report(2*self.completed)},
            metadata={'current_action_intervention': bool(plan.swap_calls), 'counterfactual_label': False,
                      'protocol': 'FIXED_PER_CFG_QUOTA_TWO_POSITION_PLACEMENT_DIAGNOSTIC'},
            status='FIXED_MASK_SUFFIX_COMPLETE_CPU_INTERFACE_NOT_METHOD_RESULT')
