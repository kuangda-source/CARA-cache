"""Actual point tensor/formula/price audit. CPU labels, never online inputs."""
import math

import torch

from .p_acr_profile20_owner_r1 import trial_plan


def paired_loss(pair,teacher):
    ec=pair[0].double()-teacher[0].double();eu=pair[1].double()-teacher[1].double()
    mc=ec.square().mean().item();mu=eu.square().mean().item();cross=(ec*eu).mean().item()
    q=(8*ec-7*eu).square().mean().item()
    if not math.isclose(q,64*mc+49*mu-112*cross,rel_tol=1e-7,abs_tol=1e-10):
        raise ValueError('Actual guided loss differs from CFG Gram reconstruction')
    return {'absolute_guided_MSE':q,'CFG_gram':[mc,mu,cross]}


def audit_point(payload,record,config,coefficients,parent_history,expected_shape):
    expected={'C','A','D','actual_latent','timestep'}|{d+'_REP'+str(r) for d in ('Pc','Pu') for r in range(4)}
    expected|={'FC_STYLE_'+d+'_REP'+str(r) for d in ('Pc','Pu') for r in range(4)}
    if set(payload)!=expected:raise ValueError('All21 actual point entries required')
    point=record['point']
    if point not in config['states'] or record['coefficients_fingerprint']!=config['coefficients_fingerprint']:
        raise ValueError('Actual preselected point/coefficient identity changed')
    if (record['parent_pre_action'][1]!='D' or record['parent_pre_action'][2]!=point['expected_source_birth']
            or point['step']-record['parent_pre_action'][2]!=point['expected_source_age']
            or record['parent_readout']!=point['expected_H1_readout']):
        raise ValueError('Actual H1 source/action/age differs')
    if not record['all20_trials_restored'] or record['candidate_or_teacher_committed_to_parent'] or len(record['serial_restores'])!=20:
        raise ValueError('All20 completed noncommitting restores required')
    trials=record['trials']
    if [(t['kind'],t['repetition'],t['section']) for t in trials]!=list(trial_plan()):
        raise ValueError('Complete warm/forward/reverse/forward price order required')
    for t in trials:
        if (t['actual_heads'] is not None or t['actual_Linear_observers'] is not None
                or t['observers']['pure_observers_suspended']!=9 or not t['per_action_compiler_preparation_is_charged']
                or not t['snapshot_hash_restore_IO_outside_timer']
                or any(not math.isfinite(t[k]) or t[k]<0 for k in ('full_pair_seconds','action_preparation_seconds','charged_action_seconds'))
                or t['charged_action_seconds']!=t['full_pair_seconds']+t['action_preparation_seconds']):
            raise ValueError('Quiet algorithm quote or preparation cost changed')
    for name,value in payload.items():
        if name in ('actual_latent','timestep'):continue
        if not isinstance(value,tuple) or len(value)!=2:raise ValueError('Two actual branch velocities required')
        for tensor in value:
            if (not isinstance(tensor,torch.Tensor) or list(tensor.shape)!=list(expected_shape)
                    or tensor.dtype!=torch.float32 or not bool(torch.isfinite(tensor).all())):
                raise ValueError('Actual post-RF velocity geometry/dtype/nonfinite')
    if (list(payload['actual_latent'].shape)!=list(expected_shape)
            or not bool(torch.isfinite(payload['actual_latent']).all())
            or payload['timestep'].numel()!=1 or not bool(torch.isfinite(payload['timestep']).all())):
        raise ValueError('Actual latent/noise coordinate changed')
    cell='D_'+('EARLY' if point['step']<25 else 'LATE');gains=coefficients['cells'][cell]
    for direction,coefficient in (('Pc',gains['Pc_eta']),('Pu',gains['Pu_zeta'])):
        base=payload['A'];D=payload['D'];side=0 if direction=='Pc' else 1
        innovation=D[side]-base[side]
        rebuilt=(D[0],base[1]+coefficient*innovation) if direction=='Pc' else (base[0]+coefficient*innovation,D[1])
        for rep in range(4):
            value=payload[direction+'_REP'+str(rep)]
            if any(not torch.equal(a,b) for a,b in zip(value,rebuilt)):
                raise ValueError('Stored single-branch correction differs from its actual innovation')
    losses={name:paired_loss(payload[name],payload['D']) for name in payload if name not in ('actual_latent','timestep')}
    for direction,field in (('Pc','Pc_eta'),('Pu','Pu_zeta')):
        repetitions=[t for t in trials if t['kind']==direction]
        if any(t['coefficient']!=gains[field] or t['actual_dense_branches']!=1 or t['paid_prefixes']!=2 or t['source_refresh'] for t in repetitions):
            raise ValueError('Real asymmetric computation/scope changed')
    choice=parent_history['joint_decision'];gain=choice['gain']
    if choice['step']!=point['step'] or gain is None or not math.isfinite(gain):
        raise ValueError('Actual H1 pre-action propagation coordinate required')
    formal={name:[t['charged_action_seconds'] for t in trials if t['kind']==name and t['section']=='TIMED']
        for name in ('C','A','D','Pc','Pu')}
    return {'point':point,'actual_sigma':record['sigma'],'actual_H1_gain':gain,'losses':losses,
        'formal_charged_seconds':formal,'preparation_costs':[{'kind':t['kind'],'rep':t['repetition'],'seconds':t['action_preparation_seconds']} for t in trials],
        'real_same_state_teacher_used_only_for_CPU_scoring':True,'source_refreshed':False,
        'all40_point_tensors_read':True,'not_video_endpoint_or_net_acceleration':True}
