"""Restored, same-origin two-call CFG teachers; no endpoint rollouts or policy fitting."""
import copy
from dataclasses import asdict, dataclass
import inspect
import time
import torch

from .mid_coverage import tree_digest
from .rv0_actions import OneAction, OneActionRouter, OneActionSuffixControl
from .rv0_cfg_budget_evaluation import solver_configuration

MODES = ('CC', 'DC', 'CD', 'DD')


@dataclass(frozen=True)
class TeacherPairPlan:
    mode: str
    solver_step: int

    def validate(self):
        if self.mode not in MODES or type(self.solver_step) is not int or self.solver_step not in (23,24):
            raise ValueError('Registered complete teacher pair at step23/24 required')


class TeacherPairRouter(OneActionRouter):
    def arm(self, plan):
        if type(plan) is not TeacherPairPlan:
            raise ValueError('Immutable paired teacher plan required')
        plan.validate()
        if self.pending or self.plan is not None or self.calls != 2*(plan.solver_step-1) or self.epoch:
            raise ValueError('Teacher pair must begin at its complete original CFG boundary')
        self.plan, self.consumed = plan, 0

    def single_plan(self):
        if self.plan is None:
            return None
        slot = self.calls - 2*(self.plan.solver_step-1) - 1
        if slot not in (0,1):
            raise ValueError('Paired teacher action leaked outside two current calls')
        return OneAction(self.plan.mode[slot], self.calls, slot, 32)

    def decide(self, *args):
        plan, total = self.plan, self.consumed
        single = self.single_plan()
        self.plan, self.consumed = single, 0
        try:
            result = super().decide(*args)
            increment = self.consumed
            return result
        finally:
            self.plan, self.consumed = plan, total + (locals().get('increment',0))

    def finish(self, *args):
        plan = self.plan
        self.plan = self.single_plan()
        try:
            return super().finish(*args)
        finally:
            self.plan = plan

    def pair_report(self):
        if not self.plan or self.pending or self.consumed != 2 or self.calls != 2*self.plan.solver_step:
            raise ValueError('Complete two-call teacher actions missing')
        events = copy.deepcopy(self.events[-2:])
        if ([e['actual_action'] for e in events] != list(self.plan.mode)
                or any(not e['paid_probe'] or e['current_deep_truth_used'] for e in events)):
            raise ValueError('Teacher actions did not execute with legal paid probes')
        return {'plan': asdict(self.plan), 'events': events,
                'source': 'SAME_ORIGIN_LOCAL_TEACHER_NOT_ENDPOINT_NOT_RV',
                'current_truth_used_for_decision': False}

    def clear_pair(self):
        self.pair_report()
        self.plan, self.consumed = None, 0


