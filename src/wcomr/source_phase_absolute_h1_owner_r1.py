"""Reuse the exact physical two-branch execution and source-fusion readout."""
import functools
from dataclasses import asdict
from .math_n2_sampling_owner_r1 import MathSamplingOwner,MathDeployment
from .source_aware_phase_sampling import bind_globals
from .source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller


class SourcePhaseH1Deployment(MathDeployment):
    def commit(self,*a,**kw):
        result=super().commit(*a,**kw);row=self.history[-1];choice=self.controller.history[-1]
        row['joint_decision']=asdict(choice)
        row['source_policy'].update(proxy_definition='ORIGINAL_ROOT_PI0_STATE_WITH_SEPARATE_ABSOLUTE_H1_OBJECTIVE',
            creation_floor_unit='WC_PAID_DELTA_Y_ROOT_PROXY_EMPIRICAL_TRANSFER',
            root_accumulated_used_for_pi0_fallback_only=True,absolute_error_written_to_root_accumulator=False,latent_or_UniPC_history_reset=False,
            event_math=self.controller.query_basis(choice))
        return result


class SourcePhaseH1Owner(MathSamplingOwner):
    def __init__(self,*a,table_parameters,**kw):
        if kw.get('horizon')!=1 or kw.get('source_mode','FUSION')!='FUSION':
            raise ValueError('Full four-action H1 and source-consistent actual readout required')
        ctor=bind_globals(MathSamplingOwner.__init__,{'EventController':functools.partial(SourcePhaseH1Controller,table_parameters=table_parameters),
            'MathDeployment':SourcePhaseH1Deployment})
        ctor(self,*a,**kw)

    def installation(self):
        return super().installation()+('SOURCE_PHASE_ABSOLUTE_H1_OWNER_R1',self.controller.table_parameters['fingerprint'])
