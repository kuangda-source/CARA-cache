"""New per-request readout/controller instances; pinned execution unchanged."""
import functools

from .source_aware_phase_sampling import bind_globals
from .source_aware_partial_sampling import DynamicSamplingOwner
from .source_aware_current_birth_sampling_r2 import CurrentBirthSamplingOwner,CurrentBirthDeployment
from .source_aware_current_birth_control_r1 import CurrentBirthCPDController
from .math_n2_event_control_r1 import EventController
from .math_n2_source_readout_r1 import SourceFusionReadout


class MathDeployment(CurrentBirthDeployment):
    def __init__(self,*args,math_parameters,source_mode,**kwargs):
        super().__init__(*args,**kwargs)
        self.readout=SourceFusionReadout(self,method='BETA1_ONE_PHASE',
            gamma=math_parameters['gamma'],mode=source_mode)

    def commit(self,*args,**kwargs):
        result=super().commit(*args,**kwargs)
        row=self.history[-1]
        if isinstance(self.controller,EventController):
            row['source_policy']['proxy_definition']='NORMALIZED_GUIDED_OUTPUT_SQUARED_ERROR'
            row['source_policy']['creation_floor_unit']='WC_PAID_DELTA_Y_ROOT_PROXY'
            row['source_policy']['accumulated_error_used_for_choice']=False
            row['source_policy']['latent_or_UniPC_history_reset']=False
            row['source_policy']['event_math']=self.controller.query_basis(self.controller.history[-1])
        return result


class MathSamplingOwner(CurrentBirthSamplingOwner):
    def __init__(self,*args,math_parameters,horizon=None,source_mode='FUSION',fixed_control_plan=None,**kwargs):
        if kwargs['method']!='A_CPD_BETA1_ONE_PHASE':raise ValueError('Frozen unit shared-phase A required')
        model=args[0] if args else kwargs['model']
        def sigma_at(step):
            scheduler=model.sample_scheduler
            if not 1<=step<=36 or len(scheduler.sigmas)<36:
                raise ValueError('Actual ordinary full36 known sigma schedule required')
            return float(scheduler.sigmas[step-1])
        controller=CurrentBirthCPDController if horizon is None else functools.partial(
            EventController,math_parameters=math_parameters,horizon=horizon,sigma_at=sigma_at,
            fixed_control_plan=fixed_control_plan)
        ctor=bind_globals(DynamicSamplingOwner.__init__,{
            'SourceAwareCPDController':functools.partial(controller,strategy=kwargs['spec']['working_epoch_strategy']),
            'SourceAwarePartialDeployment':functools.partial(MathDeployment,
                math_parameters=math_parameters,source_mode=source_mode)})
        ctor(self,*args,**kwargs)

    def installation(self):
        return super().installation()+('MATH_N2_TEACHER_FREE_SOURCE_ACTION_R1',
            self.deployment.readout.gamma,self.deployment.readout.mode)