class GuidedTeacherFork(OneActionSuffixControl):
    """Capture uses the existing complete-state/condition restoration implementation."""
    def __init__(self, *args, capture, writer, save, **kwargs):
        super().__init__(*args, **kwargs)
        if self.completed not in (22,23):
            raise ValueError('Only registered S22 and S23 origins permitted')
        cells = inspect.getclosurevars(self.velocity_fn).nonlocals
        if cells['guidance'] != 7:
            raise ValueError('Registered Cosmos guidance7 required')
        self.capture, self.writer, self.save = capture, writer, save

    @torch.no_grad()
    def measure(self, label, mode, *, advance=None):
        if mode not in MODES or any(r['label']==label for r in self.records):
            raise ValueError('Unique complete registered pair required')
        record = {'label':label, 'mode':mode, 'status':'STARTED', 'origin_completed_updates':self.completed,
                  'origin_components':self.snapshot.components(), 'origin_fingerprint':self.parent_fingerprint,
                  'origin_solver_configuration':solver_configuration(self.scheduler),
                  'origin_own_history':copy.deepcopy(self.router.history),
                  'inputs':[], 'outputs':[], 'deep':[], 'banks':[], 'solver_outputs':[],
                  'post_denoise_branch_sha256':[], 'denoise_arguments':[],
                  'formal_RV_label':False, 'endpoint_label':False}
        self.records.append(record); self.save()
        started = time.perf_counter()
        try:
            latent = self.restore_parent()
            self.capture['record'] = record; self.capture['branches'] = []
            self.router.arm(TeacherPairPlan(mode,self.completed+1))
            timestep = torch.stack([self.scheduler.timesteps[self.completed]]).unsqueeze(0)
            result = self.velocity_fn(self.noise, latent, timestep)
            self.check_identity()
            if (self.scheduler._step_index != self.completed
                    or solver_configuration(self.scheduler) != record['origin_solver_configuration']):
                raise ValueError('Velocity-only teacher changed original solver state/configuration')
            branches = self.capture['branches']
            if (len(branches)!=2 or any(not isinstance(v,torch.Tensor) or v.dtype!=torch.float32
                    or v.ndim!=5 or v.shape!=result.shape or not bool(torch.isfinite(v).all()) for v in branches)
                    or result.dtype!=torch.float32 or not bool(torch.isfinite(result).all())):
                raise ValueError('Actual complete post-denoise FP32 pair missing/nonfinite')
            record['action_report'] = self.router.pair_report()
            record['pair_end_components'] = self.snapshot.components()
            record['pair_end_fingerprint'] = self.snapshot.fingerprint()
            record['pair_end_solver_configuration'] = solver_configuration(self.scheduler)
            record['actual_guided_sha256'] = tree_digest(result)
            record['artifact'] = self.writer(label, {'conditional':branches[0], 'unconditional':branches[1],
                'guided':result.detach().cpu().clone()})
            self.router.clear_pair()
            if advance is not None:
                if self.completed != 22:
                    raise ValueError('Only S22 first repetitions generate S23 origins')
                # Reuse this exact measured velocity in the unchanged official one-step loop.
                input_witness = tree_digest((self.noise,latent,timestep))
                def saved_velocity(noise,x,t):
                    if tree_digest((noise,x,t)) != input_witness:
                        raise ValueError('Saved velocity reused for a different solver input')
                    return result
                child = self.suffix(self.model,self.noise,latent,saved_velocity,self.generator,
                    self.scheduler.timesteps[self.completed:self.completed+1])
                if self.scheduler._step_index!=23 or self.router.calls!=46 or self.net.cnt!=46:
                    raise ValueError('Measured velocity did not advance exactly one original update')
                record['child_latent_sha256'] = tree_digest(child)
                record['solver_step_reused_measured_velocity_without_net_call'] = True
                advance(child)
            record['status'] = 'COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT'
            return record
        except BaseException as error:
            record.update(status='TECH_BLOCKED_RETAINED_COMPLETE_SCOPE',error_type=type(error).__name__,error=str(error))
            raise
        finally:
            self.capture['record'] = None; self.capture['branches'] = []
            self.restore_parent()
            record['parent_restored'] = True
            record['wall_seconds'] = time.perf_counter()-started
            self.save()


def verify_origin(origin):
    rows = origin['pairs']
    if len(rows)!=8 or [r['label'] for r in rows]!=[n+'_'+k for n in MODES for k in ('first','second')]:
        raise ValueError('Complete four-action/two-repeat origin required')
    signature_keys = ('origin_components','origin_fingerprint','origin_solver_configuration','origin_own_history',
        'inputs','outputs','deep','banks','post_denoise_branch_sha256','denoise_arguments','action_report',
        'pair_end_components','pair_end_fingerprint','pair_end_solver_configuration','actual_guided_sha256')
    for mode in MODES:
        a,b = [r for r in rows if r['mode']==mode]
        if (a['status']!='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT'
                or b['status']!='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT'
                or not a['parent_restored'] or not b['parent_restored']
                or any(a[k]!=b[k] for k in signature_keys)):
            raise ValueError('Teacher repeat state/output/branch evidence differs')
        if a['status']!='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT':
            raise ValueError('Incomplete local teacher row retained')
        if any(len(a[k])!=2 for k in ('inputs','outputs','deep','banks','post_denoise_branch_sha256','denoise_arguments')):
            raise ValueError('Missing one current CFG observation')
        if a['action_report']['plan']['mode']!=mode:
            raise ValueError('Wrong teacher cell action')
    reference = rows[0]
    if any(r['origin_components']!=reference['origin_components'] or r['inputs']!=reference['inputs'] for r in rows):
        raise ValueError('Same-origin latent/condition inputs differ')
    return {'strict_repeat_groups':4, 'same_origin_inputs_all_cells':True,
            'complete_pair_rows':8, 'endpoint_labels':0}
