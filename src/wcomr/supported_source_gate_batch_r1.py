"""Nine complete controls; previous N2 parameters remain original."""
import copy
from . import clean_speed20_r1 as clean
from .math_n2_batch_r1 import execute as previous_execute
from .supported_source_gate_owner_r1 import SupportedGateOwner

METHODS=('NATIVE','RA','A_NO_P','P_OFF','SOURCE_H1','SOURCE_H2',
         'SUPPORTED_GATE_H1','SUPPORTED_GATE_H2','PLUS_P_A_H2')
RUN='wc-supported-source-gate-full36-r1'
CARD='WC-SUPPORTED-SOURCE-GATE-FULL36-R1-20261012-A'

def matrix(scenes):
    if len(scenes)!=4 or len(set(scenes))!=4:raise ValueError('Four registered CAL requests required')
    rows=[]
    for rep in (1,2):
        for method in METHODS:rows.append({'id':f'warm_{rep}_{method}','scene':scenes[0],
            'method':method,'section':'WARMUP','round':rep})
    for index,scene in enumerate(scenes):
        for method in METHODS if index%2==0 else METHODS[::-1]:
            rows.append({'id':f'timed_{index}_{method}','scene':scene,
                'method':method,'section':'TIMED','round':1})
    return rows

def execute(inference,sample,method,*,parameters,previous_parameters,**kwargs):
    if method not in METHODS:raise ValueError('Registered nine-method scope required')
    if method not in METHODS[6:]:
        return previous_execute(inference,sample,method,parameters=previous_parameters,**kwargs)
    holder={}
    def factory(*a,**kw):
        owner=SupportedGateOwner(*a,math_parameters=parameters,
            horizon=1 if method=='SUPPORTED_GATE_H1' else 2,source_mode='FUSION',
            allow_P_A=method=='PLUS_P_A_H2',**kw)
        holder['owner']=owner;return owner
    with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
        result=clean.execute(inference,sample,'KEEP_A_P',**kwargs)
    owner=holder.get('owner');result['bridge_method']=result['method'];result['method']=method
    if owner:
        result['source_history']=copy.deepcopy(owner.deployment.history)
        result['method_fingerprint']=parameters['fingerprint'];result['online_teacher_calls']=0
    return result,None
