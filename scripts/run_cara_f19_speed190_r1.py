"""One admitted original CAL35 model process, ordinary guardrails and codec."""
import argparse,json,os,sys,time
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    for k in ('project','stage'):p.add_argument('--'+k,type=Path,required=True)
    for k in ('source-revision','gpu-uuid'):p.add_argument('--'+k,required=True)
    a=p.parse_args();runtime=a.project/'runtime'
    sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    from wcomr.cara_f19_speed190_execution_r1 import validate_stage,RUNNER,RUN
    from wcomr.gpu_budget_pool_v2 import atomic_json,sha
    from wcomr.history104_storage_r2 import storage_for
    from run_cara_budget_calibration_r1 import validate_runner_handoff
    from wcomr.wc73_exclusive_r1 import runner_context_gate
    card,reg,auth=validate_stage(a.project,a.stage)
    launch=json.loads((a.stage/'GPU-launch.json').read_text());storage=storage_for(a.stage);storage.check()
    assert launch['source_revision']==a.source_revision and launch['gpu_uuid']==a.gpu_uuid
    assert os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==(a.project/'.sync/gpu-locks'/(a.gpu_uuid+'.lock')).resolve()
    command=[sys.executable,str(a.stage/RUNNER),'--project',str(a.project),'--stage',str(a.stage),
        '--source-revision',a.source_revision,'--gpu-uuid',a.gpu_uuid]
    identity=validate_runner_handoff(a.stage,launch,sha(a.stage/'GPU-launch.json'),command)
    runner_context_gate(a.project,a.stage,a.gpu_uuid)
    import torch
    torch.set_num_threads(2)
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.cara_f19_speed190_collection_r1 import collect_loaded
    read=lambda n:json.loads((a.stage/n).read_text())
    output=storage.output;assert output==a.project/'outputs'/RUN
    setup=SetupArguments(**{**read('configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(output)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    samples={r['name']:InferenceArguments(**{k:v for k,v in r.items() if k!='partition'}) for r in card['inputs']}
    state=dict(status='MODEL_LOADING',started_unix=time.time(),identity=identity,scope_sha256=card['scope_sha256'],CPU_fixture_only=False)
    target=output/'model-runner.json';atomic_json(target,state)
    try:
        init_environment();init_output_dir(output,profile=False)
        install_core_inference_registration(setup.model,setup.experiment)
        start=time.monotonic();inference=im.Inference(setup);torch.cuda.synchronize()
        state['load_seconds']=time.monotonic()-start
        assert torch.__version__=='2.7.1+cu128' and len(inference.pipe.model.net.blocks)==28
        assert torch.cuda.get_device_capability()==(8,6)
        common=dict(runtime=runtime,wc=wc,rf=rf,inference_module=im,
            expected_shape=read('configs/wc_ra_comparison_production_r2_20261010.json')['expected_real_shape'])
        result,evidence=collect_loaded(inference,samples,card,common,output,storage,
            read('manifests/wc_h0_eval_mode_contract_20261003.json')['module_types'])
        assert result['status']=='COMPLETE35_PENDING_RELEASE_SCORING'
        state.update(status='COMPLETE35_PENDING_RELEASE_SCORING',loaded_model_checks=evidence,collection_sha256=sha(output/'collection.json'))
    except BaseException as error:
        state.update(status='FAILED_NO_RETRY',error_type=type(error).__name__,error=str(error));raise
    finally:
        try:cleanup_environment()
        finally:
            state['ended_unix']=time.time();atomic_json(target,state)


if __name__=='__main__':main()
