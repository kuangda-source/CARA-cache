"""Conditional fixed-layout 46-path video requests and original preservation.

No dispatch, fitting or automatic scientific acceptance. Uses the already
tested gain owner, original Native and original S25-C reference adapters.
"""
import copy
import json
import time
from pathlib import Path

import torch
from .innovation_gain_r1 import gains_checked
from .innovation_gain_deployment_r1 import execute as gain_execute, ROLES
from .policy_generator_r1.exploration_requests import Requests as ReferenceRequests
from .policy_generator_r1.frozen_request_arguments import request_variant
from .policy_generator_r1.production_sampling import complete_request_seconds
from .policy_generator_r1.continuation_preparation import TIME_BOUNDARY
from .policy_generator_r1.production_evidence import artifact, verify_artifact
from .gpu_budget_pool_v2 import atomic_json
from .scout_readout_v22 import D_STEPS, PARENT_FINGERPRINT


class Requests:
    def __init__(self, *, inference, samples, profile, original_card, gains, common,
                 table_parameters, previous_parameters, model_identity):
        self.inference, self.samples, self.common = inference, samples, common
        self.gains = {r:gains_checked(gains[r]) for r in ('IG_SCALAR', 'IG_BAND')}
        if self.gains['IG_SCALAR'][0] != self.gains['IG_SCALAR'][1]:raise ValueError('Scalar must share its gain')
        self.tables, self.prior, self.model_identity = table_parameters, previous_parameters, model_identity
        self.references = ReferenceRequests(inference=inference, samples=samples, profile=profile,
            roles={'NATIVE35':original_card['roles']['NATIVE35'],
                   'S25_C_REFERENCE':original_card['roles']['S25_C']},
            schedules=original_card['schedules'], common=common)
        self.seen = set()

    def __call__(self, slot, directory):
        if slot['id'] in self.seen:raise ValueError('Original video slot cannot be retried')
        if slot['seed'] != 0 or slot['requested_steps'] != 35 or slot['actual_updates'] != 36:
            raise ValueError('Frozen full36/seed0 request required')
        self.seen.add(slot['id'])
        role=slot['role']
        if role in ('NATIVE35', 'S25_C_REFERENCE'):
            self.references.common=dict(self.common)
            result=self.references(slot,directory)
        elif role in ROLES:
            sample=request_variant(self.samples[slot['member']],seed=0,num_steps=35)
            result=gain_execute(self.inference,sample,role=role,gains=self.gains.get(role),
                feature_context=(slot['member'],self.model_identity,PARENT_FINGERPRINT),
                table_parameters=self.tables,previous_parameters=self.prior,
                output=directory,**self.common)
            result.update(timing_boundary=TIME_BOUNDARY,
                full_request_seconds=complete_request_seconds(result) if result.get('core_seconds') else None)
        else:raise ValueError('Unregistered video role')
        result['video_role']=role
        return result


def audit_result(slot,result):
    if result['status'] != 'COMPLETE' or result['solver_steps'] != 36 or result['guided_pairs'] != 36:
        raise ValueError('Refusal/failure/incomplete full36 original retained')
    if result['audit'] or result['in_timing_guided_copies'] or result['in_timing_hashes']:
        raise ValueError('Video timing must use the uninstrumented complete request')
    if result['timing_boundary'] != TIME_BOUNDARY or result['full_request_seconds'] != complete_request_seconds(result):
        raise ValueError('Complete request clock differs')
    role=slot['role']
    if role in ROLES:
        history=result['gain_deployment_history']
        if len(history)!=36 or result['teacher_calls']!=0 or result['online_fitting']:
            raise ValueError('Free-running history/teacher identity changed')
        for step,row in enumerate(history,1):
            dense=step in D_STEPS
            heads=2 if dense or role=='WC_C' else 4
            if (row['step']!=step or row['role']!=role or row['true_anchor_write']!=dense
                    or row['actual_head_calls']!=heads or row['teacher_calls']!=0 or row['fallback_reason'] is not None):
                raise ValueError('Original fixed mask, head count or finite support changed')
            if not dense and role!='WC_C' and row['alpha']!=(1. if step<25 else .5):
                raise ValueError('Original alpha changed')
    elif role=='NATIVE35':
        if result['full_block_calls']!=[72,72] or result['cache_installed']:
            raise ValueError('Native full-block witness changed')
    else:
        if any(h['fallback_reason'] is not None for h in result['semantic_history']):
            raise ValueError('Reference fallback retained but cannot pass fixed-mask comparison')


def collect(protocol, root, execute, save):
    matrix=protocol['matrix'];root=Path(root)
    if (len(matrix)!=46 or len({s['id'] for s in matrix})!=46
            or sum(s['section']=='QUALITY' for s in matrix)!=36
            or sum(s['section']=='WARMUP' for s in matrix)!=4
            or sum(s['section']=='TIMING_REPEAT' for s in matrix)!=6):
        raise ValueError('Full predeclared46 matrix required')
    state=dict(status='B2_GENERATION_RUNNING',rows=[dict(slot=copy.deepcopy(s),status='NOT_REACHED') for s in matrix])
    save(state)
    try:
        for row in state['rows']:
            slot=row['slot'];directory=root/slot['id']
            if directory.exists():raise FileExistsError('Original video directory already exists')
            row['status']='RUNNING';save(state);start=time.time()
            result=execute(slot,directory)
            result.update(started_unix=start,ended_unix=time.time())
            latent=result.pop('final_latent',None);guided=result.pop('guided',None)
            if guided is not None:raise ValueError('Unregistered per-step copies on video path')
            if latent is not None:
                with (directory/'final-latent.pt').open('xb') as f:torch.save(dict(final_latent=latent),f)
                result['final_latent_artifact']=artifact(directory/'final-latent.pt',root)
            if result['status']=='COMPLETE':result['video_artifact']=artifact(result['video_path'],root)
            atomic_json(directory/'request.json',dict(slot=slot,result=result))
            result['request_artifact']=artifact(directory/'request.json',root);row['result']=result;save(state)
            audit_result(slot,result)
            if latent is None:raise ValueError('Complete final latent required')
            row['status']='COMPLETE';save(state)
            del latent,result
        state['status']='B2_COMPLETE46_PENDING_VIDEO_SCORES'
        return state
    except BaseException as exc:
        row.update(status='TECH_FAILED',error_type=type(exc).__name__,error=str(exc))
        state['status']='B2_FAILED_ORIGINAL46_DENOMINATOR_RETAINED';raise
    finally:save(state)


def repeat_controls(state, root, rgb_digest):
    if state['status']!='B2_COMPLETE46_PENDING_VIDEO_SCORES':raise ValueError('Complete generation required')
    controls=[]
    for row in state['rows']:
        slot=row['slot']
        if slot['section']!='TIMING_REPEAT':continue
        reference=next(r for r in state['rows'] if r['slot']['section']=='QUALITY' and all(
            r['slot'][k]==slot[k] for k in ('member','role','seed')))
        left,right=reference['result'],row['result']
        tensors=[torch.load(verify_artifact(r['final_latent_artifact'],root),map_location='cpu',weights_only=True)['final_latent'] for r in (left,right)]
        if not torch.equal(*tensors):raise ValueError('Repeated final latent differs')
        rgb=[rgb_digest(verify_artifact(r['video_artifact'],root)) for r in (left,right)]
        if rgb[0]!=rgb[1]:raise ValueError('Repeated decoded video differs')
        controls.append(dict(first=reference['slot']['id'],repeat=slot['id'],final_latent_equal=True,RGB_equal=True))
    if len(controls)!=6:raise ValueError('All six repeated controls required')
    return controls
