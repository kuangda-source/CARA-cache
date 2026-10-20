#!/usr/bin/env python3
"""Single resident Cosmos; complete references and all1624 interval cells."""
import argparse
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--gpu-uuid',required=True)
    a=p.parse_args();os.environ.update(WC_SCOUT_KIND='CAL12',HF_HUB_CACHE=str(a.project/'hfhub'),
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
    import torch
    from cosmos_predict2.config import SetupArguments,InferenceArguments
    import cosmos_predict2.inference as im
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
    from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
    from wcomr.policy_interval_assets_r1 import CONFIG,COUNTS,RUN,CPU_PROOF,read,sha,matrix,full_rows
    from wcomr.policy_interval_assets_production_r1 import validate
    from wcomr.policy_interval_assets_sampling_r1 import execute
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.full_sampling import CompleteStateRoundtrip
    from wcomr.runtime_config import install_core_inference_registration
    from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
    from wcomr.mid_coverage import tree_digest
    from wcomr.drop1_full18_r1 import MODE_REF,STRATEGY
    c,reg,old,inputs,tables,prior=validate(a.project,a.stage)
    proof=read(a.stage/CPU_PROOF)
    assert proof['production_CPU_accepted'] and proof['source_revision']==reg['source_revision']==a.source_revision
    assert proof['registration_sha256']==sha(a.stage/'registration.json') and proof['config_sha256']==sha(a.stage/CONFIG)
    assert os.environ['CUDA_VISIBLE_DEVICES']==a.gpu_uuid and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
    assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==(a.project/'.sync/gpu-locks'/(a.gpu_uuid+'.lock')).resolve()
    os.fstat(int(os.environ['WC_LOCK_FD']))
    calibration,specs,refs,evidence=inputs
    samples={r['name']:InferenceArguments(**r) for r in c['requests']}
    setupdata=read(a.project/'configs/f1_setup.json')
    setup=SetupArguments(**{**setupdata,'keep_going':True,'worldcache_enabled':True,'output_dir':str(a.project/'outputs'/RUN)})
    assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
    out=a.project/'outputs'/RUN;assert out.is_dir() and not (out/'runner.json').exists()
    state=dict(status='POLICY_ASSETS_MODEL_LOADING',pid=os.getpid(),source_revision=a.source_revision,
        config_sha256=sha(a.stage/CONFIG),registration_sha256=sha(a.stage/'registration.json'),
        scope_counts=COUNTS,matrix=matrix(),runs=[],started_unix=time.time(),model_loads=0)
    def save():
        atomic_json(out/'runner.json',state)
        rows=full_rows(state['runs'])
        atomic_json(out/'runner-health.json',dict(phase=state['status'],registered_paths=14,
            completed_paths=sum(r['status'] in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED') for r in rows),
            running_paths=sum(r['status']=='RUNNING' for r in rows),
            not_reached_paths=sum(r['status']=='NOT_REACHED' for r in rows),
            failed_paths=sum(r['status']=='TECH_FAILED' for r in rows),
            active_path=next((r['id'] for r in rows if r['status']=='RUNNING'),None)))
    save();init_environment();init_output_dir(out,profile=False)
    try:
        install_core_inference_registration(setup.model,setup.experiment)
        start=time.perf_counter();inference=im.Inference(setup);torch.cuda.synchronize()
        state.update(load_seconds=time.perf_counter()-start,model_loads=1)
        model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
        mode=establish_shared_eval(net,read(a.stage/MODE_REF)['module_types']);verify_shared_eval(net,mode)
        assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,6) and len(net.blocks)==28
        settings=old['historical_wc_settings']
        wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
        versions=[(v,v._version) for v in net.parameters()]
        state['status']='POLICY_ASSETS_COMPLETE14_RUNNING';save()
        for planned in matrix():
            row={**planned,'status':'RUNNING','started_unix':time.time()};state['runs'].append(row);save()
            initial.restore();assert initial.fingerprint()==origin;verify_shared_eval(net,mode)
            torch.cuda.reset_peak_memory_stats()
            result=execute(inference,samples[planned['scene']],planned['mode'],table_parameters=tables,
                previous_parameters=prior,runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,
                calibration=calibration,specs=specs[STRATEGY],inference_module=im,
                output=out/planned['id'],expected_shape=old['expected_real_shape'],audit=True)
            directory=out/planned['id']
            for key,filename in [('guided','all36-guided.pt'),('final_latent','final-latent.pt')]:
                values=result.pop(key,None)
                if values is not None:
                    path=directory/filename
                    with path.open('xb') as f:torch.save({key:values},f)
                    result[key+'_artifact']=dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size)
                    result[key+'_tree_sha256']=tree_digest(values)
            row.update(result,ended_unix=time.time(),allocated_peak_bytes=torch.cuda.max_memory_allocated(),
                reserved_peak_bytes=torch.cuda.max_memory_reserved());save()
            assert row['status'] in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED')
            assert row['request_memory_lifecycle']['owners_alive_after']==0
            assert all(v._version==version for v,version in versions)
        initial.restore();assert initial.fingerprint()==origin
        state['status']='POLICY_ASSETS_GPU_COMPLETE_INDEPENDENT_RAW_POST_REQUIRED';save()
    except BaseException as error:
        if state['runs'] and state['runs'][-1]['status']=='RUNNING':
            state['runs'][-1].update(status='TECH_FAILED',error_type=type(error).__name__,error=str(error))
        state.update(status='POLICY_ASSETS_TECHNICAL_STOP_FULL_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
    finally:
        cleanup_environment();state['ended_unix']=time.time();state['registered_rows']=full_rows(state['runs']);save()


if __name__=='__main__':main()
