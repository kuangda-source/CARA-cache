"""Five complete actions, one warmup and three alternating formal rounds.

Keep the accepted H1 physical/owned restore and ordinary parent continuation.
The quiet mode mutes only the owner's declared Linear/head audit observers;
MLP forwards, masks, source maintenance and readout hooks stay installed.
"""
import copy
from contextlib import contextmanager
import functools
import inspect
from textwrap import dedent
import time

import torch

from . import p_acr_h1_diagnostic_owner_r1 as parent
from .source_phase_absolute_h1_owner_r1 import SourcePhaseH1Owner
from .p_acr_readout_r1 import ACRReadoutExecutor
from .partial_mlp_deployment_state import plain
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .source_aware_phase_sampling import bind_globals

VERSION='PA_FULL_PAIR_PRICE20_AUDIT_QUIET_ORDER_PARITY_R1'
ORDER=('C','A','D','Pc','Pu')


def trial_plan():
    return tuple((name,rep,'WARMUP' if rep==0 else 'TIMED')
        for rep in range(4) for name in (ORDER if rep%2!=0 or rep==0 else tuple(reversed(ORDER))))


class PAProfile20Owner(parent.PADiagnosticOwner):
    def __init__(self,*a,quiet_observers=False,**kw):
        if type(quiet_observers) is not bool:raise ValueError('Declared audit/quiet price mode required')
        self.quiet_observers=quiet_observers
        super().__init__(*a,**kw)

    def installation(self):
        return super().installation()+(VERSION,self.quiet_observers)

    @contextmanager
    def _observers(self):
        if not self.quiet_observers:
            yield {'pure_observers_suspended':0,'actual_head_count_available':True};return
        dictionaries={}
        for handle in self.hooks:
            hooks=handle.hooks_dict_ref()
            if hooks is None or handle.id not in hooks:raise ValueError('Original audit hook absent')
            callback=hooks[handle.id]
            if (callback.__name__ not in ('observe','observe_head')
                    or 'SamplingOwner.__init__.<locals>' not in callback.__qualname__):
                raise ValueError('Do not mute algorithm or unknown hooks')
            key=id(hooks)
            if key not in dictionaries:dictionaries[key]=(hooks,dict(hooks),set())
            dictionaries[key][2].add(handle.id)
        if len(self.hooks)!=9:raise ValueError('Exact eight Linear and one head observers required')
        forwards=tuple((layer,vars(self.net.blocks[layer].mlp).get('forward')) for layer in (4,10,16,22))
        try:
            for hooks,original,ids in dictionaries.values():
                for identifier in ids:del hooks[identifier]
            yield {'pure_observers_suspended':9,'actual_head_count_available':False}
            for hooks,original,ids in dictionaries.values():
                expected={k:v for k,v in original.items() if k not in ids}
                if list(hooks)!=list(expected) or any(hooks[k] is not v for k,v in expected.items()):
                    raise ValueError('Algorithm/foreign hook changed during quiet quote')
            if forwards!=tuple((layer,vars(self.net.blocks[layer].mlp).get('forward')) for layer in (4,10,16,22)):
                raise ValueError('Quiet quote changed an algorithm MLP forward')
        finally:
            for hooks,original,ids in dictionaries.values():hooks.clear();hooks.update(original)

    def _profile20(self,snapshot,step,noise,latent,timestep,conditions,choose,state,D_sha,work_sha):
        payload={};trials=[]
        cell=state[1]+('_EARLY' if step<25 else '_LATE');gains=self.coefficients['cells'][cell]
        for name,rep,section in trial_plan():
            self.step=step;start_heads=len(self.head_calls);start_linear=len(self.linear_rows)
            preparation_seconds=0.
            if name in ('C','A','D'):
                with self.controller.action(step,name),self._observers() as observers:
                    synchronize();start=time.perf_counter();self.actual_pair_computations+=1
                    value=SourcePhaseH1Owner.pair(self,noise,latent,timestep,conditions,choose)
                    synchronize();elapsed=time.perf_counter()-start
                history=copy.deepcopy(self.history[-1]);key=name
                if history['A_readout']['readout_action']!=name:
                    raise ValueError('Quoted CAD output does not match its semantic action')
                if rep==0:payload[key]=tuple(v.detach().cpu().clone() for v in value)
                elif any(not torch.equal(v.detach().cpu(),w) for v,w in zip(value,payload[key])):
                    raise ValueError('Repeated CAD changed at identical state')
                if name!='D' and tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha:
                    raise ValueError('CAD quote modified true D')
                if name!='D' and tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))!=work_sha:
                    raise ValueError('CAD quote modified working source')
                extra={'actual_action':history['action'],'actual_readout':name}
            else:
                coefficient=gains['Pc_eta' if name=='Pc' else 'Pu_zeta']
                setup_start=time.perf_counter()
                executor=ACRReadoutExecutor(self.model,runtime=self._acr_runtime,wc=self._acr_wc,rf=self._acr_rf,
                    context=self.context,dense=self.deployment.dense,working=self.deployment.working,
                    gamma=self.controller.table_parameters['gamma'],direction=name,coefficient=coefficient,
                    step=step,projection_readonly=self.deployment.core.readonly)
                preparation_seconds=time.perf_counter()-setup_start
                with self._observers() as observers:
                    synchronize();start=time.perf_counter();self.actual_pair_computations+=1
                    value,base_A,one_D=executor.execute(noise,latent,timestep,conditions)
                    synchronize();elapsed=time.perf_counter()-start
                side=0 if name=='Pc' else 1
                if (any(not torch.equal(v.detach().cpu(),w) for v,w in zip(base_A,payload['A']))
                        or not torch.equal(one_D.detach().cpu(),payload['D'][side])):
                    raise ValueError('Quoted asymmetric A/teacher changed at identical state')
                if (tree_digest(plain([vars(c) for c in self.deployment.dense]))!=D_sha
                        or tree_digest((self.deployment.working,self.net.probe_residual_cache,self.net.residual_cache))!=work_sha):
                    raise ValueError('Quoted ACR changed true-D/working source')
                key=name+'_REP'+str(rep);payload[key]=tuple(v.detach().cpu().clone() for v in value)
                if rep and any(not torch.equal(v,w) for v,w in zip(payload[key],payload[name+'_REP0'])):
                    raise ValueError('Repeated ACR changed at identical state')
                if self.past_delta is None:raise ValueError('Strictly-past ordinary DD required')
                payload['FC_STYLE_'+key]=tuple(v.detach().cpu().clone() for v in
                    self.past_delta.readout(one_D,context=self.context,step=step,direction=name))
                extra={'coefficient':coefficient,'actual_dense_branches':1,'paid_prefixes':2,'source_refresh':False}
            heads=len(self.head_calls)-start_heads;linear=len(self.linear_rows)-start_linear
            if self.quiet_observers:
                if heads or linear:raise ValueError('Quiet quote still appended pure audit records')
                heads=None;linear=None
            trials.append({'kind':name,'section':section,'repetition':rep,'full_pair_seconds':elapsed,
                'action_preparation_seconds':preparation_seconds,'charged_action_seconds':elapsed+preparation_seconds,
                'per_action_compiler_preparation_is_charged':True,
                'actual_heads':heads,'actual_Linear_observers':linear,'observers':observers,
                'compiler_installation_outside_timer':True,'snapshot_hash_restore_IO_outside_timer':True,**extra})
            snapshot.restore()
        if len(trials)!=20:raise ValueError('Complete five-action price20 scope required')
        return payload,trials


