"""Registered joint swaps, then native own-state decisions only at calls 69/70.

Fixed controls use the unchanged R2 implementation. A responsive tail has no
fixed quota: its original WorldCache side effects and costs are outcomes.
"""
import copy
from dataclasses import asdict

from .rv0_actions import OneActionRouter
from .rv0_fixed_mask_v2 import FixedMaskRouterV2, FixedMaskSuffixControlV2
from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256

TAIL_CALLS = (69, 70)
TAIL_POLICY = 'FIXED_REGISTERED_SWAP_THROUGH68_NATIVE_OWN_STATE69_70_ORIGINAL_RESET71_72'


class NativeTailRouter(FixedMaskRouterV2):
    def __init__(self, context):
        super().__init__(context)
        self.native_tail = False
        self._armed_tail_mode = False

    def arm_mode(self, plan, native_tail):
        if type(native_tail) is not bool or self.native_tail:
            raise ValueError('Explicit immutable native-tail mode required')
        super().arm(plan)
        self.native_tail = self._armed_tail_mode = native_tail

    def check_plan_seal(self):
        super().check_plan_seal()
        if self.native_tail != self._armed_tail_mode or self.native_tail and self.plan is None:
            raise ValueError('Armed native-tail mode changed')

    def snapshot(self):
        return {**super().snapshot(), 'native_tail': self.native_tail}

    def restore(self, state):
        super().restore(state)
        self.native_tail = self._armed_tail_mode = state['native_tail']
        self.check_plan_seal()

    def decide(self, net, branch, native_skip, original, probe, delta_x, delta_y, threshold):
        fixed_skip = super().decide(net, branch, native_skip, original, probe, delta_x, delta_y, threshold)
        row = self.pending
        if not self.native_tail or row['call'] not in TAIL_CALLS:
            return fixed_skip
        # The registered real mask has C/C at these calls. Independently guard
        # selected native reuse as well, so a future fixture cannot evade age.
        if native_skip:
            if (len(self.history[branch]) < 2 or len(net.residual_window[branch]) < 2
                    or len(net.probe_residual_window[branch]) < 2 or net.residual_cache[branch] is None):
                raise ValueError('Native tail lacks own-CFG true-full history')
            age = row['solver_step'] - self.history[branch][-1]
            if not 1 <= age <= self.plan.maximum_age_solver_steps:
                raise ValueError('Native tail current source age infeasible')
            row['age_solver_steps'] = age
        action = 'C' if native_skip else 'D'
        row.update(requested=action, selected_skip=bool(native_skip),
            native_tail_response=True, fixed_counterfactual_action=row['planned_action'],
            actual_native_override=False, tail_native_proposal_disagreement=False,
            tail_response_changes_fixed_action=action != row['planned_action'],
            tail_response_policy=TAIL_POLICY)
        return bool(native_skip)

    def finish(self, net, branch, skipped):
        self.check_plan_seal()
        row = self.pending
        if not self.native_tail or row is None or row['call'] not in TAIL_CALLS:
            return super().finish(net, branch, skipped)
        if (not row['paid_probe'] or row.get('native_tail_response') is not True
                or bool(skipped) != row['native_skip'] or row['selected_skip'] != bool(skipped)):
            raise ValueError('Native tail must execute its paid own-state native proposal')
        # Retain the original history/reset observer; bypass only the fixed
        # action equality that is intentionally released for these two calls.
        plan = self.plan
        self.plan = None
        try:
            OneActionRouter.finish(self, net, branch, skipped)
        finally:
            self.plan = plan

    def completed_report(self, prefix_calls):
        self.check_plan_seal()
        if not self.native_tail:
            return super().completed_report(prefix_calls)
        if (type(self.plan) is not FixedMaskPlan or prefix_calls != 44
                or self.calls != 72 or self.pending is not None or len(self.events) != 72):
            raise ValueError('Native-tail complete coverage differs')
        actual = tuple(e['actual_action'] for e in self.events)
        fixed = self.plan.action_mask()
        if actual[:68] != fixed[:68] or actual[70:] != ('D', 'D'):
            raise ValueError('Native response changed an action outside69/70')
        tail = self.events[68:70]
        if (any(e.get('native_tail_response') is not True or not e['paid_probe']
                or e['actual_action'] != ('C' if e['native_skip'] else 'D') for e in tail)
                or self.events[69]['native_cycle_reset'] is not True):
            raise ValueError('Native response or original reset missing')
        return {'plan': asdict(self.plan), 'parent_mask_sha256': mask_sha256(self.plan.parent_mask),
            'actual_mask_sha256': mask_sha256(actual), 'fixed_mask_sha256': mask_sha256(fixed),
            'actual_actions': list(actual), 'fixed_actions': list(fixed),
            'suffix_events': copy.deepcopy(self.events[prefix_calls:]),
            'per_CFG_full_counts': list(cfg_full_counts(actual)), 'quota_matched_per_CFG': False,
            'observed_quota_equal_to_fixed': cfg_full_counts(actual) == cfg_full_counts(fixed),
            'planned_action_changes': len(self.plan.swap_calls),
            'tail_action_changes': [e['call'] for e in tail if e['tail_response_changes_fixed_action']],
            'remaining_policy': TAIL_POLICY, 'responsive_calls_only': list(TAIL_CALLS),
            'states_evolve_independently': True, 'current_truth_used_for_decision': False,
            'equal_runtime': False, 'online_policy': False, 'single_step_RV_label': False,
            'GPU_method_result': False}


class NativeTailSuffixControl(FixedMaskSuffixControlV2):
    def run_mode(self, label, plan, native_tail):
        if type(plan) is not FixedMaskPlan or type(native_tail) is not bool or self.completed != 22:
            raise ValueError('Native-tail immutable step22 plan/mode required')
        plan.validate()
        return self._execute_suffix(label,
            before=lambda: self.router.arm_mode(plan, native_tail),
            after=lambda: {'action_report': self.router.completed_report(44)},
            metadata={'current_action_intervention': True, 'counterfactual_label': False,
                'native_tail': native_tail, 'protocol': 'REGISTERED_SWAP_NATIVE_TAIL_RESPONSE'},
            status='NATIVE_TAIL_SUFFIX_COMPLETE_INTERFACE_NOT_METHOD_RESULT')
