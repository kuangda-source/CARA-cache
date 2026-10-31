"""Produce one approved complete calibration; no dispatch, scoring or freeze."""
import argparse
from collections import Counter
import os
from pathlib import Path
import sys
import time


def validate_runner_handoff(stage, launch, launch_sha256, expected_command):
    from wcomr.cara_budget_original_handles_r1 import bind_original_process, observe_original_process
    from wcomr.cara_budget_search_journal_r1 import read_record
    from wcomr.policy_price_terminal_r1 import require

    identity = read_record(stage / 'runner-start.json')['identity']
    current = bind_original_process(os.getpid())
    # exec preserves this process identity while replacing the bootstrap argv.
    # Keep the original command hash as provenance in all downstream receipts.
    require(all(identity[key] == current[key] for key in ('pid', 'start_ticks', 'host_view'))
            and read_record(stage / 'runner-dispatch-grant.json') == dict(identity=identity, launch_sha256=launch_sha256)
            and observe_original_process(launch['guardian_identity'])['original_live'] is True,
            'Original runner grant and live guardian required')
    require(launch['commands']['runner'] == expected_command, 'Original frozen runner command differs')
    return identity


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--source-revision',required=True)
    parser.add_argument('--gpu-uuid',required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.project/'runtime'),
                  str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from wcomr.cara_budget_runner_binding_r1 import validate,RUNNER
    from wcomr.cara_budget_search_journal_r1 import read_record as read,create_record
    from wcomr.policy_price_terminal_r1 import require
    from wcomr.cara_fast_execution_r2 import RA
    from wcomr.cara_fast_spec_r1 import digest
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.wc73_exclusive_r1 import runner_context_gate
    card,launch,profile,limits,production_context=validate(args.project,args.stage)
    output=args.project/'outputs'/launch['run_id']
    storage=storage_for(args.stage)
    storage.check()
    require(storage.output==output and storage.config['image_bytes']==limits.volume_bytes,
            'Wrong original calibration storage')
    require(launch['source_revision']==args.source_revision
            and launch['gpu_uuid']==args.gpu_uuid==os.environ['CUDA_VISIBLE_DEVICES'], 'Runner identity differs')
    expected_command=[sys.executable,str(args.stage/RUNNER),'--project',str(args.project),
        '--stage',str(args.stage),'--source-revision',args.source_revision,'--gpu-uuid',args.gpu_uuid]
    identity=validate_runner_handoff(args.stage,launch,production_context['launch_sha256'],expected_command)
    create_record(output/'calibration-runner-intent.json',dict(identity=identity,context=production_context))
    require(os.environ['WC_SUPERVISOR_PID']==str(os.getppid()), 'Wrong supervisor')
    require(Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()
            ==(args.project/'.sync/gpu-locks'/(args.gpu_uuid+'.lock')).resolve(), 'Inherited device lease missing')
    context=runner_context_gate(args.project,args.stage,args.gpu_uuid)
    import torch
    torch.set_num_threads(2)
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as inference_module
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.simple26d_r1 import MODE_REF
    from wcomr.cara_budget_calibration_r1 import Calibration,ProductionRequests,PRODUCTION_CONFIG
    setup=SetupArguments(**{**read(args.stage/'configs/f1_setup.json'),
                            'keep_going':True,'worldcache_enabled':True,'output_dir':str(output)})
    require(not setup.disable_guardrails and not setup.use_torch_compile
            and not setup.offload_diffusion_model, 'Original inference setup differs')
    samples={r['name']:InferenceArguments(**{k:v for k,v in r.items() if k!='partition'}) for r in card['inputs']}
    state=dict(phase='CALIBRATION',status='MODEL_LOADING',started_unix=time.time(),
               source_revision=launch['source_revision'],scope_sha256=card['scope_sha256'],
               context_sha256=digest(production_context),scientific_freeze_written=False)

    def save(batch=None):
        if batch is not None:
            state.update(status=batch['status'])
            atomic_json(output/'calibration-collection.json',batch)
        atomic_json(output/'calibration-runner.json',state)

    save()
    init_environment()
    init_output_dir(output,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        started=time.monotonic()
        inference=inference_module.Inference(setup)
        torch.cuda.synchronize()
        state['load_seconds']=time.monotonic()-started
        model=inference.pipe.model
        net=model.net
        require(torch.__version__=='2.7.1+cu128' and len(net.blocks)==28
                and list(torch.cuda.get_device_capability())==profile['hosts'][launch['host']]['capability'],
                'Pinned runtime/model/device differs')
        require(str(model.precision)=='torch.bfloat16' and net.use_wan_fp32_strategy is True,
                'Original BF16 plus selected Wan FP32 strategy differs')
        parameters=list(net.named_parameters())
        versions=[(name,value,value._version,str(value.dtype)) for name,value in parameters]
        # Observe original loader choices. No dtype/backend conversion is made.
        state['precision']=dict(model_precision=str(model.precision),
            net_parameter_dtypes=dict(Counter(str(value.dtype) for _,value in parameters)),
            use_wan_fp32_strategy=net.use_wan_fp32_strategy,
            conditional_frame_timestep=model.config.conditional_frame_timestep,
            matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,
            cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
            cudnn_benchmark=torch.backends.cudnn.benchmark,
            cudnn_deterministic=torch.backends.cudnn.deterministic,
            outer_autocast=torch.is_autocast_enabled())
        require(state['precision']['conditional_frame_timestep']==.1
                and state['precision']['outer_autocast'] is False, 'Original condition/autocast differs')
        atomic_json(output/'calibration-model-precision.json',state['precision'])
        mode=establish_shared_eval(net,read(args.stage/MODE_REF)['module_types'])
        verify_shared_eval(net,mode)
        settings=card['roles']['ALLD']['settings']
        wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
        origin=initial.fingerprint()
        common=dict(runtime=args.project/'runtime',wc=wc,rf=rf,inference_module=inference_module,
                    expected_shape=read(args.stage/'configs/wc_ra_comparison_production_r2_20261010.json')['expected_real_shape'])
        def before():
            storage.check()
            initial.restore()
            require(initial.fingerprint()==origin, 'Request reset differs')
            verify_shared_eval(net,mode)
            require(all(value._version==version and str(value.dtype)==dtype
                        for _,value,version,dtype in versions), 'Model parameters/precision changed')

        adapter=ProductionRequests(inference=inference,samples=samples,card=card,common=common,
            ra_binding=read(args.stage/RA),host=launch['host'],before_request=before,
            production_context=production_context)
        entry=Calibration(root=output/'calibration',card=card,config=PRODUCTION_CONFIG,
            context_sha256=digest(production_context),RGB_shape=card['calibration']['RGB_shape'],
            execute=adapter,storage_limits=limits,production_context=production_context,create=True)
        batch=entry.run(allow_new=True)
        save(batch)
        require(batch['complete'] and batch['complete_physical_paths']==112,
                'Original complete51-query/112-path calibration required; no partial winner')
        initial.restore()
        require(initial.fingerprint()==origin, 'Final model state differs')
    except BaseException as error:
        state.update(status='CALIBRATION_FAILED',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        cleanup_environment()
        state['ended_unix']=time.time()
        save()
    # Keep the exclusive context allocated through cleanup and receipt writes.
    require(context is not None, 'Runner context disappeared')


if __name__=='__main__':
    main()
