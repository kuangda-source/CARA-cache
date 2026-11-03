"""Explicit residual-hold C and bounded conditional-only D for the F19 CAL card.

Pinned upstream stays unchanged. A retains its current two-layer probe and
post-RF phase rule. Only genuine DD refreshes the stored CFG difference.
"""
import ast
import copy
import hashlib

import torch

from .cfg_guided_w1_collection import signature
from .cfg_guided_w1_forward import compile_collection
from .cfg_paired_probe_forward import _compile, _function, WC_PATH
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .policy_generator_r1.production_sampling import PolicyOwner, PolicyReadout, validate_policy
from .source_aware_phase_sampling import bind_globals
from .cara_f19_speed190_identity_r1 import PARTIAL_UPDATES


def light_source(original):
    """Six exact AST changes, each with a checked structural inverse."""
    node=copy.deepcopy(original)
    originals={}
    hits={key:0 for key in ('probe','drift','interpolation','flow','probe_clone','unused_clone')}
    predicate="self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh"
    light=ast.parse('_f19_light_C(self)',mode='eval').body
    def guard(body):
        value=ast.parse('if not _f19_light_C(self):\n    pass').body[0]
        value.body=body
        return value
    class Change(ast.NodeTransformer):
        def visit_For(self,n):
            if ast.unparse(n.iter)=='anchor_blocks':
                hits['probe']+=1;return guard([n])
            return self.generic_visit(n)
        def visit_If(self,n):
            n=self.generic_visit(n)
            if ast.unparse(n.test)=='len(self.residual_window[current_idx]) >= 2':
                hits['interpolation']+=1;n.test=ast.BoolOp(op=ast.And(),values=[n.test,ast.UnaryOp(op=ast.Not(),operand=copy.deepcopy(light))])
            if ast.unparse(n.test)=="getattr(self, 'worldcache_flow_enabled', False) and self.previous_input[current_idx] is not None":
                hits['flow']+=1;n.body=[guard(n.body)]
            positions=[i for i,v in enumerate(n.body) if isinstance(v,ast.If) and ast.unparse(v.test)==predicate]
            if positions:
                if len(positions)!=1:raise ValueError('Ambiguous pinned WC decision')
                i=positions[0];hits['drift']+=1
                branch=ast.parse('if _f19_light_C(self):\n    delta_x=0.0\n    delta_y=0.0\n    dynamic_thresh=1.0\nelse:\n    pass').body[0]
                branch.orelse=n.body[:i];n.body=[branch]+n.body[i:]
            return n
        def visit_Assign(self,n):
            source=ast.unparse(n)
            key={'test_x = x_B_T_H_W_D.clone()':'probe_clone',
                 'ori_x_clone = x_B_T_H_W_D.clone()':'unused_clone'}.get(source)
            if key:
                hits[key]+=1
                originals[key]=copy.deepcopy(n.value)
                n.value=ast.IfExp(test=copy.deepcopy(light),body=ast.Name(id='x_B_T_H_W_D',ctx=ast.Load()),orelse=n.value)
            return n
    node=Change().visit(node)
    if any(v!=1 for v in hits.values()):raise ValueError('Pinned light-C transformation sites differ: '+repr(hits))
    class Undo(ast.NodeTransformer):
        def visit_If(self,n):
            if ast.unparse(n.test)=='not _f19_light_C(self)':
                return [self.visit(v) for v in n.body]
            if ast.unparse(n.test)=='_f19_light_C(self)':
                return [self.visit(v) for v in n.orelse]
            n=self.generic_visit(n)
            if isinstance(n.test,ast.BoolOp) and len(n.test.values)==2 and ast.unparse(n.test.values[1])=='not _f19_light_C(self)':
                n.test=n.test.values[0]
            return n
        def visit_IfExp(self,n):
            if ast.unparse(n.test)=='_f19_light_C(self)':return n.orelse
            return self.generic_visit(n)
    inverse=Undo().visit(copy.deepcopy(node))
    if ast.dump(inverse,include_attributes=False)!=ast.dump(original,include_attributes=False):
        raise ValueError('Light-C changed unregistered pinned statements')
    return node,dict(sites=hits,inverse_AST_equal=True,
        transformed_AST_sha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest())


