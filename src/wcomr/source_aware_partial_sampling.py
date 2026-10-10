"""Dynamic source-aware C/P/D and fixed shared A in ordinary full UniPC.

Policy calibration, same-unit P creation quality and full pair costs are
explicit batch inputs. This module does not invent production parameters.
"""
import ast
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent
import types

import torch

from . import partial_mlp_deployment_sampling as p0
from .partial_mlp_guided_sampling import GuidedSamplingOwner
from .partial_mlp_deployment_state import DeploymentRoundtrip, plain, tensor_bytes
from .source_aware_partial_deployment import SourceAwarePartialDeployment, SourceAwarePartialPair
from .source_aware_cpd_control import SourceAwareCPDController
from .cfg_ra_joint_control import JointCDController
from .cfg_ra_joint_execution import JointPolicyPairExecutor
from .cfg_guided_w1_deployment import alpha_at

METHODS=('SOURCE_RA','DYNAMIC_NO_P','CPD','REF_CPD','A_CPD_OFF',
         'A_CPD_W1_ONE_PHASE','A_CPD_BETA1_ONE_PHASE','DENSE_CONTROL')


class SourceRAAdapter(JointPolicyPairExecutor):
    @property
    def history(self):return self.controller.history

    @property
    def running(self):return self._running

    def snapshot(self):
        return copy.deepcopy({'controller':{k:getattr(self.controller,k) for k in
            ('anchor','accumulated','last_completed_step','generation','history','poisoned')},
            'last':self.last,'base_last':self.executor.last})

    def restore(self,data):
        if self._running or self.controller.poisoned or self.executor.poisoned:
            raise ValueError('Only healthy completed reference RA boundaries restore')
        for k,v in data['controller'].items():setattr(self.controller,k,v)
        self.last,self.executor.last=data['last'],data['base_last']


class SourceRAOwner(p0.SamplingOwner):
    def __init__(self,*args,calibration,threshold,**kwargs):
        super().__init__(*args,method='SOURCE_D6',**kwargs)
        self.controller=JointCDController(calibration,threshold)
        self.executor=SourceRAAdapter(self.base,self.controller)
        self.head_calls=[]
        self.hooks.append(self.net.final_layer.register_forward_hook(lambda m,a,v:
            self.head_calls.append({'step':self.step,'slot':int(self.net.cnt)%2})))

    @property
    def history(self):return plain(self.controller.history)

    def installation(self):
        return super().installation()+(id(self.controller),self.controller.calibration.fingerprint,
                                      self.controller.threshold,id(self.executor))

    def own_state(self):
        d=super().own_state();d['actual_head_calls']=self.head_calls;return d

    def restore_own_state(self,data):
        super().restore_own_state(data);self.head_calls=data['actual_head_calls']

    def finish(self):
        result=super().finish()
        if len(self.head_calls)!=72:raise ValueError('Original RA actual head count differs')
        result.pop('fixed_P_steps',None)
        result.update(method='SOURCE_RA',source_RA_history=plain(self.controller.history),
                      actual_original_plus_candidate_heads=copy.deepcopy(self.head_calls))
        return result


