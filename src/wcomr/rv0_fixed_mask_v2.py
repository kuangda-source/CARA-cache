"""R2 controls executed tail actions; native proposals are recorded separately.

R1 remains unchanged. Initialization/reset, paid probes, legal own-CFG cache
history and exact executed quotas remain mandatory. No quota repair fallback.
"""
import copy
import math

import torch

from .rv0_fixed_mask import FixedMaskRouter, FixedMaskSuffixControl
from .rv0_fixed_plan import cfg_full_counts
from .rv0_placement_v2_scope import TAIL_CONTRACT


class FixedMaskRouterV2(FixedMaskRouter):
    def arm(self, plan):
        super().arm(plan)
        self._armed_plan_value = copy.deepcopy(plan)

    def restore(self, state):
        super().restore(state)
        self._armed_plan_value = copy.deepcopy(self.plan)

    def check_plan_seal(self):
        if self.plan is not None and self.plan != self._armed_plan_value:
            raise ValueError('R2 immutable armed plan changed; no tail/quota repair allowed')

    def decide(self, net, branch, native_skip, original, probe, delta_x, delta_y, threshold):
        self.check_context(net)
        row = self.pending
        if row is None or branch != row['cfg_slot']:
            raise ValueError('R2 fixed-mask missing current call')
        row.update(paid_probe=True, native_skip=bool(native_skip), selected_skip=bool(native_skip))
        if self.plan is None:
            return native_skip
        self.check_plan_seal()
        expected = self.plan.action_mask()[row['call']-1]
        protected = row['call'] >= 69 or net.cnt < 14
        row.update(planned_action=expected, protected_native_action=protected,
                   protected_executed_action=protected, tail_contract=TAIL_CONTRACT)
        # This branch should be unreachable in the pinned forward, which does
        # not probe during initialization. It must never become forced reuse.
        if net.cnt < 14 and (expected != 'D' or bool(native_skip)):
            raise ValueError('R2 original initialization/reset full action differs')
        if expected == 'C' or row['call'] in self.plan.swap_calls:
            if (len(self.history[branch]) < 2 or len(net.residual_window[branch]) < 2
                    or len(net.probe_residual_window[branch]) < 2
                    or net.residual_cache[branch] is None):
                raise ValueError('R2 fixed-mask C/D pair lacks own-CFG true-full cache history')
            age = row['solver_step'] - self.history[branch][-1]
            if not 1 <= age <= self.plan.maximum_age_solver_steps:
                raise ValueError('R2 fixed-mask current source age infeasible')
            row['age_solver_steps'] = age
        for tensor in (original, probe, net.residual_cache[branch]):
            if tensor is not None and not bool(torch.isfinite(tensor).all()):
                raise ValueError('Nonfinite R2 fixed-mask decision state')
        scalars = [float(v) for v in (delta_x, delta_y, threshold,
                                      net.accumulated_rel_l1_distance[branch])]
        if any(not math.isfinite(v) for v in scalars):
            raise ValueError('Nonfinite R2 fixed-mask paid-probe signal')
        override = (expected == 'C') != bool(native_skip)
        row.update(requested=expected, selected_skip=expected == 'C',
                   actual_native_override=override,
                   tail_native_proposal_disagreement=bool(row['call'] in (69,70) and override),
                   paid_input_drift=scalars[0], paid_probe_drift=scalars[1],
                   dynamic_threshold=scalars[2], accumulator_before_action=scalars[3])
        self.consumed += 1
        return row['selected_skip']

    def finish(self, net, branch, skipped):
        self.check_plan_seal()
        super().finish(net, branch, skipped)

    def completed_report(self, prefix_calls):
        self.check_plan_seal()
        report = super().completed_report(prefix_calls)
        report.update(tail_contract=TAIL_CONTRACT,
            protected_calls_preserved_without_override=False,
            protected_executed_actions_preserved=True,
            native_tail_proposal_preservation_required=False,
            tail_native_proposal_disagreements=[e['call'] for e in self.events
                if e.get('tail_native_proposal_disagreement')])
        return report


class FixedMaskSuffixControlV2(FixedMaskSuffixControl):
    def restore_parent(self):
        # The immutable R1 restored the router before its failure was saved.
        # R2 captures the pending decision first, without affecting selection.
        if (self.router.pending is not None and self.records
                and self.records[-1]['status'] == 'TECH_BLOCKED'):
            self.records[-1]['failure_router_before_restore'] = {
                'pending':copy.deepcopy(self.router.pending),
                'completed_events':copy.deepcopy(self.router.events),
                'completed_per_CFG_full_counts':list(cfg_full_counts(
                    [e['actual_action'] for e in self.router.events])),
                'history':copy.deepcopy(self.router.history)}
        return super().restore_parent()
