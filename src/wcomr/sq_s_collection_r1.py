"""S's fixed-parent same-state measurements; no GPU dispatcher or mask fitting.

Only actual C positions pay a separate Dense teacher. Actual D outputs are
reused, and their C counterfactual reads sources captured before that D. Raw
states are offered to the caller's streaming sink only at four F19 positions.
The sink, whole-card controls, resource quote and real-model acceptance remain
separate requirements.
"""
import ast
import copy
from enum import Enum
import time

import numpy as np
import torch

from .cfg_guided_w1_forward import compile_collection
from .cfg_paired_probe_forward import _function, RF_PATH, RF_SHA
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .full_sampling import CompleteStateRoundtrip
from .mid_coverage import WC_FIELDS, tree_digest
from .partial_mlp_deployment_state import plain, tensor_bytes
from .policy_generator_r1 import production_sampling as production
from .policy_interval_readout_r1 import ReadoutKernel
from .source_aware_phase_sampling import bind_globals
from .sq_risk_r1 import TARGETS, branch_moments
from .sq_s_owner_roundtrip_r1 import PolicyOwnerRoundtrip
from .sq_s_sources_r1 import PARENTS, capture_before_pair

RAW_STEPS=(9,22,33,35)


def require(value,message):
    if not value:raise ValueError(message)