class SpeedReadout(PolicyReadout):
    def __init__(self,*args,partial_updates=(),**kwargs):
        super().__init__(*args,**kwargs)
        self.partial_updates=tuple(partial_updates)
        self.delta=self.delta_step=None

    def prewarp(self,net,branch,hidden):
        if self.current['step'] not in self.partial_updates and self.policy['actions'][self.current['step']-1]=='A':
            return super().prewarp(net,branch,hidden)
        self._branch(net,branch)

    def hidden(self,net,skipped,branch,*args):
        if self.current['step'] in self.partial_updates and branch==1:
            self._branch(net,branch)
            if not skipped or branch in self.current['branches']:raise ValueError('Conditional-only D requires an unrefreshed negative branch')
            self.current['branches'][branch]=dict(action='C',proposed_head=None,
                status='DELTA_HOLD_NO_UNCONDITIONAL_D',past_D_steps=self.calibrators[branch].receipt()['anchor_steps'],extra_heads=0)
            return
        return super().hidden(net,skipped,branch,*args)

    def end(self,actual,action):
        cur=self.current
        step=cur['step']
        if step not in self.partial_updates:
            result=super().end(actual,action)
            if action=='DD':
                self.delta=(actual[0]-actual[1]).detach().clone();self.delta_step=step
            return result
        if (action!='DC' or set(cur['branches'])!={0,1}
                or [cur['branches'][b]['action'] for b in (0,1)]!=['D','C']
                or any(not cur['branches'][b].get('output_seen') for b in (0,1))
                or int(self.net.cnt)!=2*step%70 or self.delta_step is None
                or not 1<=step-self.delta_step<=2
                or signature((cur['noise'],cur['latent'],cur['timestep']))!=cur['input_signature']
                or signature([vars(c) for c in cur['conditions']])!=cur['condition_signature']):
            raise ValueError('Complete causal conditional-D/delta-hold pair required')
        result=(actual[0],actual[0]-self.delta)
        if any(not bool(torch.isfinite(v).all()) for v in result):raise ValueError('Nonfinite held-difference output')
        self.history.append(dict(step=step,action='DC',shared_alpha=None,
            branch_status=[cur['branches'][b]['status'] for b in (0,1)],
            past_D_steps=[cur['branches'][b]['past_D_steps'] for b in (0,1)],
            delta_true_DD_step=self.delta_step,delta_actual_age=step-self.delta_step,
            extra_heads=0,teacher_calls=0,post_RF_fusion=True,C_readout_updates_D_anchor=False))
        self.current=None;self.completed=step
        return result


class SpeedOwner(PolicyOwner):
    def __init__(self,model,*,policy,profile,context,runtime,wc,rf,light_C=False,partial_updates=()):
        validate_policy(profile,policy)
        self.model,self.net,self.policy,self.profile=model,model.net,policy,profile
        self.light_C=light_C
        self.partial_updates=tuple(partial_updates)
        last=None
        for step,action in enumerate(policy['actions'],1):
            if step in self.partial_updates:
                if action!='D' or step in profile.protected_dense or last is None or step-last>2:
                    raise ValueError('Partial D must be unprotected and within two actual updates of true DD')
            elif action=='D':last=step
        if self.partial_updates and self.partial_updates!=PARTIAL_UPDATES:raise ValueError('Frozen four partial-D positions required')
        self.readout=SpeedReadout(model,context=context,policy=policy,partial_updates=self.partial_updates)
        def is_light(net):
            cur=self.readout.current
            return bool(cur and ((light_C and policy['actions'][cur['step']-1]=='C')
                or (cur['step'] in self.partial_updates and int(net.cnt)%2==1)))
        transform_proof={}
        def source(*args):
            node=_function(*args)
            if args[1]==WC_PATH:
                node,proof=light_source(node);transform_proof.update(proof)
            return node
        def compiler(node,namespace,label):
            return _compile(node,dict(namespace,_f19_light_C=is_light),label)
        from .cfg_paired_probe_production import _bindings
        def bindings(function,actual,overrides):
            return _bindings(function,actual,dict(overrides,_f19_light_C=is_light))
        compile_speed=bind_globals(compile_collection,dict(_function=source,_compile=compiler,_bindings=bindings))
        _,denoise,self.proof=compile_speed(runtime,wc,rf,self.readout)
        self.light_source_proof=transform_proof
        self.executor=NativePolicyPairedExecutor(model,denoise,torch,
            wc_forward=wc.worldcache_mini_train_dit_forward,rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
        self.choose=self._choose
        self.history=[];self.deployment=self
        self.fallback_reason=None;self.force_dense=False

    def _choose(self,packets):
        if not self.force_dense and self.readout.completed+1 in self.partial_updates:
            if self.readout.delta_step is None or not 1<=self.readout.completed+1-self.readout.delta_step<=2:
                raise ValueError('Unavailable or stale true-DD difference')
            return 'DC'
        return super()._choose(packets)

    def pair(self,*args,**kwargs):
        result=super().pair(*args,**kwargs)
        row=self.history[-1]
        if row['step'] in self.partial_updates:
            row['actual']='CONDITIONAL_D_DELTA_HOLD'
        row['light_C']=self.light_C and row['planned']=='C'
        return result

    def close(self):
        self.readout.delta=None
        super().close()
