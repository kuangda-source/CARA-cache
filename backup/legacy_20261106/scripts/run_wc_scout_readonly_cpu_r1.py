#!/usr/bin/env python3
"""Read five frozen old artifacts on CPU in an independent stage. No generation."""
import gc
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()


def main():
    stage=Path(sys.argv[1]).resolve()
    root=stage.parent.parent
    assert stage.parent.name=='.sync' and stage.name.startswith('wc-scout-readonly-cpu-')
    started=time.time()
    reg=json.loads((stage/'registration.json').read_text())
    for f,h in reg['payload_sha256'].items(): assert sha(stage/f)==h,f
    plan=json.loads((stage/'plans/scouts_20261018/SCOUT_READONLY_CPU_PLAN.json').read_text())
    before=plan['original_metadata_sha256']
    assert all(sha(Path(p))==h for p,h in before.items())
    pool=json.loads((root/'reports/gpu-budget-v2.json').read_text())
    # N10 is not opened here. A still-active project GPU job defers CPU work.
    assert not any(j['status']=='RESERVED_OR_RUNNING' for j in pool['jobs'].values())
    os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',
                      HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import torch
    torch.set_num_threads(2)
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**k): raise RuntimeError('This scout only reads existing CPU tensors')
    torch.cuda._lazy_init=forbidden
    spec=importlib.util.spec_from_file_location('scout_math',stage/'src/wcomr/scout_diagnostics_r1.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    checks=[]
    def load_asset(v):
        a=v['artifact'];p=Path(a['path']).resolve()
        assert (root/'outputs').resolve() in p.parents
        assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256'],str(p)
        obj=torch.load(p,map_location='cpu',weights_only=True)
        assert set(obj)=={'guided'} and len(obj['guided'])==36
        guides=obj['guided']
        assert all(x.device.type=='cpu' and x.is_floating_point() and list(x.shape)==[1,16,24,54,96]
                   and bool(torch.isfinite(x).all()) for x in guides)
        checks.append(dict(role=v['role'],scene=v['scene'],original_id=v['original_id'],
                           artifact=a,all36_finite_geometry=True))
        return guides
    guides={a['role']:load_asset(a) for a in plan['assets']}
    for role in ('S25-C','S25-A'):
        assert all(torch.equal(x,y) for x,y in zip(guides[role][:20],guides['S26-C'][:20]))
    assert len({tuple(v['scheduler_timesteps']) for v in plan['assets']})==1
    n12=mod.amplitude_and_direction(guides['S25-C'][20],guides['S25-A'][20],guides['S26-C'][20],torch=torch)
    del guides;gc.collect()
    variations=[]
    for asset in plan['native_assets']:
        guides=load_asset(asset)
        variations.append(dict(scene=asset['scene'],**mod.native_variation(guides,plan['gains'],torch=torch)))
        del guides;gc.collect()
    schedules={}
    for key in ('gain_squared_weighted','unweighted'):
        normalized=[]
        for v in variations:
            den=sum(v[key][1:])/35
            assert den>0
            normalized.append([s/den for s in v[key]])
        score=[sum(q[i] for q in normalized)/len(normalized) for i in range(36)]
        schedules[key]=dict(scene_equal_scores=score,**mod.one_exchange(score,plan['base_mask']))
    assert all(sha(Path(p))==h for p,h in before.items())
    result=dict(status='SCOUT_REAL_SAVED_CPU_DIAGNOSTICS_COMPLETE',source_revision=reg['source_revision'],
        checks=checks,raw_artifacts_reloaded=5,N12_same_state_independent_inputs=1,
        same_state_basis='accepted seeded complete-state restore and first20 bit-equal guided outputs',
        direct_pre_action_latent_hash_saved=False,same_state_update=21,
        X_A_and_R=n12,X_S_native_variations=variations,X_S_schedule_candidates=schedules,
        primary_schedule='gain_squared_weighted',gain_semantics=plan['gain_semantics'],
        endpoint_rank_or_gate_evaluation=None,missing_current_and_previous_probe_tensors=True,
        original_metadata_unchanged=True,model_loads=0,new_teacher_calls=0,new_generator_runs=0,
        GPU_submissions=0,new_GPUh=0,CUDA_initialized=torch.cuda.is_initialized(),ledger_written=False,
        original_stage_written=False,CPU_wall_seconds=time.time()-started,
        local_error_or_schedule_score_is_endpoint_benefit=False)
    dest=stage/'result.json';assert not dest.exists()
    dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,allow_nan=False))


if __name__=='__main__': main()
