"""Read-only W3 teacher/feature audit, separate from deployed H1 decisions."""
import math

import numpy as np
import torch

from .w3_causal_trend_r1 import CausalHistory,Observation,SameStateLabel
from .w3_label64_h1_owner_r1 import STEPS
from .w3_actual_clock_replay_r1 import validate_clock


def full_matrix(requests):
    if len(requests)!=8 or len({r['name'] for r in requests})!=8:raise ValueError('All eight frozen development requests required')
    rows=[]
    for section,samples in (('WARMUP',requests[:1]),('FORMAL',requests)):
        for sample in samples:
            for kind in ('BASELINE','DIAGNOSTIC'):
                rows.append({'id':str(len(rows))+'_'+section+'_'+kind,'scene':sample['name'],'section':section,
                    'kind':kind,'status':'NOT_RUN','planned_ordinary_pairs':36,
                    'planned_extra_pairs':24 if kind=='DIAGNOSTIC' else 0,
                    'planned_label_steps':list(STEPS) if kind=='DIAGNOSTIC' else []})
    if len(rows)!=18 or sum(r['planned_ordinary_pairs']+r['planned_extra_pairs'] for r in rows)!=864:
        raise ValueError('Complete formal/warm18/864 denominator changed')
    return rows


def audit_features(rows,*,clock):
    """Recompute all T1/T2 prefixes from ordinary pre-action observations."""
    validate_clock(clock)
    if len(rows)!=36 or [r['step'] for r in rows]!=list(range(1,37)):
        raise ValueError('All ordinary36 causal history rows required')
    observations=[Observation(**r['observation']) for r in rows]
    h=CausalHistory(observations[0].prompt,observations[0].seed,window=4);features=[]
    for row,o in zip(rows,observations):
        if (o.step!=row['step'] or o.sigma!=clock['sigmas'][o.step-1]
                or row.get('ordinary_parent_only') is not True or row.get('teacher_or_candidate_history_used') is not False):
            raise ValueError('Actual ordinary pre-action clock/source-only input required')
        if row.get('scheduler_pre_step_index') is None:
            if o.step!=1 or row.get('sigma_from_actual_first_grid_before_init') is not True:
                raise ValueError('Only original first solver call may precede index initialization')
        elif row['scheduler_pre_step_index']!=o.step-1 or row['sigma_from_actual_first_grid_before_init']:
            raise ValueError('Actual current solver index differs')
        fs=h.push(o)
        for model,f in fs.items():
            actual=row['features'].get(model,{})
            if (tuple(actual.get('names',()))!=f.names or tuple(actual.get('values',()))!=f.values
                    or tuple(actual.get('prefix_steps',()))!=f.prefix_steps):
                raise ValueError('Saved feature differs from causal ordinary prefix: '+model)
        features.append(fs)
    return features


def paired_error(pair,teacher):
    """As-executed FP32 guided vector; independent NumPy FP64 Gram check."""
    errors=tuple(p-t for p,t in zip(pair,teacher))
    guided=8*errors[0]-7*errors[1]
    actual=guided.double().square().mean().item()
    ec,eu=(v.detach().cpu().numpy().astype(np.float64) for v in errors)
    mc=float(np.mean(ec*ec));mu=float(np.mean(eu*eu));cross=float(np.mean(ec*eu))
    independent=float(np.mean((8*ec-7*eu)**2));gram=64*mc+49*mu-112*cross
    if not math.isclose(independent,gram,rel_tol=1e-8,abs_tol=max(1e-12,(64*mc+49*mu)*1e-12)):
        raise ValueError('Independent CFG Gram identity failed')
    reference=8*ec-7*eu;observed=guided.double().cpu().numpy()
    rounding_energy=float(np.mean((observed-reference)**2))
    rounding_cap=16*np.finfo(np.float32).eps**2*(64*mc+49*mu)+1e-18
    # Cauchy-Schwarz bounds the difference of squared norms without a
    # relative-error rejection near a strongly cancelling guided vector.
    mse_difference_bound=2*math.sqrt(independent*rounding_energy)+rounding_energy
    if (rounding_energy>rounding_cap or abs(actual-independent)>mse_difference_bound+max(1e-12,independent*1e-12)):
        raise ValueError('FP32/independent64 guided coordinates exceed numerical bound')
    return {'as_executed_guided_MSE':actual,'independent64_guided_MSE':independent,
        'independent_CFG_Gram':[mc,mu,cross],'FP32_FP64_delta':actual-independent,
        'rounding_energy':rounding_energy,'MSE_roundoff_difference_bound':mse_difference_bound}


