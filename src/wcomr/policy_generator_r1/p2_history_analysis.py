"""Recompute own-state diagnostic errors from original paired branch tensors."""
import hashlib
import math
from pathlib import Path
from .continuation_preparation import require
from .evaluation_analysis import spearman

LABELS=('C','A_HALF','A_ONE')


def compare(actual,other):
    require(set(actual)==set(other)==set(LABELS),'Complete three-action comparison required')
    require(all(math.isfinite(x) and x>=0 for x in [*actual.values(),*other.values()]),'Finite nonnegative losses required')
    best_actual={k for k,v in actual.items() if v==min(actual.values())}
    best_other={k for k,v in other.items() if v==min(other.values())}
    return dict(Spearman_with_average_ties=spearman([actual[k] for k in LABELS],[other[k] for k in LABELS]),
        best_actual=sorted(best_actual),best_other=sorted(best_other),best_set_intersection=sorted(best_actual&best_other),
        tied_other_choice_regret_range=[min(actual[k] for k in best_other)-min(actual.values()),max(actual[k] for k in best_other)-min(actual.values())],
        absolute_difference={k:actual[k]-other[k] for k in LABELS},
        ratio={k:actual[k]/other[k] if other[k] else None for k in LABELS})


def audit_record(record,*,root,teacher_stat=None):
    import torch
    from ..mid_coverage import tree_digest
    from ..policy_interval_readout_r1 import guided
    path=Path(record['branch_artifact']['path']);root=Path(root).resolve()
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),'Original branch artifact must be inside own output')
    rawbytes=path.read_bytes();require(hashlib.sha256(rawbytes).hexdigest()==record['branch_artifact']['sha256'] and len(rawbytes)==record['branch_artifact']['bytes'],'Original branch bytes differ')
    raw=torch.load(path,map_location='cpu',weights_only=False)
    for key in ('point','input_sha256','anchor_identity','parent_state_before_sha256'):
        require(raw[key]==record[key],'Diagnostic identity differs: '+key)
    require(raw['Phi_key']=='A_ONE' and record['parent_state_before_after_equal'] is True and record['shadow_writes_parent'] is False,'Parent noninterference missing')
    require(set(raw['windows'])=={'actual','adjacent'} and len(raw['D'])==2,'Both windows and both D branches required')
    shape=raw['D'][0].shape;mse={}
    for window,values in raw['windows'].items():
        require(set(values)==set(LABELS),'Missing action branch tensors')
        require(all(len(pair)==2 and all(v.shape==shape and bool(torch.isfinite(v).all()) for v in pair) for pair in [raw['D'],*values.values()]),'Nonfinite or inconsistent branch tensors')
        mse[window]={label:float((guided(pair).double()-guided(raw['D']).double()).square().mean()) for label,pair in values.items()}
    require(mse==record['guided_MSE'],'Saved local errors disagree with original branch outputs')
    require(all(torch.equal(a,b) for a,b in zip(raw['windows']['actual']['A_ONE'],raw['windows']['adjacent']['A_ONE'])),'Phi depends on older window')
    teacher=None
    if teacher_stat is not None:
        require(teacher_stat['source']==raw['point']['source'] and teacher_stat['target']==raw['point']['target'],'Teacher cell must share (s,t)')
        e,ed,d=teacher_stat['e2'],teacher_stat['ed'],teacher_stat['d2']
        proxy={k:e+2*a*ed+a*a*d for k,a in zip(LABELS,(0.,.5,1.))}
        teacher=dict(basis='TEACHER_GUIDED_QUADRATIC_PROXY_NOT_NEW_OWN_TRAJECTORY',loss=proxy,comparison=compare(mse['actual'],proxy))
    return dict(point=raw['point'],input_sha256=raw['input_sha256'],anchor_identity=raw['anchor_identity'],
        guided_MSE=mse,history_only=compare(mse['actual'],mse['adjacent']),teacher_to_own_state=teacher,
        branch_outputs_sha256=tree_digest(raw['windows']),accepted_branch_bytes=True,
        independent_prompt_count=1,clean_deployment_timing=False,policy_update_allowed=False)
