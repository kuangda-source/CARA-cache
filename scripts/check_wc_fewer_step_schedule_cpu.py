#!/usr/bin/env python3
"""Pinned actual UniPC35/23 CPU grids and state reset; no model or GPU."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import time

PINNED={
 'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py':'f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3',
 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py':'c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87'}


def check(runtime):
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**k):raise RuntimeError('CUDA forbidden in schedule preflight')
    torch.cuda._lazy_init=forbidden
    for name,digest in PINNED.items():
        assert hashlib.sha256((runtime/name).read_bytes()).hexdigest()==digest,name
    model=ast.parse((runtime/list(PINNED)[1]).read_text())
    constructors=[node for node in ast.walk(model) if isinstance(node,ast.Call)
                  and isinstance(node.func,ast.Name) and node.func.id=='FlowUniPCMultistepScheduler']
    assert len(constructors)==1
    kwargs={v.arg:ast.literal_eval(v.value) for v in constructors[0].keywords}
    assert kwargs=={'num_train_timesteps':1000,'shift':1,'use_dynamic_shifting':False}
    spec=importlib.util.spec_from_file_location('pinned_flow_unipc',runtime/list(PINNED)[0])
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    scheduler=m.FlowUniPCMultistepScheduler(**kwargs)
    rows=[]
    for requested in (35,23,35):
        scheduler.set_timesteps(requested,device='cpu',shift=5,use_kerras_sigma=True)
        assert scheduler.num_inference_steps==len(scheduler.timesteps)==requested+1
        assert len(scheduler.sigmas)==requested+2 and scheduler.sigmas[-1]==0
        assert scheduler.timesteps.dtype==torch.int64 and scheduler.sigmas.dtype==torch.float32
        assert scheduler.timesteps.device.type==scheduler.sigmas.device.type=='cpu'
        assert scheduler._step_index is None and scheduler._begin_index is None
        assert scheduler.lower_order_nums==0 and scheduler.last_sample is None
        assert all(v is None for v in scheduler.model_outputs)
        generator=torch.Generator(device='cpu').manual_seed(0)
        value=torch.randn((1,2,3,4),generator=generator)
        for timestep in scheduler.timesteps:
            value=scheduler.step(torch.ones_like(value)*.05,timestep,value,return_dict=False,generator=generator)[0]
            assert torch.isfinite(value).all()
        assert scheduler._step_index==requested+1
        rows.append({'requested_steps':requested,'actual_grid_steps':len(scheduler.timesteps),
            'timesteps':scheduler.timesteps.tolist(),'sigmas':scheduler.sigmas.tolist(),
            'CPU_constant_velocity_step_updates':scheduler._step_index,
            'CPU_toy_final_raw_sha256':hashlib.sha256(value.numpy().tobytes()).hexdigest()})
    assert rows[0]==rows[2] and rows[0]['actual_grid_steps']==36 and rows[1]['actual_grid_steps']==24
    assert not torch.cuda.is_initialized()
    return {'status':'PINNED_UNIPC_CPU35_TO36_23_TO24_RESET_AND_TOY_UPDATES_PASS_NOT_NATIVE_PIPELINE',
        'CPU_only':True,'cuda_initialized':False,'weights_loaded':False,'forward_executed':False,
        'upstream_sha256':PINNED,'official_constructor_kwargs':kwargs,'rows':rows,
        'quality_acceptance':False,'GPU_speed_claim':False,
        'limits':['Actual pinned scheduler on CPU; constant-velocity fixture is not a model prediction.',
            'Grid24 is verified for23 requested Karras steps, but complete Native23 pipeline, CFG calls, artifact and parity remain unverified.',
            'No linear runtime discount, same-state trajectory comparison, new GPU admission or frozen live-card change.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('runtime','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();start=time.perf_counter();r=check(a.runtime)
    r.update(CPU_wall_seconds=time.perf_counter()-start,check_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':r['status'],'CPU_seconds':r['CPU_wall_seconds'],'grid_steps':[v['actual_grid_steps'] for v in r['rows']]}))
