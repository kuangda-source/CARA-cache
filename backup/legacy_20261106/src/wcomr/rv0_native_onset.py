"""Sealed 65/67/69 own-state response windows after one registered joint swap.

The fixed-mask implementation and original history/reset observer are reused.
No current deep truth, quota repair, or modification of completed tail runs.
"""
import copy
from dataclasses import asdict

from .rv0_actions import OneActionRouter
from .rv0_fixed_mask_v2 import FixedMaskRouterV2, FixedMaskSuffixControlV2
from .rv0_fixed_plan import FixedMaskPlan, cfg_full_counts, mask_sha256
from .rv0_native_tail_causal import PlacementSuffixControl

CALLS_BY_MODE = {'FIXED61': (), 'LATE69': (69, 70),
                 'RESP65': tuple(range(65, 71)), 'RESP67': tuple(range(67, 71))}


def response_policy(calls):
    if calls not in CALLS_BY_MODE.values() or not calls:
        raise ValueError('Registered nonempty immutable response window required')
    if calls == (69, 70):
        return 'FIXED_REGISTERED_SWAP_THROUGH68_NATIVE_OWN_STATE69_70_ORIGINAL_RESET71_72'
    return ('FIXED_REGISTERED_SWAP_THROUGH'+str(calls[0]-1)+'_NATIVE_OWN_STATE'
            +str(calls[0])+'_70_ORIGINAL_RESET71_72')


class NativeResponseRouter(FixedMaskRouterV2):
    def __init__(self, context):
        super().__init__(context)
        self.responsive_calls = self._armed_response_calls = ()

    def arm_mode(self, plan, calls):
        if type(calls) is not tuple or calls not in CALLS_BY_MODE.values() or self.responsive_calls:
            raise ValueError('Registered immutable 65/67/69 response window required')
        super().arm(plan)
        self.responsive_calls = self._armed_response_calls = calls

    def check_plan_seal(self):
        super().check_plan_seal()
        if (self.responsive_calls != self._armed_response_calls
                or self.responsive_calls and self.plan is None):
            raise ValueError('Armed response window changed')

    def snapshot(self):
        self.check_plan_seal()
        return {**super().snapshot(), 'responsive_calls': self.responsive_calls,
                'armed_response_calls': self._armed_response_calls}

    def restore(self, state):
        calls = state['responsive_calls']
        if (type(calls) is not tuple or calls not in CALLS_BY_MODE.values()
                or calls != state['armed_response_calls']):
            raise ValueError('Stored immutable response window seal differs')
        super().restore(state)
        self.responsive_calls = self._armed_response_calls = calls
        self.check_plan_seal()

    def decide(self, net, branch, native_skip, original, probe, delta_x, delta_y, threshold):
        fixed_skip = super().decide(net, branch, native_skip, original, probe, delta_x, delta_y, threshold)
        row = self.pending
        if row['call'] not in self.responsive_calls:
            return fixed_skip
        if native_skip:
            if (len(self.history[branch]) < 2 or len(net.residual_window[branch]) < 2
                    or len(net.probe_residual_window[branch]) < 2 or net.residual_cache[branch] is None):
                raise ValueError('Native response lacks own-CFG true-full history')
            age = row['solver_step']-self.history[branch][-1]
            if not 1 <= age <= self.plan.maximum_age_solver_steps:
                raise ValueError('Native response current source age infeasible')
            row['age_solver_steps'] = age
        action = 'C' if native_skip else 'D'
        row.update(requested=action, selected_skip=bool(native_skip), native_response=True,
            fixed_counterfactual_action=row['planned_action'], actual_native_override=False,
            tail_native_proposal_disagreement=False,
            response_changes_fixed_action=action != row['planned_action'],
            response_policy=response_policy(self.responsive_calls))
        return bool(native_skip)

    def finish(self, net, branch, skipped):
        self.check_plan_seal()
        row = self.pending
        if row is None or row['call'] not in self.responsive_calls:
            return super().finish(net, branch, skipped)
        if (not row['paid_probe'] or row.get('native_response') is not True
                or bool(skipped) != row['native_skip'] or row['selected_skip'] != bool(skipped)):
            raise ValueError('Native response must execute its paid own-state proposal')
        plan = self.plan
        self.plan = None
        try:
            OneActionRouter.finish(self, net, branch, skipped)
        finally:
            self.plan = plan

    def completed_report(self, prefix_calls):
        self.check_plan_seal()
        if not self.responsive_calls:
            return super().completed_report(prefix_calls)
        if (type(self.plan) is not FixedMaskPlan or prefix_calls != 44
                or self.calls != 72 or self.pending is not None or len(self.events) != 72):
            raise ValueError('Complete native response coverage differs')
        actual = tuple(e['actual_action'] for e in self.events)
        fixed = self.plan.action_mask()
        start = self.responsive_calls[0]
        if actual[:start-1] != fixed[:start-1] or actual[70:] != ('D', 'D'):
            raise ValueError('Native response changed an action outside its registered window')
        window = [self.events[n-1] for n in self.responsive_calls]
        if (any(e.get('native_response') is not True or not e['paid_probe']
                or e['actual_action'] != ('C' if e['native_skip'] else 'D') for e in window)
                or self.events[69]['native_cycle_reset'] is not True):
            raise ValueError('Actual native response or original reset missing')
        return {'plan': asdict(self.plan), 'parent_mask_sha256': mask_sha256(self.plan.parent_mask),
            'actual_mask_sha256': mask_sha256(actual), 'fixed_mask_sha256': mask_sha256(fixed),
            'actual_actions': list(actual), 'fixed_actions': list(fixed),
            'suffix_events': copy.deepcopy(self.events[prefix_calls:]),
            'per_CFG_full_counts': list(cfg_full_counts(actual)), 'quota_matched_per_CFG': False,
            'observed_quota_equal_to_fixed': cfg_full_counts(actual) == cfg_full_counts(fixed),
            'planned_action_changes': len(self.plan.swap_calls),
            'response_action_changes': [e['call'] for e in window if e['response_changes_fixed_action']],
            'remaining_policy': response_policy(self.responsive_calls),
            'responsive_calls_only': list(self.responsive_calls), 'states_evolve_independently': True,
            'current_truth_used_for_decision': False, 'equal_runtime': False,
            'online_policy': False, 'single_step_RV_label': False, 'GPU_method_result': False}


class NativeResponseSuffixControl(FixedMaskSuffixControlV2):
    # Reuse the exact original adaptive OFF continuation and restoration path.
    run_off = PlacementSuffixControl.run_off

    def run_mode(self, label, plan, calls):
        if type(plan) is not FixedMaskPlan or self.completed != 22:
            raise ValueError('Immutable registered step22 response plan required')
        if type(calls) is not tuple or calls not in CALLS_BY_MODE.values():
            raise ValueError('Registered immutable response window required')
        plan.validate()
        return self._execute_suffix(label,
            before=lambda: self.router.arm_mode(plan, calls),
            after=lambda: {'action_report': self.router.completed_report(44)},
            metadata={'current_action_intervention': True, 'counterfactual_label': False,
                'responsive_calls': list(calls), 'protocol': 'REGISTERED_SWAP_NATIVE_RESPONSE_ONSET'},
            status='NATIVE_RESPONSE_ONSET_SUFFIX_COMPLETE_INTERFACE_NOT_METHOD_RESULT')
