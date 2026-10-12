"""Four original strong controls and two actual absolute-H1 table candidates."""
import copy
from . import clean_speed20_r1 as clean
from .math_n2_batch_r1 import execute as previous_execute
from .source_phase_absolute_h1_owner_r1 import SourcePhaseH1Owner

METHODS=('NATIVE','RA','A_NO_P','P_OFF','TABLE_PHASE_H1','TABLE_POOLED_H1')


def execute(inference,sample,method,*,table_parameters,previous_parameters,**kw):
    if method not in METHODS:raise ValueError('Complete registered six-method CPU/development bridge required')
    if method in METHODS[:4]:return previous_execute(inference,sample,method,parameters=previous_parameters,**kw)
    group='SOURCE_PHASE' if method=='TABLE_PHASE_H1' else 'SOURCE'
    p=table_parameters[group];assert p['table_model']['grouping']==group
    holder={}
    def factory(*a,**kwargs):
        owner=SourcePhaseH1Owner(*a,table_parameters=p,math_parameters=previous_parameters,horizon=1,source_mode='FUSION',**kwargs)
        holder['owner']=owner;return owner
    with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
        result=clean.execute(inference,sample,'KEEP_A_P',**kw)
    owner=holder['owner'];result['bridge_method']=result['method'];result['method']=method
    result['source_history']=copy.deepcopy(owner.deployment.history)
    result['method_fingerprint']=p['fingerprint'];result['online_teacher_calls']=0
    return result,None
