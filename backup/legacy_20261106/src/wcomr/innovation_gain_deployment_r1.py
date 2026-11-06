"""Fixed-D free-running readouts. No shadow teacher, fitting or parent reset.

Consume the C output already paid for by the current sparse forward; pay only
one additional candidate head/RF pair. B1 separately checks this path against
its fully isolated adapter. D alone updates the two true feature anchors.
"""
import copy
import math
from types import SimpleNamespace

import torch

from . import clean_speed20_r1 as clean
from .cfg_guided_w1_outputs import shared_output_fusion
from .innovation_gain_r1 import gains_checked, gain_proposal
from .scout_readout_v22 import Anchor, D_STEPS, proposal, UnsupportedReadout
from .scout_parent_v22 import PLAN, noise_coordinates
from .source_phase_fixed_mask_r1 import FixedMaskH1Owner

ROLES=('WC_C','A_PHASE','FULL','DEEP','DCTA','IG_SCALAR','IG_BAND')


@torch.no_grad()
def paid_readout(kernel, role, *, current, anchors, pair_inputs, cached, ratio, age, alpha, gains=None):
    if role not in ROLES:raise ValueError('Registered fixed-D role required')
    if role=='WC_C':return cached
    if role.startswith('IG_'):gains=gains_checked(gains)
    if role=='IG_SCALAR' and gains[0]!=gains[1]:raise ValueError('Scalar requires equal gains')
    noise,latent,timestep,conditions=pair_inputs;raw=[]
    for branch,(old,last) in enumerate(anchors):
        row=current[branch];p=row['probe']-row['original']
        if role.startswith('IG_'):
            residual=gain_proposal(p,old,last,ratio=ratio,gains=gains,age=age)
        else:
            residual=proposal('R4_GLOBAL' if role=='DEEP' else role,p,old,last,kappa=ratio,age=age)[0]
        proxy=SimpleNamespace(cnt=branch,previous_input=[None,None],previous_internal_states=[None,None],
            worldcache_flow_enabled=kernel.net.worldcache_flow_enabled,worldcache_flow_scale=kernel.net.worldcache_flow_scale)
        proxy.previous_input[branch]=row['original'];proxy.previous_internal_states[branch]=row['probe']
        hidden=kernel.warp(proxy,row['original']+residual,last.residual,row['original'].shape[1])
        head=kernel.net.unpatchify(kernel.net.final_layer(hidden,row['embedding'],adaln_lora_B_T_3D=row['adaln']))
        raw.append(kernel.to_velocity(kernel.model,noise,latent,timestep,conditions[branch],_supplied_net_output=head))
    return shared_output_fusion(cached,tuple(raw),alpha)


class GainDeploymentOwner(FixedMaskH1Owner):
    def __init__(self,*args,role,gains,feature_context,runtime,wc,rf,**kwargs):
        if role not in ROLES:raise ValueError('Registered readout required')
        if role.startswith('IG_'):gains=gains_checked(gains)
        super().__init__(*args,replay_plan=PLAN,runtime=runtime,wc=wc,rf=rf,**kwargs)
        self.role,self.gains,self.feature_context=role,gains,feature_context
        self.bank=[];self.features={};self.gain_history=[]
        self.gain_head_calls=0
        def count_head(*args):self.gain_head_calls+=1
        self.head_hook=self.model.net.final_layer.register_forward_pre_hook(count_head)
        self.old_hidden=self.deployment.readout.semantic_hidden
        self.deployment.readout.semantic_hidden=self.capture_hidden
        from .policy_interval_readout_r1 import ReadoutKernel
        self.kernel=ReadoutKernel(self.model,runtime,wc,rf,self.deployment.warp)

    def capture_hidden(self,net,skipped,branch,original,probe,hidden,kwargs,embedding,adaln):
        if branch in self.features:raise ValueError('Duplicate current branch')
        self.features[branch]=dict(original=original,probe=probe,embedding=embedding,adaln=adaln,
            anchor_probe=net.probe_residual_cache[branch],residual=net.residual_cache[branch])
        return self.old_hidden(net,skipped,branch,original,probe,hidden,kwargs,embedding,adaln)

    @torch.no_grad()
    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1;self.features={}
        xis,_=noise_coordinates(self.model.sample_scheduler,step,timestep)
        inputs=(noise,latent,timestep,conditions)
        heads_before=self.gain_head_calls
        actual=super().pair(*inputs,choose)
        if self.history[-1]['action']!=('DD' if step in D_STEPS else 'CC') or set(self.features)!={0,1}:
            raise ValueError('Fixed D/current branch mismatch')
        row=dict(step=step,role=self.role,true_anchor_write=False,teacher_calls=0,extra_head_pairs=0,
                 alpha=None,gains=list(self.gains) if self.gains is not None else None,fallback_reason=None)
        if step in D_STEPS:
            if self.role!='WC_C':
                self.bank.append(tuple(Anchor(self.feature_context,b,step,xis[step-1],
                    self.features[b]['anchor_probe'].detach().clone(),self.features[b]['residual'].detach().clone()) for b in (0,1)))
                self.bank=self.bank[-2:]
            returned=actual;row['true_anchor_write']=True
        elif self.role=='WC_C':returned=actual
        else:
            if len(self.bank)!=2:raise ValueError('Missing two true D anchors')
            anchors=tuple((self.bank[0][b],self.bank[1][b]) for b in (0,1))
            old,last=anchors[0];span=last.xi-old.xi
            if not 0<=old.xi<last.xi<xis[step-1]<=1:raise ValueError('Invalid actual sigma spans')
            ratio=(xis[step-1]-last.xi)/span;alpha=1. if step<25 else .5
            try:
                returned=paid_readout(self.kernel,self.role,current=[self.features[b] for b in (0,1)],
                    anchors=anchors,pair_inputs=inputs,cached=actual,ratio=ratio,age=step-last.step,alpha=alpha,gains=self.gains)
                if any(not bool(torch.isfinite(v).all()) for v in returned):raise UnsupportedReadout('Nonfinite output')
            except UnsupportedReadout as exc:
                returned=actual;row['fallback_reason']=str(exc)
            row.update(alpha=alpha,ratio_h_over_H=ratio,anchor_steps=[old.step,last.step])
        row['actual_head_calls']=self.gain_head_calls-heads_before
        row['extra_head_pairs']=(row['actual_head_calls']-2)/2
        self.gain_history.append(row);self.features.clear()
        return returned

    def close(self):
        self.deployment.readout.semantic_hidden=self.old_hidden
        self.head_hook.remove()
        self.bank.clear();self.features.clear();self.kernel=None
        return super().close()


def execute(inference,sample,*,role,gains,feature_context,table_parameters,previous_parameters,**kwargs):
    holder={}
    def factory(*args,**kw):
        owner=GainDeploymentOwner(*args,role=role,gains=gains,feature_context=feature_context,
            table_parameters=table_parameters['SOURCE_PHASE'],math_parameters=previous_parameters,
            horizon=1,source_mode='FUSION',**kw)
        holder['owner']=owner;return owner
    try:
        with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
            result=clean.execute(inference,sample,'KEEP_A_P',**kwargs)
        result.update(gain_deployment_history=copy.deepcopy(holder['owner'].gain_history),readout_role=role,
                      frozen_gains=list(gains) if gains is not None else None,teacher_calls=0,online_fitting=False)
        if result['status']=='COMPLETE' and len(result['gain_deployment_history'])!=36:
            raise ValueError('Complete free-running readout history required')
        return result
    finally:holder.clear()
