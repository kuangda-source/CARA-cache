"""Read all six output pairs and reduce their true same-state CFG errors."""
import copy
import math

import torch

from . import e4c_source_age_tensor_audit_r1 as old
from .p_reference_same_state_owner_r1 import VARIANTS
from .mid_coverage import tree_digest


BASE_KEYS={'C','DENSE_SAME_STATE','candidate_latent','timestep'}
EXTRA_KEYS=set(VARIANTS)-{'D_REFERENCE_SCALAR'}


def audit(state,root,loader,expected_shape):
    view=copy.deepcopy(state);records={};independent=[];extra_tensors=0;D_checks=0
    for request in view['requests']:
        for row in request['paths']:
            for event in row['origins']:
                for branch in event['branches']:
                    for point in branch['age_points']:
                        art=point['artifact'];records[art['path']]=(event['event']['id'],branch['source'],point)
                        art['tensor_sha256']={k:v for k,v in art['tensor_sha256'].items() if k in BASE_KEYS}
    def read(path,**kwargs):
        nonlocal extra_tensors,D_checks
        values=loader(path,**kwargs)
        record=records.get(str(path))
        # Path equality is resolved independently by the inherited reader;
        # stored paths on this host may use the project's symlink spelling.
        if record is None:
            from pathlib import Path
            record=next((v for k,v in records.items() if Path(k).resolve()==path),None)
        if record is None:return values
        event,source,point=record
        if set(values)!=BASE_KEYS|EXTRA_KEYS:
            raise ValueError('All five readouts plus actual dense teacher required')
        original=next(p for req in state['requests'] for row in req['paths'] for e in row['origins']
            for b in e['branches'] for p in b['age_points'] if p['artifact']['path']==point['artifact']['path'])
        if {k:tree_digest(v) for k,v in values.items()}!=original['artifact']['tensor_sha256']:
            raise ValueError('Additional raw candidate output binding differs')
        dense=values['DENSE_SAME_STATE'];out={}
        for name in VARIANTS:
            pair=values['C'] if name=='D_REFERENCE_SCALAR' else values[name]
            if (len(pair)!=2 or any(t.device.type!='cpu' or t.dtype!=torch.float32
                    or list(t.shape)!=expected_shape or not torch.isfinite(t).all() for t in pair)):
                raise ValueError('Full finite FP32 candidate geometry required')
            ec,eu=[a-b for a,b in zip(pair,dense)]
            mse=(8*ec-7*eu).double().square().mean().item()
            saved=next(r for r in original['five_reference_readouts'] if r['variant']==name)['guided_moments']
            if not math.isclose(mse,saved['base_guided_MSE'],rel_tol=1e-12,abs_tol=1e-15):
                raise ValueError('Independent five-way guided error differs')
            out[name]=mse
            if name!='D_REFERENCE_SCALAR':extra_tensors+=2
        if source=='D':
            for a,b in (('P_REFERENCE_SCALAR','C'),('P_REFERENCE_UNIT','D_REFERENCE_UNIT')):
                if not all(torch.equal(x,y) for x,y in zip(values[a],values[b])):
                    raise ValueError('Actual D-source reference parity differs')
                D_checks+=2
        independent.append({'event':event,'source':source,'age':point['age'],
                            'same_state_guided_MSE':out})
        return {k:v for k,v in values.items() if k in BASE_KEYS}
    base=old.audit(view,root,read,expected_shape)
    if len(independent)!=24 or extra_tensors!=192 or D_checks!=48:
        raise ValueError('Whole24 points,192 extra tensors and48 D-source controls required')
    return {**base,'actual_tensors_reloaded':base['actual_tensors_reloaded']+extra_tensors,
        'actual_direct_tensor_comparisons':base['actual_direct_tensor_comparisons']+D_checks,
        'all_five_independent_error_records':independent,'actual_D_source_control_equalities':D_checks,
        'deployment_not_switched_to_winning_candidate':True}