# Reuse the accepted physical snapshot/ordinary-parent body. Exactly two
# super calls become explicit parent dispatch; only the diagnostic loop and
# its recorded denominator change. No WC/RF/condition/solver body is rewritten.
def _derive_pair():
    original=dedent(inspect.getsource(parent.PADiagnosticOwner.pair))
    start=original.index("        for name in ('C','A','D'):")
    end=original.index('        if (self.controller._state()!=state',start)
    old=original[start:end]
    new=('        payload,trials=self._profile20(snapshot,step,noise,latent,timestep,conditions,choose,state,D_sha,work_sha)\n')
    changed=original.replace(old,new,1)
    sites=[('super().pair(noise,latent,timestep,conditions,choose)',
            'SourcePhaseH1Owner.pair(self,noise,latent,timestep,conditions,choose)',2),
           ('all11','all20',2)]
    for before,after,count in sites:
        if changed.count(before)!=count:raise ValueError('Accepted parent derivation site changed: '+before)
        changed=changed.replace(before,after)
    inverse=changed
    for before,after,count in reversed(sites):inverse=inverse.replace(after,before)
    inverse=inverse.replace(new,old,1)
    if inverse!=original:raise ValueError('Profile parent changed outside explicit loop/sites')
    namespace={**vars(parent),'SourcePhaseH1Owner':SourcePhaseH1Owner}
    exec(compile(changed,__file__+'#accepted-H1-body-price20','exec'),namespace)
    return namespace['pair']


PAProfile20Owner.pair=_derive_pair()


def install_profile20(*a,quiet_observers=False,**kw):
    constructor=functools.partial(PAProfile20Owner,quiet_observers=quiet_observers)
    function=bind_globals(parent.install_pa_diagnostics.__wrapped__,{'PADiagnosticOwner':constructor})
    return contextmanager(function)(*a,**kw)
