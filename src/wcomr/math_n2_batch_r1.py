"""Complete nine-method CAL comparison through ordinary guarded Inference."""
import copy
import functools

from . import clean_speed20_r1 as clean
from .math_n2_sampling_owner_r1 import MathSamplingOwner
from .source_aware_current_birth_sampling_r2 import CurrentBirthSamplingOwner

METHODS=('NATIVE','RA','A_NO_P','NONZERO_CPD','P_OFF','SOURCE_FIXED','SOURCE_H1','SOURCE_H2','H2_P_TO_D')
RUN='wc-math-n2-source-sigma-full36-r1'
CARD='WC-MATH-N2-SOURCE-SIGMA-FULL36-R1-20261012-A'

def matrix(scenes):
    if len(scenes)!=4 or len(set(scenes))!=4:raise ValueError('All four fixed CAL requests required')
    rows=[]
    for rep in (1,2):
        for method in METHODS:
            rows.append({'id':f'warm_{rep}_{method}','scene':scenes[0],'method':method,
                         'section':'WARMUP','round':rep})
    for index,scene in enumerate(scenes):
        order=METHODS if index%2==0 else METHODS[:7][::-1]+METHODS[7:]
        for method in order:
            rows.append({'id':f'timed_{index}_{method}','scene':scene,'method':method,
                         'section':'TIMED','round':1})
    assert len(rows)==54 and sum(r['section']=='TIMED' for r in rows)==36
    return rows

def replace_P_mask(history):
    mask=[d.reason.rsplit(':',1)[-1] if d.reason.startswith('MATH_EVENT_') else d.action for d in history]
    if len(mask)!=36:raise ValueError('Already completed same-request H2 history required')
    return ['D' if a=='P' else a for a in mask]

def execute(inference,sample,method,*,parameters,previous_H2_plan=None,**kwargs):
    if method not in METHODS:raise ValueError('One registered complete method required')
    holder={};factory=CurrentBirthSamplingOwner
    if method=='NONZERO_CPD':
        def factory(*a,**kw):
            kw['method']='CPD';o=CurrentBirthSamplingOwner(*a,**kw);holder['owner']=o;return o
    elif method not in ('NATIVE','RA','A_NO_P'):
        options={'math_parameters':parameters,'source_mode':'P_OFF' if method=='P_OFF' else 'FUSION',
                 'horizon':None if method in ('P_OFF','SOURCE_FIXED') else 1 if method=='SOURCE_H1' else 2}
        if method=='H2_P_TO_D':
            if previous_H2_plan is None:raise ValueError('Full H2 plan required before fixed control')
            options['fixed_control_plan']=previous_H2_plan
        def factory(*a,**kw):
            o=MathSamplingOwner(*a,**options,**kw);holder['owner']=o;return o
    mapped=method if method in ('NATIVE','RA','A_NO_P') else 'KEEP_A_P'
    with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
        result=clean.execute(inference,sample,mapped,**kwargs)
    result['bridge_method']=result['method'];result['method']=method
    owner=holder.get('owner')
    plan=None
    if owner:
        result['source_history']=copy.deepcopy(owner.deployment.history)
        result['method_fingerprint']=parameters['fingerprint']
        result['online_teacher_calls']=0
        if method=='SOURCE_H2':plan=replace_P_mask(owner.controller.history)
        if method=='H2_P_TO_D' and 'PP' in result['actions']:raise ValueError('Fixed P-to-D control executed P')
    return result,plan
