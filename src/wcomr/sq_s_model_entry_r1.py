"""One S inference load, original setup/precision, complete matrix, cleanup.

The caller supplies an already admitted context and the pinned Cosmos modules.
CPU controls replace only the declared loader/environment boundaries. This
module creates no GPU lease, container, authorization or budget reservation.
"""
from collections import Counter
import copy
from pathlib import Path
import time

import torch

from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .h0_mode import establish_shared_eval,verify_shared_eval
from .sq_s_batch_r1 import digest,require,validate_scope
from .sq_s_physical_r1 import make_physical_scope
from .sq_s_runner_r1 import run_matrix
from .sq_s_storage_r1 import SCollectionStore

REAL_IDENTITY='2104a9d053fc6e2967de363fa261bb3a514ee5b93a97d7783208bf3f187c32a6'
REAL_RESOURCE='c3f5d742cbd014838104cae6e7d5afc7adfb9b41c01650bf6a311890a500db2b'


def execute(*,bundle,runtime,output,storage,context,runtime_api,save_health,
            save_matrix,save_result,CPU_fixture=False):
    """Consume one original caller/store context; exceptions never retry a load."""
    require(type(CPU_fixture) is bool,'Explicit CPU/real entry boundary required')
    upper,physical,identity,contract=(bundle[k] for k in ('upper','physical','identity','resource_contract'))
    require(upper['CPU_fixture_only']==contract['CPU_fixture_only']==CPU_fixture,
        'Model entry CPU/real scopes differ')
    validate_scope(upper)
    require(identity['identity_sha256']==digest({k:v for k,v in identity.items() if k!='identity_sha256'}),
        'Frozen S execution identity differs')
    witness=bundle.get('witness')
    require(physical==make_physical_scope(upper,physical['host'],identity['identity_sha256'],witness),
        'Complete original S physical matrix differs')
    require(CPU_fixture or bundle.get('CPU_decode_fixture') is None,
        'A CPU decode fixture cannot enter the real model loader')
    if not CPU_fixture:
        require(identity['identity_sha256']==REAL_IDENTITY and contract['contract_sha256']==REAL_RESOURCE,
            'Only the original real S execution and resource identities are admitted')
        require(context.get('authorizes_S_collection') is True
            and context.get('scope_sha256')==upper['scope_sha256']
            and context.get('physical_scope_sha256')==physical['physical_scope_sha256']
            and context.get('execution_identity_sha256')==REAL_IDENTITY
            and context.get('S_resource_contract_sha256')==REAL_RESOURCE
            and context.get('host')==physical['host']
            and all(context.get(k) for k in ('launch_id','gpu_uuid','source_revision')),
            'Original separately admitted S-only context required before loading')
        if witness is not None:
            require(context['gpu_uuid']==identity['retained_OFF_GPU_UUID']
                and context.get('fresh_reuse_witness_sha256')==witness['witness_sha256'],
                'The original OFF hardware and fresh witness are required before loading')
    require(not getattr(storage,'_s_model_entry_consumed',False),
        'Original S model entry exists; recover without retry')
    storage._s_model_entry_consumed=True
    storage.check()
    setup_values={**identity['model_setup'],**identity['setup_overrides'],'output_dir':str(output)}
    require(identity['setup_overrides']==dict(keep_going=True,worldcache_enabled=True)
        and setup_values['keep_going'] and setup_values['worldcache_enabled']
        and not any(setup_values[k] for k in ('disable_guardrails','use_torch_compile','offload_diffusion_model')),
        'Original guarded, uncompiled, resident S inference setup required')
    setup=runtime_api.config.SetupArguments(**setup_values)
    require(Path(setup.output_dir)==Path(output)
        and all(getattr(setup,k)==v for k,v in setup_values.items() if k!='output_dir'),
        'Runtime setup parser changed an original S setting')
    if not CPU_fixture:
        from .runtime_config import MODEL,EXPERIMENT
        require((setup.model,setup.experiment)==(MODEL,EXPERIMENT),
            'Original registered S model/experiment selection differs')
    samples={r['name']:runtime_api.config.InferenceArguments(**r) for r in identity['inputs']}
    require(list(samples)==upper['prompts']
        and all(all(getattr(samples[r['name']],key)==value for key,value in r.items()) for r in identity['inputs'])
        and all(samples[r['name']].seed==r['seed']==0
        and samples[r['name']].guidance==r['guidance']==7 and samples[r['name']].num_steps==r['num_steps']==35
        and samples[r['name']].num_output_frames==r['num_output_frames']==93 for r in identity['inputs']),
        'Original two S request objects differ before model loading')
    state=dict(status='S_MODEL_ENVIRONMENT_STARTING',CPU_fixture=CPU_fixture,
        execution_identity_sha256=identity['identity_sha256'],physical_scope_sha256=physical['physical_scope_sha256'],
        model_load_attempts=0,model_loads=0,environment_cleanup_attempted=False,environment_cleanup_accepted=False,
        original_GPU_release_accepted=False,original_financial_settlement_accepted=False,
        actual_scientific_labels_accepted=False,started_unix=time.time())
    save_health(copy.deepcopy(state));result=None
    try:
        runtime_api.initialize.init_environment()
        runtime_api.initialize.init_output_dir(output,profile=False)
        runtime_api.install_registration(setup.model,setup.experiment)
        state.update(status='S_MODEL_LOADING',model_load_attempts=1)
        save_health(copy.deepcopy(state))
        started=time.monotonic();inference=runtime_api.inference.Inference(setup)
        if not CPU_fixture:torch.cuda.synchronize()
        state.update(model_loads=1,model_load_seconds=time.monotonic()-started)
        model=inference.pipe.model;net=model.net
        if not CPU_fixture:
            require(torch.__version__==identity['torch_version']=='2.7.1+cu128'
                and torch.cuda.device_count()==1 and len(net.blocks)==28
                and list(torch.cuda.get_device_capability())=={'two_card':[8,6],'four_card':[8,9]}[physical['host']],
                'Original S model/runtime/sole device differs')
        precision=dict(model_precision=str(model.precision),
            parameter_dtypes=dict(Counter(str(p.dtype) for p in net.parameters())),
            parameter_tensors=sum(1 for _ in net.parameters()),blocks=len(net.blocks),
            use_wan_fp32_strategy=net.use_wan_fp32_strategy,
            conditional_frame_timestep=model.config.conditional_frame_timestep,
            outer_autocast=torch.is_autocast_enabled(),backend=backend_flags())
        require(precision['conditional_frame_timestep']==.1 and precision['outer_autocast'] is False
            and precision['use_wan_fp32_strategy'] is True,'Original S condition/autocast/Wan strategy differs')
        if not CPU_fixture:
            require(precision['model_precision']=='torch.bfloat16' and precision['parameter_tensors']==569
                and precision['parameter_dtypes']=={'torch.bfloat16':569},'Original full2B parameter precision differs')
        state['precision']=precision
        mode=establish_shared_eval(net,bundle['mode_types']);verify_shared_eval(net,mode)
        settings=identity['historical_WC_settings']
        runtime_api.wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
        limits=bundle['store_limits']
        store=SCollectionStore(output/'streaming',prompts=upper['prompts'],**limits)
        common=dict(runtime=runtime,wc=runtime_api.wc,rf=runtime_api.rf,settings=settings,
            calibration=None,specs={},inference_module=runtime_api.inference,
            expected_shape=identity['expected_real_shape'],audit=True)
        state.update(status='S_MODEL_LOADED_RUNNING_COMPLETE_MATRIX');save_health(copy.deepcopy(state))
        result=run_matrix(request_kwargs=dict(scope=upper,inference=inference,samples=samples,profile=bundle['profile'],
                common=common,sink=store,logical_copy_cap_bytes=contract['limits']['logical_copy_guard_bytes'],
                cpu_validation=CPU_fixture,production_context=context),
            physical_scope=physical,execution_identity_sha256=identity['identity_sha256'],resource_contract=contract,
            store=store,output=output/'paths',initial=initial,before_request=lambda slot:storage.check(),
            verify_mode=lambda:verify_shared_eval(net,mode),save_matrix=save_matrix,
            save_health=lambda value:save_health(dict(state,matrix_health=value)),witness=witness,
            CPU_decode_fixture=bundle.get('CPU_decode_fixture'))
        require(backend_flags()==precision['backend'],'S model/matrix changed original backend flags')
    except BaseException as error:
        state.update(status='S_MODEL_ENTRY_FAILED_RETAINED_NO_RETRY',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        state['environment_cleanup_attempted']=True
        try:
            runtime_api.initialize.cleanup_environment();state['environment_cleanup_accepted']=True
        except BaseException as error:
            state.update(status='S_MODEL_ENTRY_FAILED_RETAINED_NO_RETRY',cleanup_error_type=type(error).__name__,cleanup_error=str(error))
            raise
        finally:
            state['ended_unix']=time.time();save_health(copy.deepcopy(state))
    state['status']='S_MODEL_AND_MATRIX_COMPLETE_AWAITING_ORIGINAL_ALLOCATION_TERMINAL'
    result=dict(result,model_entry=state)
    save_result(result);save_health(copy.deepcopy(state))
    return result
