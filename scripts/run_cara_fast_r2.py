"""Run only the admitted A32 card; preserve original model/solver/precision."""
import argparse
from collections import Counter
import os
from pathlib import Path
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    for key in ('project','stage'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--source-revision',required=True)
    parser.add_argument('--gpu-uuid',required=True)
    args=parser.parse_args()
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'scripts'),str(args.project/'runtime'),
                  str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from wcomr.cara_fast_execution_r2 import validate,read,RUN,RA,PROFILE,require
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.history104_storage_r2 import storage_for
    from wcomr.wc73_exclusive_r1 import runner_context_gate
    card,registration,authority=validate(args.project,args.stage)
    output=args.project/'outputs'/RUN
    storage=storage_for(args.stage)
    storage.check()
    require(storage.output==output, 'Wrong A32 output storage')
    require(registration['source_revision']==args.source_revision
            and authority['gpu_uuid']==args.gpu_uuid==os.environ['CUDA_VISIBLE_DEVICES'], 'Runner identity differs')
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
    from wcomr.cara_fast_requests_r2 import Requests
    from wcomr.cara_fast_collection_r2 import verify_diagnostics
    from wcomr.wc_time_collection_r1 import collect_phase
    profile=read(args.stage/PROFILE)
    setup=SetupArguments(**{**read(args.stage/'configs/f1_setup.json'),
                            'keep_going':True,'worldcache_enabled':True,'output_dir':str(output)})
    require(not setup.disable_guardrails and not setup.use_torch_compile
            and not setup.offload_diffusion_model, 'Original inference setup differs')
    samples={r['name']:InferenceArguments(**{k:v for k,v in r.items() if k!='partition'}) for r in card['inputs']}
    state=dict(phase='A',status='MODEL_LOADING',started_unix=time.time(),
               source_revision=registration['source_revision'],scope_sha256=card['scope_sha256'])

    def save(batch=None):
        if batch is not None:
            state.update(status=batch['status'])
            atomic_json(output/'A-collection.json',batch)
        atomic_json(output/'A-runner.json',state)

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
                and list(torch.cuda.get_device_capability())==profile['hosts'][authority['host']]['capability'],
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
        atomic_json(output/'A-model-precision.json',state['precision'])
        mode=establish_shared_eval(net,read(args.stage/MODE_REF)['module_types'])
        verify_shared_eval(net,mode)
        settings=card['roles']['ALLD']['settings']
        wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
        origin=initial.fingerprint()
        common=dict(runtime=args.project/'runtime',wc=wc,rf=rf,inference_module=inference_module,
                    expected_shape=read(args.stage/'configs/wc_ra_comparison_production_r2_20261010.json')['expected_real_shape'])
        adapter=Requests(inference=inference,samples=samples,card=card,common=common,
            ra_binding=read(args.stage/RA),host=authority['host'],cpu_validation=False,
            production_context=dict(scope_sha256=card['scope_sha256'],host=authority['host'],
                gpu_uuid=args.gpu_uuid,launch_id=authority['launch_id']))

        def before(slot):
            storage.check()
            initial.restore()
            require(initial.fingerprint()==origin, 'Request reset differs')
            verify_shared_eval(net,mode)
            require(all(value._version==version and str(value.dtype)==dtype
                        for _,value,version,dtype in versions), 'Model parameters/precision changed')

        collect_phase(adapter,'A',output/'A',before_request=before,save=save,after_diagnostics=verify_diagnostics)
        initial.restore()
        require(initial.fingerprint()==origin, 'Final model state differs')
    finally:
        cleanup_environment()
        state['ended_unix']=time.time()
        save()
    # Keep the exclusive context allocated through cleanup and receipt writes.
    require(context is not None, 'Runner context disappeared')


if __name__=='__main__':
    main()
