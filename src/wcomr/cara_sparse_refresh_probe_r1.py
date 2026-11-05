"""Opt-in sparse-refresh probe; original F19 contracts remain the default."""
from types import MethodType

from .cara_f19_speed190_sampling_r1 import SpeedOwner, SpeedReadout


class SparseReadout(SpeedReadout):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.sync_residual=True
        self.residual_delta=None
        self.cache_birth_steps=[None,None]

    def delta_age_allowed(self,step):
        return self.delta_step is not None and 1<=step-self.delta_step<=6

    def remember_dd(self,actual,step):
        super().remember_dd(actual,step)
        self.residual_delta=(self.net.residual_cache[0]-self.net.residual_cache[1]).detach()
        self.cache_birth_steps=[step,step]

    def partial_result(self,actual,step):
        self.cache_birth_steps[0]=step
        if self.sync_residual:
            self.net.residual_cache[1]=self.net.residual_cache[0]-self.residual_delta
            self.cache_birth_steps[1]=step
        return super().partial_result(actual,step)

    def end(self,actual,action):
        result=super().end(actual,action)
        self.history[-1].update(cache_birth_steps=list(self.cache_birth_steps),
            residual_sync=self.sync_residual and self.completed in self.partial_updates)
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
