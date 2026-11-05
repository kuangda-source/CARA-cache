"""Opt-in sparse-refresh probe; original F19 contracts remain the default."""
import math
import statistics
from types import MethodType

from .calibration import Anchor
from .cara_f19_speed190_sampling_r1 import SpeedOwner, SpeedReadout


def s1_gate(*,D_seconds,P_seconds,C_next_MSE,sync_C_next_MSE,drift_D_to_next,drift_P_to_next):
    """Confirmed in-job S1 decision, using amplitude kappa from next-step C.

    Both C errors use the same next-step state/teacher; the no-P control restores
    the latest-DD caches. Drift is the frozen cumulative-drift coordinate.
    """
    D=statistics.median(D_seconds);P=statistics.median(P_seconds)
    values=(D,P,C_next_MSE,sync_C_next_MSE,drift_D_to_next,drift_P_to_next)
    if not all(math.isfinite(v) for v in values) or not (
            D>0 and P>=0 and C_next_MSE>0 and sync_C_next_MSE>=0 and 0<=drift_P_to_next<drift_D_to_next):
        raise ValueError('S1 requires finite timing, positive C error and ordered D/P drift')
    lam=drift_P_to_next/drift_D_to_next
    kappa=(math.sqrt(sync_C_next_MSE/C_next_MSE)-lam)/(1-lam)
    ratio=P/D
    return dict(cost_ratio=ratio,kappa=kappa,lambda_drift=lam,
        timing_passed=ratio<=.5,kappa_passed=kappa<.45,gate_passed=ratio<=.5 and kappa<.45)


class SparseReadout(SpeedReadout):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.sync_residual=True
        self.residual_delta=None
        self.probe_delta=None
        self.synthetic_uncond_anchor_step=None
        self.true_uncond_anchor=None
        self.cache_birth_steps=[None,None]

    def delta_age_allowed(self,step):
        return self.delta_step is not None and 1<=step-self.delta_step<=6

    def remember_dd(self,actual,step):
        super().remember_dd(actual,step)
        self.residual_delta=(self.net.residual_cache[0]-self.net.residual_cache[1]).detach()
        self.probe_delta=(self.net.probe_residual_cache[0]-self.net.probe_residual_cache[1]).detach()
        self.synthetic_uncond_anchor_step=None
        self.true_uncond_anchor=self.calibrators[1].anchors[-1]
        self.cache_birth_steps=[step,step]

    def hidden(self,net,skipped,branch,*args):
        if not skipped and branch==1 and self.synthetic_uncond_anchor_step is not None:
            # The next real D regresses against the previous real D, not P.
            self.calibrators[1].anchors=[self.true_uncond_anchor]
        return super().hidden(net,skipped,branch,*args)

    def partial_result(self,actual,step):
        self.cache_birth_steps[0]=step
        if self.sync_residual:
            self.net.residual_cache[1]=self.net.residual_cache[0]-self.residual_delta
            self.cache_birth_steps[1]=step
            # Confirmed A-state sync. This is an approximate anchor, not an
            # observed uncond D: do not train observe_full's regression on it.
            anchor=Anchor(step,(self.net.probe_residual_cache[0]-self.probe_delta).detach(),
                self.net.residual_cache[1].detach())
            calibrator=self.calibrators[1]
            calibrator.anchors=(calibrator.anchors+[anchor])[-2:]
            self.synthetic_uncond_anchor_step=step
        return super().partial_result(actual,step)

    def end(self,actual,action):
        result=super().end(actual,action)
        self.history[-1].update(cache_birth_steps=list(self.cache_birth_steps),
            residual_sync=self.sync_residual and self.completed in self.partial_updates,
            calibrator_anchor_steps=[c.anchors[-1].step for c in self.calibrators],
            synthetic_uncond_anchor_step=self.synthetic_uncond_anchor_step)
        return result


class SparseOwner(SpeedOwner):
    readout_class=SparseReadout

    def __init__(self,*args,sync_residual=True,**kwargs):
        super().__init__(*args,**kwargs)
        if not self.light_C:raise ValueError('Sparse probe requires residual-hold light C')
        self.readout.sync_residual=sync_residual

    def validate_partial(self):
        # Only the three preregistered probe masks lift the historical F19 freeze.
        if self.partial_updates not in ((29,32),(22,24),(29,)):
            raise ValueError('Unregistered sparse-refresh probe positions')
        last=None
        for step,action in enumerate(self.policy['actions'],1):
            if step in self.partial_updates:
                if action!='D' or step in self.profile.protected_dense or last is None or not 1<=step-last<=6:
                    raise ValueError('P requires a causal true DD within six steps')
            elif action=='D':last=step

    def close(self):
        self.readout.residual_delta=None
        self.readout.probe_delta=None
        self.readout.true_uncond_anchor=None
        super().close()

    def pair(self,*args,**kwargs):
        result=super().pair(*args,**kwargs)
        if self.history[-1]['step'] in self.partial_updates:self.history[-1]['actual']='P'
        return result


class LayerReuse:
    """S1-only block forwards: first k execute, remaining layers reuse latest D.

    Attach before the parent trajectory. Call begin once per pair; only D writes
    layer anchors. P operates on a disposable local state and never emits video.
    """
    def __init__(self,net):
        self.net=net
        self.originals=[block.forward for block in net.blocks]
        self.residuals=[[None]*len(net.blocks) for _ in (0,1)]
        self.birth_steps=[[None]*len(net.blocks) for _ in (0,1)]
        self.action='C';self.step=None;self.k=None
        for index,block in enumerate(net.blocks):
            def forward(module,value,_index=index,**kwargs):
                branch=int(self.net.cnt)%2
                if self.action=='P' and _index>=self.k:
                    return value+self.residuals[branch][_index]
                result=self.originals[_index](value,**kwargs)
                if self.action=='D':
                    self.residuals[branch][_index]=(result-value).detach()
                    self.birth_steps[branch][_index]=self.step
                return result
            block.forward=MethodType(forward,block)

    def begin(self,step,action,*,k=None):
        if action not in ('D','C','P'):raise ValueError('S1 layer action must be D/C/P')
        if action=='P':
            if k not in (14,20) or k>len(self.originals):raise ValueError('S1 uses k=14 or k=20')
            if any(v is None for branch in self.residuals for v in branch[k:]):
                raise ValueError('P_k requires latest-D layer residuals')
        self.step,self.action,self.k=step,action,k

    def close(self):
        for block,forward in zip(self.net.blocks,self.originals):block.forward=forward
        self.residuals.clear()
