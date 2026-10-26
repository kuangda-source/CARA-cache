"""Local or GPU-hidden host CPU checks. Explicit small weights, no inference claim."""
import argparse
import hashlib
import io
import inspect
import json
import os
from pathlib import Path
import sys
import time
import traceback
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or a.artifacts.exists():raise FileExistsError('Unique receipt/artifacts required')
    a.artifacts.mkdir(parents=True)
    import torch
    torch.set_num_threads(1)
    def forbid(*a,**kw):raise RuntimeError('CPU validation forbids CUDA initialization/downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    start=time.monotonic();stream=io.StringIO();value={}
    try:
        tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_innovation_gain_r1'))
        if not tests.wasSuccessful():raise ValueError('Innovation unit/source-adapter checks failed')
        import check_scout_parent_cpu_v22 as parent_test
        original_parent_body_source=inspect.getsource(parent_test.body)
        from wcomr.innovation_gain_observer_r1 import execute, restore_readout_inputs
        from wcomr.innovation_gain_r1 import InnovationGainKernel
        from wcomr.innovation_gain_assets_r1 import GainAssetStore, load_state
        from test_scout_readout_v22 import fixture
        real_schema=None;actual_request=None
        if (ROOT/'registration.json').exists():
            # Host execution only: import the actual frozen request class.
            # Explicit optional-dependency CPU import adapters match prior
            # accepted host CPU checks; no CUDA or weights are permitted.
            runtime=ROOT/'cache/runtime'
            sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
            os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
            import triton
            class Driver:
                def get_benchmarker(self):return forbid
                def __getattr__(self,name):raise RuntimeError('CPU refuses Triton: '+name)
            triton.runtime.driver.active=Driver()
            import transformers.utils as hu
            from transformers.utils import import_utils as iu
            saved=hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device
            hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True
            torch.cuda.current_device=lambda:0
            try:
                from cosmos_predict2.config import InferenceArguments
            finally:
                hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
            raw=json.loads((ROOT/'configs/wc_scout_cal12_production_entry_r1_20261018.json').read_text())['requests']
            samples=[InferenceArguments.model_validate(r) for r in raw[:2]]
            assert InferenceArguments.model_config['frozen'] is True
            def actual_request(name):
                return InferenceArguments.model_validate({**samples[0].model_dump(mode='python',round_trip=True),
                                                           'name':name,'resolution':'16,16'})
            source=inspect.getsource(parent_test.body)
            assert source.count('type(selected[0])(name)')==1 and source.count("type(selected[0])('OLD_CAL_CPU_FAILURE')")==1
            source=source.replace('type(selected[0])(name)','_actual_request(name)').replace(
                "type(selected[0])('OLD_CAL_CPU_FAILURE')","_actual_request('OLD_CAL_CPU_FAILURE')")
            parent_test._actual_request=actual_request
            exec(compile(source,__file__+'#real-frozen-request-declared-small-geometry','exec'),vars(parent_test))
            real_schema=dict(actual_class=InferenceArguments.__module__+'.'+InferenceArguments.__qualname__,
                actual_frozen=True,production_requests_validated=len(samples),production_resolution='432,768',
                declared_CPU_fixture_resolution='16,16',real_weights=False)
        seen=[];replays=[];stores=[]
        def new_execute(*args,**kwargs):
            sink=kwargs['sink']
            schemas={}
            store=None
            def checked_sink(payload):
                nonlocal store
                extra=payload['innovation_gain']
                assert extra['additional_guided_adapter_replays']==3
                assert extra['token_layout']=='BTHWD' and set(extra['outputs'])=={'f10','f01','f05'}
                assert 'gain_moments' in payload
                if store is None:
                    store=GainAssetStore(a.artifacts/('streamed_'+str(len(stores))),
                                        byte_limit=2**30,check_space=lambda:None)
                    stores.append(store)
                artifact=store.save(payload)
                loaded=load_state(store.root,artifact)
                restored=restore_readout_inputs(loaded,schemas[payload['context'][0]],'cpu')
                warp=fixture()[0].warp
                for gains,label in (((0.,0.),'FULL'),((1.,1.),'R4_GLOBAL')):
                    kernel=InnovationGainKernel(args[0].pipe.model,kwargs['runtime'],kwargs['wc'],kwargs['rf'],
                        warp,max_logical_copy_bytes=1<<30,gains=gains)
                    replay=kernel.evaluate_gain(**restored)
                    assert all(torch.equal(x,y) for x,y in zip(replay['outputs'],payload['readouts'][label]['outputs']))
                    replays.append(label)
                seen.append((payload['context'][0],payload['step']))
                sink(payload)
            # CPU harness rebuilds its declared condition class per flow. Each
            # execute still checks a single stable schema across all six states.
            return execute(*args,**{**kwargs,'sink':checked_sink},condition_registry=schemas)
        parent_test.execute=new_execute
        controls=parent_test.run(ROOT/'cache/runtime',lambda path:torch.load(path,map_location='cpu',weights_only=True),a.artifacts)
        from check_innovation_gain_deployment_cpu_r1 import run as deploy_checks
        deployment=deploy_checks(ROOT/'cache/runtime',a.artifacts/'deployment',
                                 body_source=original_parent_body_source,actual_request=actual_request)
        value=dict(status='IG_SOURCE_BOUND_CPU_PASS_NOT_REAL_MODEL_RESULT',unit_tests=tests.testsRun,
                   full_parent_controls=controls,observed_gain_states_including_failure_attempts=len(seen),
                   saved_input_endpoint_replays_including_failure_attempts=len(replays),
                   streamed_unique_anchor_stores=len(stores),
                   actual_request_schema=real_schema,
                   free_running_deployment_controls=deployment,
                   original_parent_implementation_unchanged=True)
    except BaseException:
        value=dict(status='CPU_FAILED',traceback=traceback.format_exc())
    files=[str(x.relative_to(ROOT)) for pattern in ('src/wcomr/innovation_gain*_r1.py','tests/test_innovation_gain_r1.py') for x in ROOT.glob(pattern)]
    files += ['scripts/check_cara_innovation_gain_cpu_r1.py','src/wcomr/scout_parent_v22.py','src/wcomr/scout_readout_v22.py',
              'tests/check_scout_parent_cpu_v22.py','tests/test_scout_readout_v22.py']
    files+=['tests/check_innovation_gain_deployment_cpu_r1.py']
    value.update(source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
        tests_log=stream.getvalue(),wall_seconds=time.monotonic()-start,observed_unix=time.time(),
        cuda_initialized=torch.cuda.is_initialized(),GPU_submissions=0,real_model_inference=False)
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value[k] for k in ('status','wall_seconds','real_model_inference')}))
    if value['status']=='CPU_FAILED':print(value['traceback']);raise SystemExit(1)


if __name__=='__main__':main()