def data_record(value):
    """CPU-owned data only; never serialize a live condition/model object."""
    value=plain(value)
    if isinstance(value,torch.Tensor):return value.detach().cpu().clone()
    if isinstance(value,Enum):return data_record(value.value)
    if isinstance(value,np.ndarray):
        return dict(numpy_dtype=str(value.dtype),numpy_shape=list(value.shape),values=value.tolist())
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:data_record(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return type(value)(data_record(v) for v in value)
    if value is None or type(value) in (str,int,float,bool):return value
    raise TypeError('Unregistered S artifact field: '+type(value).__name__)


class DenseFeatures:
    def __init__(self,retain_hidden):
        self.features={};self.retain_hidden=retain_hidden

    def prewarp(self,*args):pass
    def output(self,*args):pass

    def hidden(self,net,skipped,branch,original,probe,hidden,kwargs,embedding,adaln):
        require(not skipped and branch not in self.features,'One actual Dense teacher observation per branch required')
        row=dict(original=original.detach().clone(),probe=probe.detach().clone())
        if self.retain_hidden:
            row.update(hidden=hidden.detach().clone(),embedding=embedding.detach().clone(),adaln=copy.deepcopy(adaln))
        self.features[branch]=row


class SParentCollector:
    def __init__(self,owner,*,parent,prompt,enabled,sink,logical_copy_cap_bytes,runtime,wc,rf):
        require(parent in PARENTS and type(enabled) is bool and callable(sink),'Registered parent, explicit ON/OFF and sink required')
        require(type(logical_copy_cap_bytes) is int and logical_copy_cap_bytes>0,'Explicit diagnostic copy cap required')
        require(tuple(t for t,a in enumerate(owner.policy['actions'],1) if a=='D')==PARENTS[parent]
                and all(a in ('C','D') for a in owner.policy['actions']),'Exact fixed C-only parent required')
        self.owner=owner;self.parent=parent;self.prompt=prompt;self.enabled=enabled;self.sink=sink
        self.copy_cap=logical_copy_cap_bytes;self.runtime=runtime;self.wc=wc;self.rf=rf
        self.rows=[];self.features={};self.collecting=False;self.original_hidden=owner.readout.hidden
        # compile_collection captures readout.hidden at owner construction.
        # Recompile against the same actual modules after installing this one
        # additional declared observation. The parent chooses the same actions.
        owner.readout.hidden=self.hidden
        _,owner.executor.denoise,proof=compile_collection(runtime,wc,rf,owner.readout)
        changed=copy.deepcopy(dict(proof));original=copy.deepcopy(dict(owner.proof))
        changed['production_WC_globals']['_mf_a_hidden']=original['production_WC_globals']['_mf_a_hidden']
        require(changed==original,'S parent changed production outside its declared hidden observer')
        owner.proof=proof
        self.kernel=ReadoutKernel(owner.model,runtime,wc,rf,owner.readout.warp)

    def hidden(self,net,skipped,branch,original,probe,hidden,kwargs,embedding,adaln):
        self.original_hidden(net,skipped,branch,original,probe,hidden,kwargs,embedding,adaln)
        if self.collecting:
            step=self.owner.readout.current['step']
            require(branch not in self.features and skipped==(step not in PARENTS[self.parent]),
                    'S observed a different actual parent action')
            self.features[branch]=dict(original=original.detach().clone(),probe=probe.detach().clone(),
                embedding=embedding.detach().clone(),adaln=copy.deepcopy(adaln))

    def copy_budget(self,inputs):
        owner=self.owner;net=owner.net
        live=plain((
            {k:getattr(net,k) for k in WC_FIELDS if hasattr(net,k)},
            {k:v for k,v in vars(owner.model.sample_scheduler).items() if not callable(v)},
            list(net.buffers()),owner.history,owner.readout.history,
            [vars(c) for c in owner.readout.calibrators],inputs[:3],[vars(c) for c in inputs[3]]))
        # Includes two physical checkpoints, owner/teacher/input copies and a
        # CPU sink copy. It is a conservative logical bound, not device peak.
        upper=8*tensor_bytes(live)
        require(upper<=self.copy_cap,'S diagnostic logical copy cap exceeded before snapshots')
        return upper

    @torch.no_grad()
    def pair(self,parent_pair,noise,latent,timestep,conditions,choose):
        owner=self.owner;step=owner.readout.completed+1;inputs=(noise,latent,timestep,conditions)
        selected=self.enabled and step in TARGETS
        self.features={};self.collecting=selected
        pre=past=None;logical=0
        if selected:
            logical=self.copy_budget(inputs)
            past=capture_before_pair(owner,parent=self.parent,step=step)
            if step not in PARENTS[self.parent]:
                pre=CompleteStateRoundtrip(owner.net,owner.model.sample_scheduler,latent)
        try:actual=parent_pair(*inputs,choose)
        finally:self.collecting=False
        history=owner.history[-1]
        require(history['actual']==owner.policy['actions'][step-1] and history['fallback_reason'] is None
                and history['source_history']['extra_heads']==0,'Fixed S parent deviated or paid an unregistered head')
        if selected:self.observe(step,inputs,actual,pre,past,logical)
        self.features.clear()
        return actual

    def observe(self,step,inputs,actual,pre,past,logical):
        owner=self.owner;net=owner.net;started=time.perf_counter()
        require(set(self.features)=={0,1},'Both paid parent prefixes required')
        post=CompleteStateRoundtrip(net,owner.model.sample_scheduler,inputs[1])
        own=PolicyOwnerRoundtrip(owner,logical_copy_cap_bytes=self.copy_cap)
        physical_before=post.fingerprint();owner_before=own.origin
        inputs_before=tree_digest(plain((inputs[:3],[vars(c) for c in inputs[3]])))
        sources_before=tree_digest(plain(past.source()))
        require(not any(torch.is_inference(p) for p in net.parameters()),'Versioned model parameters required for the S shadow guard')
        versions=[(p,p._version) for p in net.parameters()]
        raw_selected=self.parent=='F19-C' and step in RAW_STEPS
        dense_features=None;raw=None;row=None
        def restore_and_verify():
            post.restore();own.restore()
            require(post.fingerprint()==physical_before and own.fingerprint()==owner_before,
                    'S shadow changed protected parent state')
            require(tree_digest(plain((inputs[:3],[vars(c) for c in inputs[3]])))==inputs_before,
                    'S shadow changed original paired inputs or condition')
            require(tree_digest(plain(past.source()))==sources_before,'S shadow changed the strictly past true-D sources')
            require(all(p._version==v for p,v in versions),'S shadow changed model weights')
        try:
            if pre is not None:
                pre.restore()
                observer=DenseFeatures(raw_selected)
                _,denoise,proof=compile_collection(self.runtime,self.wc,self.rf,observer)
                teacher_executor=NativePolicyPairedExecutor(owner.model,denoise,torch,
                    wc_forward=self.wc.worldcache_mini_train_dit_forward,
                    rf_denoise=self.rf.Video2WorldModelRectifiedFlow.denoise)
                teacher=teacher_executor.pair(*copy.deepcopy(inputs),lambda _:'DD')
                require(teacher_executor.last['action']=='DD' and set(observer.features)=={0,1},
                        'One complete independent Dense teacher pair required')
                require(all(torch.equal(self.features[b][key],observer.features[b][key])
                    for b in (0,1) for key in ('original','probe')),'S teacher paid a different input/prefix')
                candidate=actual;dense_features=observer.features
            else:
                teacher=actual
                candidate,_,_=self.kernel.run('C',source=past.source(),
                    current=[self.features[b] for b in (0,1)],pair_inputs=copy.deepcopy(inputs))
            require(all(v.dtype==torch.float32 for v in (*candidate,*teacher)),
                    'Actual aligned FP32 post-RF output coordinates required')
            moments=branch_moments(candidate,teacher,a=8.,b=-7.)
            row=dict(prompt=self.prompt,parent=self.parent,step=step,context=list(owner.readout.context),
                planned_parent_action=owner.policy['actions'][step-1],moments=moments,
                source=past.metadata(),extra_Dense_teacher_pairs=int(pre is not None),
                extra_C_readout_pairs=int(pre is None),extra_Dense_hidden_replay_heads=0,
                raw_state_selected=raw_selected,teacher_writes_parent=False,
                actual_D_teacher_reused=pre is None,paid_prefix_equal=True,
                parent_roundtrip_equal=True,logical_copy_bytes_upper_bound=logical,
                P1_Dense_hidden_head_replay_accepted=False)
            if raw_selected:
                require(dense_features is not None,'The four registered F19 raw positions must be actual C')
                raw=data_record(dict(schema='SQ_S_F19_RAW_CPU_DATA_R1',prompt=self.prompt,parent=self.parent,
                    context=owner.readout.context,step=step,source=past.metadata(),anchors=past.anchors,
                    current=[self.features[b] for b in (0,1)],teacher=teacher,
                    teacher_features=[dense_features[b] for b in (0,1)],
                    pair_inputs=dict(noise=inputs[0],latent=inputs[1],timestep=inputs[2],
                        conditions=[dict(class_name=type(c).__qualname__,fields=vars(c)) for c in inputs[3]]),
                    P1_Dense_hidden_head_replay_accepted=False,
                    serialized_whole_pipeline_resume_accepted=False,source_proof=dict(owner.proof)))
        finally:restore_and_verify()
        try:self.sink(copy.deepcopy(row),raw)
        finally:restore_and_verify()
        row['diagnostic_seconds_including_shadow_copy_hash_sink']=time.perf_counter()-started
        self.rows.append(row)

    def finish(self):
        expected=list(TARGETS) if self.enabled else []
        require([r['step'] for r in self.rows]==expected,'Complete S parent target cohort required')
        expected_C=sum(t not in PARENTS[self.parent] for t in TARGETS) if self.enabled else 0
        require(sum(r['extra_Dense_teacher_pairs'] for r in self.rows)==expected_C
                and sum(r['extra_C_readout_pairs'] for r in self.rows)==len(expected)-expected_C,
                'S Dense/C shadow head denominators differ')
        return copy.deepcopy(self.rows)

    def close(self):
        self.features.clear()
        if self.original_hidden is None:return
        installed=vars(self.owner.readout).get('hidden')
        require(getattr(installed,'__self__',None) is self,'S hidden observer binding changed before cleanup')
        del self.owner.readout.__dict__['hidden']
        self.original_hidden=None;self.kernel=None


def execute(inference,sample,*,parent,profile,policy,enabled,sink,logical_copy_cap_bytes,**kwargs):
    require(sample.num_steps==35 and sample.guidance==7,'This S collector binds the registered actual36 guidance7 request')
    source=_function(kwargs['runtime'],RF_PATH,RF_SHA,'get_velocity_fn_from_batch')
    cfg=[n for n in ast.walk(source) if isinstance(n,ast.Assign)
         and any(isinstance(t,ast.Name) and t.id=='velocity_pred' for t in n.targets)]
    require(len(cfg)==1 and ast.unparse(cfg[0].value)=='cond_v + guidance * (cond_v - uncond_v)',
            'S coefficients must be derived from the pinned actual CFG arithmetic')
    holder={}
    class ObservedOwner(production.PolicyOwner):
        def __init__(self,*args,**kw):
            super().__init__(*args,**kw)
            holder['collector']=SParentCollector(self,parent=parent,prompt=sample.name,enabled=enabled,
                sink=sink,logical_copy_cap_bytes=logical_copy_cap_bytes,
                runtime=kwargs['runtime'],wc=kwargs['wc'],rf=kwargs['rf'])
        def pair(self,*args):return holder['collector'].pair(super().pair,*args)
        def close(self):
            try:holder['collector'].close()
            finally:super().close()
    runner=bind_globals(production.execute,{'PolicyOwner':ObservedOwner})
    try:
        result=runner(inference,sample,profile=profile,policy=policy,**kwargs)
        result['S_rows']=holder['collector'].finish() if result['status']=='COMPLETE' else []
        result['S_collection_enabled']=enabled
        result['S_real_model_or_video_accepted']=False
        return result
    finally:holder.clear()
