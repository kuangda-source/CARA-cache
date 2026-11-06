"""Frozen per-CFG quota router for the registered four position-exchange cells."""
import copy
import math
from dataclasses import asdict
import torch
from .rv0_actions import OneActionRouter, OneActionSuffixControl
from .rv0_cfg_budget_plan import CFGBudgetPlan, full_counts, mask_sha256

POLICY='OFFLINE_FIXED_PARENT_MASK_WITH_REGISTERED_CFG_POSITION_EXCHANGES'


class CFGBudgetRouter(OneActionRouter):
    def __init__(self,context,registered_parent_mask):
        super().__init__(context)
        self.registered_parent_mask=tuple(registered_parent_mask)
        CFGBudgetPlan('BASE',self.registered_parent_mask).validate()
        self._armed_plan_value=None

    def check_context(self,net):
        super().check_context(net)
        if int(net.worldcache_num_steps*net.worldcache_ret_ratio)!=14:
            raise ValueError('Registered 14-call initialization changed')

    def arm(self,plan):
        if type(plan) is not CFGBudgetPlan:raise ValueError('Immutable registered CFG position plan required')
        plan.validate()
        if (plan.parent_mask!=self.registered_parent_mask or self.pending or self.plan is not None
                or self.calls!=44 or self.epoch!=0 or len(self.events)!=44
                or tuple(e['actual_action'] for e in self.events)!=plan.parent_mask[:44]):
            raise ValueError('Registered shared parent prefix/context differs')
        self.plan,self.consumed=plan,0;self._armed_plan_value=copy.deepcopy(plan)

    def restore(self,state):
        super().restore(state);self._armed_plan_value=copy.deepcopy(self.plan)

    def check_plan_seal(self):
        if self.plan is not None and self.plan!=self._armed_plan_value:
            raise ValueError('Armed CFG position plan changed; no quota repair permitted')

    def decide(self,net,branch,native_skip,original,probe,delta_x,delta_y,threshold):
        self.check_context(net);row=self.pending
        if row is None or branch!=row['cfg_slot']:raise ValueError('Missing paid current CFG decision')
        row.update(paid_probe=True,native_skip=bool(native_skip),selected_skip=bool(native_skip))
        if self.plan is None:return native_skip
        self.check_plan_seal();expected=self.plan.action_mask()[row['call']-1]
        if net.cnt<14 and (expected!='D' or bool(native_skip)):
            raise ValueError('Original initialization/reset must remain full')
        swapped=tuple(x for pair in self.plan.swaps for x in pair)
        if expected=='C' or row['call'] in swapped:
            if (len(self.history[branch])<2 or len(net.residual_window[branch])<2
                    or len(net.probe_residual_window[branch])<2 or net.residual_cache[branch] is None):
                raise ValueError('Position decision lacks own-CFG true-full cache history')
            age=row['solver_step']-self.history[branch][-1]
            if not 1<=age<=32:raise ValueError('Registered cache source age infeasible')
            row['age_solver_steps']=age
        for tensor in (original,probe,net.residual_cache[branch]):
            if tensor is not None and not bool(torch.isfinite(tensor).all()):raise ValueError('Nonfinite fixed-budget decision state')
        scalars=[float(v) for v in (delta_x,delta_y,threshold,net.accumulated_rel_l1_distance[branch])]
        if any(not math.isfinite(v) for v in scalars):raise ValueError('Nonfinite paid fixed-budget signal')
        override=(expected=='C')!=bool(native_skip)
        row.update(requested=expected,planned_action=expected,selected_skip=expected=='C',actual_native_override=override,
            tail_native_proposal_disagreement=bool(row['call'] in (69,70) and override),
            protected_executed_action=row['call']>=69,paid_input_drift=scalars[0],paid_probe_drift=scalars[1],
            dynamic_threshold=scalars[2],accumulator_before_action=scalars[3])
        self.consumed+=1
        return row['selected_skip']

    def finish(self,net,branch,skipped):
        self.check_plan_seal()
        if self.plan is not None:
            row=self.pending;expected=self.plan.action_mask()[row['call']-1]
            if ('C' if skipped else 'D')!=expected:raise ValueError('Executed action differs; no count-changing fallback')
            swapped=tuple(x for pair in self.plan.swaps for x in pair)
            if (expected=='C' or row['call'] in swapped) and not row['paid_probe']:
                raise ValueError('Position decision lacks paid own-state probe')
            row.update(planned_action=expected,protected_executed_action=row['call']>=69)
        plan=self.plan;self.plan=None
        try:super().finish(net,branch,skipped)
        finally:self.plan=plan

    def completed_report(self,prefix_calls):
        self.check_plan_seal()
        if prefix_calls!=44 or self.calls!=72 or self.pending or len(self.events)!=72:
            raise ValueError('Complete registered suffix coverage required')
        actual=tuple(e['actual_action'] for e in self.events)
        expected=self.registered_parent_mask if self.plan is None else self.plan.action_mask()
        if actual!=expected or full_counts(actual)!=(18,17):
            raise ValueError('Frozen parent/full per-CFG quotas changed')
        return {'plan':None if self.plan is None else asdict(self.plan),
            'parent_mask_sha256':mask_sha256(self.registered_parent_mask),'actual_mask_sha256':mask_sha256(actual),
            'actual_actions':list(actual),'per_CFG_full_counts':[18,17],'quota_matched_per_CFG':True,
            'suffix_events':copy.deepcopy(self.events[44:]),'planned_action_changes':0 if self.plan is None else 2*len(self.plan.swaps),
            'paid_mask_decisions':self.consumed,'remaining_policy':'ORIGINAL_WC_ADAPTIVE_REFERENCE' if self.plan is None else POLICY,
            'tail_native_proposal_disagreements':[e['call'] for e in self.events if e.get('tail_native_proposal_disagreement')],
            'native_tail_proposal_preservation_required':False,'original_initialization_reset_and_full_tail_preserved':True,
            'budget_matched':True,'states_evolve_independently':True,'current_truth_used_for_decision':False,'RV_label':False}


class CFGBudgetSuffixControl(OneActionSuffixControl):
    def run_plan(self,label,plan):
        if plan is not None:
            if type(plan) is not CFGBudgetPlan:raise ValueError('Immutable registered position plan required')
            plan.validate()
        if self.completed!=22:raise ValueError('Registered complete step22 fork required')
        return self._execute_suffix(label,before=(lambda:self.router.arm(plan)) if plan is not None else (lambda:None),
            after=lambda:{'action_report':self.router.completed_report(44)},
            metadata={'current_action_intervention':bool(plan and plan.swaps),'counterfactual_label':False,
                'protocol':'FIXED_PER_CFG_QUOTA_FOUR_POSITION_CELLS_NOT_SINGLE_ACTION_RV'},
            status='CFG_BUDGET_SUFFIX_COMPLETE_INTERFACE_NOT_METHOD_RESULT')
