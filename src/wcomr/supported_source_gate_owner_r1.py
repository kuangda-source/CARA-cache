"""Fresh support-aware instances; all N2 physical readout/MLP code unchanged."""
import functools
from dataclasses import asdict

from .source_aware_phase_sampling import bind_globals
from .math_n2_sampling_owner_r1 import MathSamplingOwner,MathDeployment
from .supported_source_gate_control_r1 import SupportedGateController

class SupportedGateDeployment(MathDeployment):
    def commit(self,*args,**kwargs):
        value=super().commit(*args,**kwargs)
        self.history[-1]['source_policy']['proxy_definition']='AMPLITUDE_GAIN_SQUARED_NORMALIZED_GUIDED_MSE_PROXY'
        self.history[-1]['joint_decision']=asdict(self.controller.history[-1])
        return value

class SupportedGateOwner(MathSamplingOwner):
    def __init__(self,*args,allow_P_A=False,**kwargs):
        if kwargs.get('horizon') not in (1,2) or kwargs.get('source_mode','FUSION')!='FUSION':
            raise ValueError('One fixed H1/H2, source minimum and optional P-A required')
        ctor=bind_globals(MathSamplingOwner.__init__,{'EventController':
            functools.partial(SupportedGateController,allow_P_A=allow_P_A),
            'MathDeployment':SupportedGateDeployment})
        ctor(self,*args,**kwargs)

    def installation(self):
        return super().installation()+('SUPPORTED_SOURCE_GATE_OWNER_R1',self.controller.allow_P_A)