class DynamicSamplingOwner(GuidedSamplingOwner):
    def __init__(self,model,*,method,context,runtime,wc,rf,calibration,spec):
        if method not in METHODS or method=='SOURCE_RA':raise ValueError('Explicit dynamic method required')
        self.controller=SourceAwareCPDController(calibration,spec['threshold'],spec['costs'],spec['partial_prior'])
        a_method=method.removeprefix('A_CPD_') if method.startswith('A_CPD_') else 'OFF'
        def factory(*args,**kwargs):
            # No fixed P positions: all eligible choices come from paid probes.
            kwargs['p_steps']=()
            return SourceAwarePartialDeployment(*args,controller=self.controller,
                reference=method=='REF_CPD',**kwargs)
        original=GuidedSamplingOwner.__init__
        if original.__closure__:raise ValueError('Original guided constructor gained a closure')
        derived=types.FunctionType(original.__code__,
            {**original.__globals__,'GuidedPartialDeployment':factory},original.__name__,original.__defaults__)
        derived.__kwdefaults__=original.__kwdefaults__
        derived(self,model,method='A_P0_'+a_method,context=context,runtime=runtime,wc=wc,rf=rf)
        self.dynamic_method,self.reference=method,method=='REF_CPD'
        self.executor=SourceAwarePartialPair(self.base,self.deployment)

    def installation(self):
        return super().installation()+(self.dynamic_method,id(self.controller),
            self.controller.calibration.fingerprint,self.controller.threshold,
            self.controller.costs,self.controller.partial_prior,self.reference)

    def check_healthy(self):
        super().check_healthy()
        if self.controller.poisoned:raise ValueError('Failed dynamic pair cannot restore or continue')

    def own_state(self):
        data=super().own_state();data['source_controller']=self.controller.state_dict();return data

    def restore_own_state(self,data):
        super().restore_own_state(data);self.controller.restore(data['source_controller'])

    def checkpoint(self,physical,gate,config):
        self.check_healthy()
        remaining=config['logical_copy_cap_bytes']-gate['logical_tensor_copy_bytes']
        extra=tensor_bytes(self.own_state())
        if extra>remaining:raise ValueError('Dynamic policy/state copy budget exceeded')
        if gate['GPU_logical_copy_bytes'] and torch.cuda.mem_get_info()[0]<gate['required_GPU_headroom_bytes']+2*extra:
            raise ValueError('Dynamic complete checkpoint GPU headroom unavailable')
        own=DeploymentRoundtrip(self,logical_copy_cap_bytes=remaining)
        before=physical.fingerprint()
        if config.get('CPU_mutate_owned_state_before_restore',False):
            self.controller.creation_floor=999.;self.controller.accumulated=999.
            self.controller.working_step=-99;self.controller.consecutive_P=-99
            self.controller.history.clear()
            self.deployment.readout.completed=-99;self.deployment.readout.history.clear()
            self.deployment.working=[None,None];self.deployment.opportunities=-99
            self.head_calls.append({'injected_checkpoint_only':True})
        physical.restore();own.restore()
        if physical.fingerprint()!=before:raise ValueError('Dynamic physical state restore differs')
        return {'additional_state_bytes':own.bytes,'complete_additional_state_restored':True,
            'physical_state_restored':True,'fingerprint':own.origin,
            'checkpoint_perturbation_executed':bool(config.get('CPU_mutate_owned_state_before_restore',False)),
            'source_controller_and_A_history_perturbation_restored':True,
            'arbitrary_failed_pair_recovery_claim':False}

    def finish(self):
        result=super().finish();result.pop('fixed_P_steps',None)
        result['method']=self.dynamic_method
        result['dynamic_source_aware_policy']=True
        return result


