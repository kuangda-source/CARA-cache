"""One current CFG step: OFF, D46, or D45+D46, then native adaptation.

Reuse the pinned original one-action forward and its legal-history checks;
do not modify the archived one-action implementation or model algorithm.
"""
from dataclasses import asdict,dataclass
import copy

from .rv0_actions import OneAction,OneActionRouter,OneActionSuffixControl


@dataclass(frozen=True)
class StepCFGPlan:
    mode:str
    solver_step:int
    maximum_age_solver_steps:int

    @property
    def full_calls(self):
        return {'OFF':(),'SINGLE':(46,),'PAIRED':(45,46)}[self.mode]

    def validate(self):
        if (self.mode not in ('OFF','SINGLE','PAIRED') or type(self.solver_step) is not int
                or self.solver_step!=23 or type(self.maximum_age_solver_steps) is not int
                or self.maximum_age_solver_steps!=32):
            raise ValueError('Registered immediate step23 CFG plan differs')
        for call in self.full_calls:OneAction('D',call,(call-1)%2,32).validate()


class StepCFGRouter(OneActionRouter):
    def arm(self,plan):
        if type(plan) is not StepCFGPlan:raise ValueError('Immutable step-CFG plan required')
        plan.validate()
        if self.pending or self.plan is not None or self.calls!=44 or self.epoch!=0:
            raise ValueError('Step-CFG plan must start from complete step22/call44')
        self.plan,self.consumed=plan,0

    def current_single_plan(self):
        if self.plan is None or self.calls not in self.plan.full_calls:return None
        return OneAction('D',self.calls,(self.calls-1)%2,self.plan.maximum_age_solver_steps)

    def decide(self,*args):
        plan,total=self.plan,self.consumed
        current=self.current_single_plan();increment=0
        self.plan,self.consumed=current,0
        try:
            result=super().decide(*args);increment=self.consumed
            return result
        finally:
            self.plan,self.consumed=plan,total+increment

    def finish(self,*args):
        plan=self.plan;self.plan=self.current_single_plan()
        try:return super().finish(*args)
        finally:self.plan=plan

    def completed_report(self,prefix_calls):
        if (type(self.plan) is not StepCFGPlan or prefix_calls!=44 or self.calls!=72 or self.pending
                or self.consumed!=len(self.plan.full_calls)):
            raise ValueError('Registered step-CFG decisions or complete suffix missing')
        events=copy.deepcopy(self.events[prefix_calls:])
        if [e['call'] for e in events]!=list(range(45,73)):
            raise ValueError('Complete step-CFG call grid missing')
        requested=[e['call'] for e in events if e['requested'] is not None]
        if requested!=list(self.plan.full_calls):raise ValueError('Step-CFG current action scope leaked')
        return {'plan':asdict(self.plan),'requested_full_calls':requested,'suffix_events':events,
            'decision_interventions':self.consumed,'remaining_policy':'ORIGINAL_WC_ADAPTIVE',
            'same_remaining_policy_function_not_same_future_action_mask':True,
            'budget_matched':False,'current_truth_used_for_decision':False,'RV_label':False}


class StepCFGSuffixControl(OneActionSuffixControl):
    def run_plan(self,label,plan):
        if type(plan) is not StepCFGPlan:raise ValueError('Immutable step-CFG plan required')
        plan.validate()
        return self._execute_suffix(label,before=lambda:self.router.arm(plan),
            after=lambda:{'action_report':self.router.completed_report(2*self.completed)},
            metadata={'current_action_intervention':bool(plan.full_calls),'counterfactual_label':False,
                'protocol':'CURRENT_CFG_STEP_SHARED_ADAPTIVE_SUFFIX_NOT_SINGLE_ACTION_OR_BUDGET_MATCHED'},
            status='CURRENT_CFG_STEP_SUFFIX_COMPLETE_NOT_RV_LABEL')
