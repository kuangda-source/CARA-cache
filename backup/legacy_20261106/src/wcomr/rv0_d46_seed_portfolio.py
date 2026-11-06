"""Two independent fresh-seed Native/WC pairs sharing one model load."""
import copy
from pathlib import Path

import torch
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .rv0_fork import WC_CONFIGURATION
from .mid_coverage import WC_FIELDS, tree_digest
from .rv0_d46_seed_causal import run_d46_seed_batch
from .w1_native_reference_sampling import run_native_request


def run_portfolio(inference, samples, wc, settings, *, state, save, output,
                  inference_module, mode_setup, runtime, scope, sampling_policy,
                  native_runner=run_native_request, causal_runner=run_d46_seed_batch):
    if ([s.seed for s in samples] != [1,2] or [s.name for s in samples] != ['human_199_seed1','human_199_seed2']
            or state.get('cases') or scope['seed_values'] != [1,2]):
        raise ValueError('Two registered seed requests required before any generation')
    model=inference.pipe.model;net=model.net
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    fingerprint=initial.fingerprint(); original_keys={k for k in WC_FIELDS if hasattr(net,k)}
    settings_before={k:copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    def restore():
        initial.restore()
        for name in set(WC_FIELDS)-original_keys:
            if hasattr(net,name):delattr(net,name)
        for name,value in settings_before.items():setattr(net,name,copy.deepcopy(value))
        if initial.fingerprint()!=fingerprint:raise ValueError('Cross-request initial state restore failed')
    state.update(planned_scope=scope['scope_counts'],cases=[]);save()
    try:
        for sample in samples:
            case={'name':sample.name,'seed':sample.seed,'status':'STARTED','native':{'status':'STARTED'},'WC':{}}
            state['cases'].append(case);save();restore()
            case['pre_Native_initial_fingerprint']=initial.fingerprint()
            native_runner(inference,sample,state=case['native'],save=save,output=output/sample.name/'Native35',
                inference_module=inference_module,sampling_policy=sampling_policy,
                expected_flags=backend_flags(),synchronize=lambda:torch.cuda.synchronize() if torch.cuda.is_initialized() else None)
            restore();case['pre_WC_initial_fingerprint']=initial.fingerprint()
            context=(scope['run_id']+':'+sample.name,state['model_context'],tree_digest(sample.model_dump(mode='json')))
            config={'sample_names':[sample.name],'run_id':scope['run_id'],'target_calls':[46],
                'maximum_age_solver_steps':32,'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30)}
            causal_runner(inference,[sample],wc,settings,state=case['WC'],save=save,output=output/sample.name/'WC',
                inference_module=inference_module,contexts=[context],mode_setup=mode_setup,runtime=runtime,config=config)
            case['status']='SEED_NATIVE_AND_WC_CONTROLS_COMPLETE_SCORING_PENDING';save();restore()
        state['status']='D46_TWO_SEEDS_GPU_CORE_COMPLETE_AUDIT_AND_SCORE_PENDING';save()
    except BaseException as error:
        state.update(status='D46_SEED_TECH_BLOCKED_FULL_TWO_SEED_DENOMINATOR_RETAINED',error=str(error));save();raise
    finally:
        restore()