def verify_batch(state):
    if (state.get('planned_parent_paths')!=32 or len(state.get('requests',[]))!=4
            or state.get('planned_origins')!=0 or state.get('planned_post_RF_branch_tensors')!=0
            or state.get('selected_steps')!=[]):
        raise ValueError('Complete new four-request eight-method dynamic scope required')
    for request in state['requests']:
        rows=request['paths']
        if tuple(r['collect'] for r in rows)!=METHODS or len(request['prepared_input_calls'])!=8:
            raise ValueError('Missing complete dynamic method/control scope')
        if any(p['prepared']!=request['prepared_input_calls'][0]['prepared'] for p in request['prepared_input_calls']):
            raise ValueError('Dynamic prepared inputs differ')
        for row in rows:
            c=row['collection_complete'];method=row['collect'];d=c.get('deployment')
            if (row['status']!='COMPLETE_PARENT_PATH' or len(row['guided_sha256'])!=36
                    or len(row['solver_returns'])!=36 or row['actions'][:7]!=['DD']*7
                    or row['actions'][-1]!='DD' or row['counters']!=list(range(0,70,2))+[0]
                    or row['origins'] or len(row['P0_roundtrips'])!=4
                    or any(not r['complete_additional_state_restored'] or not r['physical_state_restored'] for r in row['P0_roundtrips'])
                    or row['conditions_before']!=row['conditions_after']
                    or row['condition_fields_before']!=row['condition_fields_after']
                    or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                    or c['complete_pairs']!=36
                    or row['vector_artifact']['tensor_sha256']['guided']!=row['guided_list_sha256']
                    or row['vector_artifact']['tensor_sha256']['final_latent']!=row['final_latent_sha256']):
                raise ValueError('Dynamic full36 output/state/conditions binding differs')
            if method=='SOURCE_RA':
                if len(c['source_RA_history'])!=36 or len(c['actual_original_plus_candidate_heads'])!=72:
                    raise ValueError('Original RA controller scope or head cost differs')
                continue
            a=d['A_readout']
            if (not d['source_risk_RA_policy_implemented'] or len(d['source_policy_history'])!=36
                    or [h['action']*2 for h in d['source_policy_history']]!=row['actions']
                    or d['fixed_schedule_used_for_dynamic_choice'] or d['teacher_calls'] or a['teacher_calls']
                    or len(c['actual_original_plus_candidate_heads'])!=72+a['extra_candidate_heads']
                    or len(a['history'])!=36 or row['own_history']!=d['history']):
                raise ValueError('Complete dynamic policy/readout/cost missing')
            for h in d['history']:
                p=h['source_policy']
                if (p['decision']['action']*2!=h['action'] or p['decision']['step']!=h['step']
                        or h['action']!='DD' and h['true_D_before']!=h['true_D_after']):
                    raise ValueError('Dynamic semantic action or true D history differs')
                if h['action']=='PP' and (p['creation_floor_proxy_after']<=0
                        or p['dense_anchor_after']!=p['decision']['state_before'][0]
                        or p['accumulated_interval_proxy_after']<p['decision']['state_before'][4]
                        or any(v['RA_zero_risk_reset_allowed'] or v['kind']!='P' for v in h['working_sources'])):
                    raise ValueError('P falsely became zero-risk D or reset interval history')
                if h['action']=='DD' and (p['creation_floor_proxy_after']!=0
                        or p['accumulated_interval_proxy_after']!=0 or p['dense_anchor_after']!=h['step']):
                    raise ValueError('Actual dense controller commit missing')
                ah=h['A_readout']
                if (ah['step']!=h['step'] or ah['action']!=h['action']
                        or ah['shared_alpha']!=alpha_at(a['method'],h['step'])
                        or ah['C_or_P_observation_updates_D_anchor']
                        or h['action']=='PP' and (ah['extra_heads']
                            or ah['branch_status']!=['P_NOT_ACTUAL_D']*2)):
                    raise ValueError('Dynamic A strength or semantic D observer differs')
                actual=[v for v in c['Linear_inputs'] if v['step']==h['step']]
                records=h['actual_projection_records']
                if h['action']=='CC':
                    if actual or records:raise ValueError('C secretly executed deep MLP')
                elif (len(records)!=8 or len(actual)!=16 or any(
                        sum(v['layer']==r['layer'] and v['slot']==r['slot']
                            and v['rows']==r['actual_MLP_rows'] for v in actual)!=2 for r in records)):
                    raise ValueError('Actual per-layer pair Linear rows differ from dynamic work')
    return {'complete_paths':32,'solver_updates':1152,'normal_net_calls':2304,
            'dynamic_outputs_enter_ordinary_full_UniPC':True,'teacher_calls':0,
            'Cosmos_or_video_quality_or_clean_speed_claim':False}


