#!/usr/bin/env python3
"""GPU-hidden P2 all-count Native and same-trajectory history production CPU."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def actual_request_boundaries(adapter,card,bases,request_class,stage):
    """Real frozen arguments enter both production engines; no CUDA or weights."""
    from wcomr.policy_generator_r1.frozen_request_arguments import request_variant
    from wcomr.policy_generator_r1.shared66_collection import collect
    import copy
    count=0
    for role in card['roles']:
        for member in bases:
            slot=dict(id='guard_'+role+'_'+member,role=role,member=member,seed=0)
            try:adapter(slot,stage/'never-created')
            except ValueError as e:assert str(e)=='Ordinary guardrails required'
            else:raise AssertionError('Unprotected real request accepted')
            count+=1
    assert count==60 and not (stage/'never-created').exists()
    failures=[]
    for seed,n in ((True,26),('0',26),(0,0),(0,-1),(0,26.5)):
        try:request_variant(next(iter(bases.values())),seed=seed,num_steps=n)
        except ValueError:failures.append('invalid_override')
        else:raise AssertionError('Invalid override accepted')
    try:request_class.model_validate(dict(next(iter(bases.values())).model_dump(mode='python',round_trip=True),guidance=99))
    except Exception as e:assert type(e).__name__=='ValidationError';failures.append('real_schema_constraint')
    else:raise AssertionError('Real schema validation bypassed')
    slot=dict(card['matrix'][0],id='bad-grid',actual_updates=999)
    try:adapter(slot,stage/'never-created')
    except ValueError as e:assert 'schedule differ' in str(e);failures.append('bad_slot_grid')
    else:raise AssertionError('Bad grid accepted')
    try:adapter(dict(card['matrix'][0],id='bad-grid'),stage/'never-created')
    except ValueError as e:assert 'already attempted' in str(e);failures.append('failed_slot_no_replay')
    else:raise AssertionError('Failed slot replayed')
    states=[]
    try:collect(card,stage/'boundary-no-output',lambda slot,policy,directory:adapter(slot,directory),lambda state:states.append(copy.deepcopy(state)))
    except ValueError as e:assert str(e)=='Ordinary guardrails required'
    else:raise AssertionError('Full card swallowed request failure')
    final=states[-1];assert final['status']=='FAILED66_DENOMINATOR_RETAINED' and len(final['rows'])==66
    assert final['rows'][0]['status']=='TECH_FAILED' and all(r['status']=='NOT_REACHED' for r in final['rows'][1:])
    assert not (stage/'boundary-no-output').exists()
    return dict(actual_class=request_class.__module__+'.'+request_class.__qualname__,actual_class_frozen=request_class.model_config['frozen'],preload_validated_slots=66,old_bug_reproduced=True,full_resolution_request_identity_preserved=True,actual_adapter_guard_refusals=count,negative_controls=failures,failed66_original_denominator_retained=True,failed66_completed=0,failed66_unreached=65,original_requests_unchanged=True)


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();runtime=a.project/'runtime';started=time.time()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',WC_SCOUT_KIND='CAL12')
    sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import torch
    assert not torch.cuda.is_initialized();torch.set_num_threads(1)
    def forbidden(*a,**kw):raise RuntimeError('PG CPU forbids CUDA, model weights and network')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    original_load=torch.load
    def diagnostic_load(file,*args,**kwargs):
        path=Path(file if isinstance(file,(str,Path)) else file.name).resolve()
        if not path.is_relative_to((a.stage/'CPU-pg-numeric').resolve()) or path.suffix!='.pt':forbidden()
        return original_load(file,*args,**kwargs)
    torch.load=diagnostic_load
    import triton
    class Driver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,n):raise RuntimeError('CPU refuses Triton: '+n)
    triton.runtime.driver.active=Driver()
    import transformers.utils as hu
    from transformers.utils import import_utils as iu
    saved=(hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device)
    hu.is_flash_attn_2_available=iu.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    try:
        from cosmos_predict2.config import SetupArguments,InferenceArguments
        import cosmos_predict2.inference as im
        from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
        from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    finally:hu.is_flash_attn_2_available,iu.is_flash_attn_2_available,torch.cuda.current_device=saved
    from wcomr.policy_interval_assets_r1 import read,sha
    reg=read(a.stage/'registration.json')
    assert {n:sha(a.stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']
    assert {n:sha(runtime/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
    original_requests=read(a.stage/'configs/wc_policy_interval_assets_full1624_r1_20261020.json')['requests']
    card=read(a.stage/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json')
    requests=[{**r,'num_steps':spec['requested_steps']} for spec in card['roles'].values() for r in original_requests]
    samples=[InferenceArguments(**r) for r in requests]
    assert len(samples)==60 and all(all(s.model_dump(mode='json')[k]==v for k,v in r.items()) for s,r in zip(samples,requests))
    setup=SetupArguments(**{**read(a.stage/'configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.stage/'CPU-output')})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    spec=importlib.util.spec_from_file_location('pg_sampler_checks',a.stage/'tests/check_cara_cal66_sampling_cpu_r2.py')
    checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    from wcomr.policy_generator_r1.p2_native_sampling import execute
    from types import SimpleNamespace
    from wcomr.policy_generator_r1.exploration_requests import Requests
    from wcomr.policy_generator_r1.frozen_request_arguments import request_variant
    from wcomr.policy_generator_r1.interval_grammar import Profile
    import copy
    params=dict(card['profile']);params['protected_dense']=tuple(params['protected_dense']);params['alpha_candidates']=tuple(params['alpha_candidates']);profile=Profile(**params)
    bases={r['name']:InferenceArguments(**r) for r in original_requests}
    before={n:s.model_dump(mode='python',round_trip=True) for n,s in bases.items()}
    adapter=Requests(inference=SimpleNamespace(rank0=True,text_guardrail_runner=None,video_guardrail_runner=None),samples=bases,profile=profile,roles=card['roles'],schedules=card['schedules'],common=dict(runtime=runtime,wc=None,rf=None,settings={},calibration=None,specs={},inference_module=im,expected_shape=[]))
    prepared=adapter.validate_slots(card['matrix']);assert len(prepared)==66 and not adapter.seen
    for slot,sample in zip(card['matrix'],prepared):
        assert type(sample) is InferenceArguments and sample.model_dump(mode='python',round_trip=True)==dict(before[slot['member']],seed=slot['seed'],num_steps=card['roles'][slot['role']]['requested_steps'])
    try:copy.deepcopy(next(iter(bases.values()))).seed=0
    except Exception as e:assert type(e).__name__=='ValidationError' and 'frozen_instance' in str(e)
    else:raise AssertionError('Old bug no longer reproduced on actual class')
    actual_boundary=actual_request_boundaries(adapter,card,bases,InferenceArguments,a.stage)
    from check_wc_policy_price_refresh_cpu_r1 import guardrail_codec_probe
    codec=guardrail_codec_probe(a.stage,a.project,im)
    import unittest
    spec2=importlib.util.spec_from_file_location('p2_batch_cpu',a.stage/'tests/test_cara_pg_p2_production_batch.py')
    batch=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(batch)
    batch_result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(batch))
    assert batch_result.wasSuccessful()
    tiny=InferenceArguments.model_validate({**original_requests[0],'resolution':'16,16'})
    numeric=checks.run(runtime,a.stage/'CPU-pg-numeric',tiny)
    assert before=={n:s.model_dump(mode='python',round_trip=True) for n,s in bases.items()}
    assert {c['flow'] for c in numeric['checks']}=={False,True}
    from four_card_policy_assets_port_r1 import cpu_transport_probe
    transport=cpu_transport_probe(a.stage)
    value=dict(status='SHARED_CAL66_FROZEN_ENTRY_CPU_R2_COMPLETE_NOT_GPU',source_revision=reg['source_revision'],
        registration_sha256=sha(a.stage/'registration.json'),started_unix=started,ended_unix=time.time(),
        frozen_boundary=actual_boundary,batch_controls_passed=batch_result.testsRun,actual_request_count=60,guard_refusal_controls=60,actual_SetupArguments=True,codec=codec,numeric=numeric,transport=transport,
        CUDA_initialized=False,model_weights_loaded=0,GPU_submissions=0,ledger_written=False)
    assert not torch.cuda.is_initialized()
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=value['status'],CPU_wall_seconds=value['ended_unix']-started)))
if __name__=='__main__':main()
