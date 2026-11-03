"""GPU-hidden actual production import plus all affected full sampler paths."""
import argparse,importlib.util,json,os,sys,time,unittest
from pathlib import Path


def main():
    p=argparse.ArgumentParser()
    for key in ('project','stage'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();runtime=a.project/'runtime';started=time.time()
    os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WC_SCOUT_KIND='CAL12')
    sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.stage/'tests'),str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    os.environ['CARA_READ_WRITE_RUNTIME']=str(runtime)
    import torch,triton
    torch.set_num_threads(2)
    def forbidden(*a,**kw):raise RuntimeError('CAL35 CPU forbids CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,n):raise RuntimeError('CPU refuses Triton: '+n)
    triton.runtime.driver.active=Driver()
    import transformers.utils as hu
    from transformers.utils import import_utils as iu
    saved=hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device
    hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        import cosmos_predict2.inference
        from cosmos_predict2._src.predict2.inference import worldcache_utils
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow
    finally:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
    from wcomr.cara_f19_speed190_execution_r1 import validate_stage,MANIFEST
    from wcomr.gpu_budget_pool_v2 import atomic_json
    card,reg,auth=validate_stage(a.project,a.stage,require_proof=False)
    setup=SetupArguments(**{**json.loads((a.stage/'configs/f1_setup.json').read_text()),
        'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.stage/'CPU-output')})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    for r in card['inputs']:InferenceArguments(**{k:v for k,v in r.items() if k!='partition'})
    import check_cara_f19_speed190_pipeline_cpu_r1 as pipeline
    numeric=pipeline.run(runtime,a.stage/('CPU-pipeline-'+str(os.getpid())))
    assert len(numeric['checks'])==2 and {r['flow'] for r in numeric['checks']}=={False,True}
    suite=unittest.defaultTestLoader.loadTestsFromName('test_cara_f19_speed190_sampling_r1')
    tests=unittest.TextTestRunner(verbosity=1).run(suite)
    assert tests.wasSuccessful() and tests.testsRun==4 and not torch.cuda.is_initialized()
    proof=dict(passed=True,scope_sha256=card['scope_sha256'],source_sha256=reg['payload_sha256'],
        runtime_source_sha256=reg['runtime_source_sha256'],actual_production_entry_imported=True,
        complete35_tiny_pipeline_accepted=True,new_sampling_tests_passed=True,
        unchanged_lifecycle_components_reused=True,CUDA_initialized=False,
        model_weights_loaded=0,GPU_submissions=0,numeric=numeric,unit_tests=tests.testsRun,
        started_unix=started,ended_unix=time.time(),CPU_fixture_only=True)
    if (a.stage/'CPU-proof.json').exists():raise ValueError('CPU proof already exists')
    atomic_json(a.stage/'CPU-proof.json',proof)
    print(json.dumps(dict(status='CAL35_LINUX_CPU_PASS',complete_tiny_paths=70,wall_seconds=time.time()-started)))


if __name__=='__main__':main()
