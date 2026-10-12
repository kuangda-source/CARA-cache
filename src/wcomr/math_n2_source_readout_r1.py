"""Teacher-free, source-consistent fusion in post-RF velocity space.

One paid probe/ordinary head per branch. Only requested correction heads are
computed; no tensor hashing, snapshot, fitting, or future labels occur here.
The existing P residual prediction and true-D observation owners are reused.
"""
import copy

import torch

from .partial_mlp_guided_readout import SemanticPartialReadout
from .cfg_guided_w1_deployment import alpha_at
from .cfg_guided_w1_collection import signature
from .cfg_guided_w1_outputs import shared_output_fusion
from .math_source_fusion_r1 import fuse_outputs
from .p_working_reference_residual_r1 import predict_P_reference

VERSION='MATH_N2_POST_RF_SOURCE_FUSION_R1'


class SourceFusionReadout(SemanticPartialReadout):
    def __init__(self,deployment,*,method,gamma,mode='FUSION'):
        if not 0<=gamma<=1 or mode not in ('FUSION','P_OFF'):
            raise ValueError('One frozen shared gain and registered source mode required')
        super().__init__(deployment,method=method)
        self.gamma,self.mode=float(gamma),mode

    def wants_A(self):
        if self.current is not None and 'selected_A' in self.current:
            return self.current['selected_A']
        cur=self.deployment.current
        choice=cur.get('source_choice') if cur else None
        if choice is not None and choice.reason.startswith('MATH_EVENT_'):
            result=choice.reason.endswith(':A')
        else:
            result=not(self.mode=='P_OFF' and self.deployment.working[0]
                       and self.deployment.working[0]['kind']=='P')
        # PartialDeployment.commit clears its current packet before the
        # readout's end. Preserve the already selected scalar decision only.
        if self.current is not None:self.current['selected_A']=bool(result)
        return result

    def prewarp(self,net,branch,hidden):
        # Selection has already occurred. Plain C need not clone a feature for
        # a correction that will not be computed.
        if self.deployment.current['action']=='C' and not self.wants_A():
            self._branch(net,branch);return
        return super().prewarp(net,branch,hidden)

    @torch.no_grad()
    def _P_hidden(self,net,skipped,branch,original,probe,hidden,block_kwargs,embedding,adaln):
        step=self._branch(net,branch);d=self.deployment;c=self.calibrators[branch]
        source=d.working[branch]
        if (skipped is not True or d.current['action']!='C' or source['kind']!='P'
                or branch not in self.current['prewarp'] or any(m.training for m in net.modules())):
            raise ValueError('Actual paid P-source C boundary required')
        self.warp,self.to_velocity=d.warp,d.to_velocity
        before=copy.deepcopy(c.receipt())
        working_probe,working_residual=net.probe_residual_cache[branch],net.residual_cache[branch]
        entry={'action':'C','proposed_head':None,'extra_heads':0,
               'past_D_steps':before['anchor_steps'],'working_source_kind':'P'}
        self.current['branches'][branch]=entry
        residual,proof=predict_P_reference(calibrator=c,context=self.context,step=step,slot=branch,
            working_source=source,current_probe=probe-original,working_probe=working_probe,
            working_prewarp_residual=working_residual,
            official=self.current['prewarp'][branch]-original,beta_mode='unit')
        entry.update(status=proof['status'],P_reference=proof)
        try:
            if proof['status'].endswith('fallback'):return
            devices=([probe.device.index if probe.device.index is not None else torch.cuda.current_device()]
                     if probe.device.type=='cuda' else [])
            buffers=[(b,b.detach().clone()) for b in net.final_layer.buffers()]
            try:
                with torch.random.fork_rng(devices=devices):
                    value=self.warp(net,original+residual,working_residual,original.shape[1])
                    entry['proposed_head']=net.unpatchify(net.final_layer(value,embedding,adaln_lora_B_T_3D=adaln))
                    entry['extra_heads']=1
            finally:
                for b,saved in buffers:b.copy_(saved)
            if (net.probe_residual_cache[branch] is not working_probe
                    or net.residual_cache[branch] is not working_residual or d.working[branch] is not source):
                raise ValueError('Source readout replaced its real P cache')
        finally:
            self.current['prewarp'].pop(branch,None)
            if c.receipt()!=before:raise ValueError('Source readout mutated actual D history')

    @torch.no_grad()
    def semantic_hidden(self,net,skipped,branch,*values):
        d=self.deployment
        if d.current['action']!='C':return super().semantic_hidden(net,skipped,branch,*values)
        if not self.wants_A():
            method=self.method;self.method='OFF'
            try:return super().semantic_hidden(net,skipped,branch,*values)
            finally:self.method=method
        if d.working[branch]['kind']=='D' or self.gamma==0:
            return super().semantic_hidden(net,skipped,branch,*values)
        if self.gamma==1:return self._P_hidden(net,skipped,branch,*values)
        pre=self.current['prewarp'][branch]
        super().semantic_hidden(net,skipped,branch,*values)
        old=self.current['branches'].pop(branch)
        self.current['prewarp'][branch]=pre
        self._P_hidden(net,skipped,branch,*values)
        current=self.current['branches'][branch]
        current['old_proposed_head']=old['proposed_head']
        current['old_status']=old['status']
        current['extra_heads']+=old['extra_heads']
        current['two_related_predictions']=True

    @torch.no_grad()
    def end(self,actual,action):
        cur=self.current;wants=self.wants_A()
        if (cur is None or action not in ('CC','PP','DD') or set(cur['branches'])!={0,1}
                or ''.join(cur['branches'][b]['action'] for b in (0,1))!=action
                or int(self.net.cnt)!=2*cur['step']%70
                or any(not cur['branches'][b].get('output_seen') for b in (0,1))):
            raise ValueError('Full actual semantic pair required before source fusion')
        if (signature((cur['noise'],cur['latent'],cur['timestep']))!=cur['input_signature']
                or signature([vars(c) for c in cur['conditions']])!=cur['condition_signature']):
            raise ValueError('Source fusion changed actual solver input or condition')
        alpha=alpha_at(self.method,cur['step']) if wants else 0
        returned=actual
        if action=='CC' and alpha:
            def velocity(key):
                return tuple(self.to_velocity(self.model,cur['noise'],cur['latent'],cur['timestep'],
                    cur['conditions'][b],_supplied_net_output=cur['branches'][b][key])
                    if cur['branches'][b].get(key) is not None else actual[b] for b in (0,1))
            proposed=velocity('proposed_head')
            if any(e.get('two_related_predictions') for e in cur['branches'].values()):
                if not all(e.get('two_related_predictions') for e in cur['branches'].values()):
                    raise ValueError('Both CFG branches require the same source/gain')
                # Fuse A outputs, including their shared alpha. No assumption
                # that a nonlinear head or warp commutes with this operation.
                returned=fuse_outputs(shared_output_fusion(actual,velocity('old_proposed_head'),alpha),
                                      shared_output_fusion(actual,proposed,alpha),self.gamma)
            else:returned=shared_output_fusion(actual,proposed,alpha)
        self.history.append({'step':cur['step'],'action':action,'shared_alpha':alpha,
            'branch_status':[cur['branches'][b]['status'] for b in (0,1)],
            'working_source_kind':[cur['branches'][b]['working_source_kind'] for b in (0,1)],
            'past_D_steps':[cur['branches'][b]['past_D_steps'] for b in (0,1)],
            'extra_heads':sum(cur['branches'][b]['extra_heads'] for b in (0,1)),
            'extra_deep_blocks':0,'teacher_calls':0,'post_RF_fusion':True,
            'C_or_P_observation_updates_D_anchor':False,'source_fusion_version':VERSION,
            'gamma':self.gamma,'readout_action':'A' if action=='CC' and alpha else action[0],
            'P_reference':[copy.deepcopy(cur['branches'][b].get('P_reference')) for b in (0,1)]})
        self.completed+=1;self.current=None
        return returned