def derive(factory):
    source=dedent(inspect.getsource(p0._derive))
    changes=[('planned_parent_paths=52,planned_origins=0','planned_parent_paths=32,planned_origins=0'),
             ("calibration_collection_policy='P0_FIXED_D6_CHAIN_INTEGRATION'",
              "calibration_collection_policy='EXPLICIT_SOURCE_AWARE_DYNAMIC_POLICY'")]
    changed=source
    for old,new in changes:
        if changed.count(old)!=1:raise ValueError('Original full sampler derivation differs')
        changed=changed.replace(old,new)
    inverse=changed
    for old,new in reversed(changes):inverse=inverse.replace(new,old)
    if inverse!=source or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(source)):
        raise ValueError('Dynamic guarded sampler changed outside scope/policy declaration')
    ns={**p0._derive.__globals__,'_owner':factory,'METHODS':METHODS,'P_STEPS':(),
        'verify_batch':verify_batch,'__file__':__file__}
    exec(compile(changed,__file__+'#ordinary-dynamic-derivation','exec'),ns)
    batch,proof=ns['_derive']()
    return batch,{**proof,'original_P0_derivation_inverse_AST_equal':True,
                  'dynamic_derivation_explicit_sites':2,'complete_new_method_scope':list(METHODS),
                  'no_fixed_P_positions_in_dynamic_batch':True}


def run_batch(*args,calibration,policy_specs,**kwargs):
    if set(policy_specs)!=set(METHODS):raise ValueError('All explicit policy parameter bindings required')
    def factory(model,method,context,runtime,wc,rf):
        spec=policy_specs[method]
        if method=='SOURCE_RA':
            return SourceRAOwner(model,context=context,runtime=runtime,wc=wc,rf=rf,
                                 calibration=calibration,threshold=spec['threshold'])
        return DynamicSamplingOwner(model,method=method,context=context,runtime=runtime,wc=wc,rf=rf,
                                    calibration=calibration,spec=spec)
    batch,proof=derive(factory)
    result=batch(*args,**kwargs)
    return result


def audit_vectors(state,root,loader,expected_shape):
    verify_batch(state)
    root=Path(root).resolve();files=[];partial_refs=RA_refs=OFF_refs=0
    for request in state['requests']:
        loaded={}
        for row in request['paths']:
            art=row['vector_artifact'];p=Path(art['path']).resolve()
            if (not p.is_relative_to(root) or p.suffix!='.pt' or p.stat().st_size!=art['bytes']
                    or hashlib.sha256(p.read_bytes()).hexdigest()!=art['sha256']):
                raise ValueError('Changed or truncated dynamic vector artifact')
            x=loader(p,map_location='cpu',weights_only=True)
            if (set(x)!={'guided','final_latent'} or len(x['guided'])!=36
                    or any(list(t.shape)!=expected_shape or t.dtype!=torch.float32
                        or not bool(torch.isfinite(t).all()) for t in x['guided']+[x['final_latent']])
                    or {k:p0.tree_digest(v) for k,v in x.items()}!=art['tensor_sha256']
                    or [p0.tree_digest(t) for t in x['guided']]!=row['guided_sha256']):
                raise ValueError('Actual dynamic vectors differ from complete receipt')
            loaded[row['collect']]=x;files.append({'path':str(p),'bytes':art['bytes'],'sha256':art['sha256']})
        for a,b in [('SOURCE_RA','DYNAMIC_NO_P'),('CPD','A_CPD_OFF'),('CPD','REF_CPD')]:
            x,y=loaded[a],loaded[b]
            for v,w in zip(x['guided']+[x['final_latent']],y['guided']+[y['final_latent']]):
                if b=='REF_CPD':torch.testing.assert_close(v,w,rtol=1e-5,atol=2e-6)
                elif not torch.equal(v,w):raise ValueError('No-P RA or A OFF full trajectory parity differs')
        RA_refs+=1;OFF_refs+=1;partial_refs+=1
    if len(files)!=32 or {str(p.resolve()) for p in root.rglob('*.pt')}!={v['path'] for v in files}:
        raise ValueError('Complete dynamic vector set missing or extra')
    return {'files':files,'actual_guided_reloaded':1152,'actual_latents_reloaded':32,
        'full_GEMM_partial_trajectory_references':partial_refs,'original_RA_trajectory_references':RA_refs,
        'A_OFF_trajectory_references':OFF_refs,'real_quality_or_clean_speed_claim':False}