def audit_label(payload,record,features,parent_history,*,expected_shape,provenance):
    step=record['step']
    if step not in STEPS or len(features)!=36 or len(parent_history)!=36:raise ValueError('Original8 label steps and full parent history required')
    f=features[step-1]['T1'];o=f.observation;h=parent_history[step-1];choice=h['joint_decision']
    state=record['pre_action_state'];age=step-state[2] if state[1] is not None and state[2] is not None else None
    if (record['label_provenance']!=provenance or record['candidate_or_teacher_committed_to_parent']
            or tuple(record['pre_action_state'])!=tuple(choice['state_before']) or choice['step']!=step
            or record['parent_action']!=h['action'] or record['parent_readout']!=h['A_readout']['readout_action']
            or record['feature_state_id']!=o.state_id or record['sigma']!=o.sigma
            or o.source_kind!=state[1] or o.source_age!=age
            or o.gain!=choice['gain'] or not o.state_id.startswith(record['input_sha256']+':')):
        raise ValueError('Label and ordinary actual input/source/state identity differ')
    if record['status']=='UNKNOWN_ORIGINAL_SUPPORT_NOT_RELAXED':
        if (payload is not None or record['label'] is not None or record['artifact'] is not None or record['extra_pairs']
                or o.calibration_supported or record.get('trials') or record.get('serial_restores')):
            raise ValueError('Unknown original support cannot have a fabricated teacher')
        return {'step':step,'status':record['status'],'labels_available':False,'denominator_kept':True}
    if (record['status']!='COMPLETE_SAME_STATE_CAD_LABEL_NOT_ONLINE_VALUE' or record['extra_pairs']!=3
            or not record['same_state_snapshot_and_parent_restore_verified'] or not record['teacher_never_used_in_feature_inputs']
            or len(record['serial_restores'])!=3 or not o.calibration_supported or o.protected):
        raise ValueError('All three supported noncommitting CAD restores required')
    for restore in record['serial_restores']:
        if len(restore)!=2 or [r['stage'] for r in restore]!=['physical_restore','owned_restore']:
            raise ValueError('Physical and owned restore accounting required each trial')
        if any(r['original_pre_snapshot_two_copy_gate_unchanged'] is not True for r in restore):
            raise ValueError('Original combined snapshot gate changed')
    trials=record['trials']
    if [t['kind'] for t in trials]!=['C','A','D'] or any(t['actual_readout']!=t['kind']
            or t['actual_action']!=('CC' if t['kind'] in ('C','A') else 'DD')
            or not math.isfinite(t['full_pair_seconds']) or t['full_pair_seconds']<0 for t in trials):
        raise ValueError('Three actual semantic CAD computations required')
    if set(payload)!={'C','A','D','actual_latent','timestep'}:raise ValueError('Full8 point tensors required')
    for kind in ('C','A','D'):
        p=payload[kind]
        if not isinstance(p,tuple) or len(p)!=2:raise ValueError('Two actual branch velocities required')
        if any(not isinstance(t,torch.Tensor) or list(t.shape)!=list(expected_shape) or t.dtype!=torch.float32
                or t.device.type!='cpu' or not torch.isfinite(t).all() for t in p):
            raise ValueError('Finite CPU FP32 post-RF matching geometry required')
    latent,time=payload['actual_latent'],payload['timestep']
    if list(latent.shape)!=list(expected_shape) or not torch.isfinite(latent).all() or time.numel()!=1 or not torch.isfinite(time).all():
        raise ValueError('Original latent/time coordinates missing')
    losses={kind:paired_error(payload[kind],payload['D']) for kind in ('C','A','D')}
    label=SameStateLabel(**record['label'])
    if label.provenance!=provenance:raise ValueError('Teacher provenance changed')
    for field,kind in (('q_C','C'),('q_A','A')):
        if not math.isclose(getattr(label,field),losses[kind]['as_executed_guided_MSE'],rel_tol=1e-10,abs_tol=1e-12):
            raise ValueError('Saved teacher error differs from raw '+kind+' branch velocities')
    target=label.target(f)
    if not np.allclose(target,np.asarray(record['gain_squared_targets']),rtol=1e-10,atol=1e-12):
        raise ValueError('Actual H1 gain must be applied exactly once to coherent targets')
    return {'step':step,'status':'RAW_CAD_AND_ORDINARY_PREFIX_AUDITED','losses':losses,
        'gain_squared_targets':target.tolist(),'all8_point_tensors_read':True,'labels_available':True,
        'source_refreshed':False,'not_video_endpoint_or_controller_improvement':True}
