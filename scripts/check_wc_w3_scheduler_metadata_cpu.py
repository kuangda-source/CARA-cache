#!/usr/bin/env python3
"""Real scheduler CPU: metadata-order sensitivity, with numerical positive control."""
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('project','selected-stage','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();start=time.monotonic()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.selected_stage/'src'))
    import torch
    assert not torch.cuda.is_initialized()
    def forbid(*a,**k):raise RuntimeError('Scheduler metadata CPU forbids CUDA/download')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid;torch.set_num_threads(2)
    from wcomr.mid_coverage import tree_digest
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    models=a.project/'runtime/cosmos_predict2/_src/predict2/models'
    factory=models/'text2world_model_rectified_flow.py';source=models/'fm_solvers_unipc.py'
    assert sha(factory)=='c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87'
    assert sha(source)=='f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3'
    call=next(n.value for n in ast.walk(ast.parse(factory.read_text())) if isinstance(n,ast.Assign)
              and any(isinstance(t,ast.Attribute) and t.attr=='sample_scheduler' for t in n.targets))
    assert isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=='FlowUniPCMultistepScheduler' and not call.args
    kwargs={k.arg:ast.literal_eval(k.value) for k in call.keywords}
    assert kwargs=={'num_train_timesteps':1000,'shift':1,'use_dynamic_shifting':False}
    spec=importlib.util.spec_from_file_location('frozen_actual_scheduler',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);cls=m.FlowUniPCMultistepScheduler
    base=cls(**kwargs);config=dict(base._internal_dict);metadata=config['_use_default_values']
    assert isinstance(metadata,list) and len(metadata)==len(set(metadata)) and set(metadata)<=set(config)-{'_use_default_values'}
    numerical={k:v for k,v in config.items() if k!='_use_default_values'}
    config_source=Path(sys.modules['diffusers.configuration_utils'].__file__)
    text=config_source.read_text();assert 'list(set(new_kwargs.keys()) - set(init_kwargs))' in text
    assert '_use_default_values' not in source.read_text()
    selected=json.loads((a.selected_stage/'paired-config.json').read_text());protocol=selected['sampling_protocol']
    def trajectory(order,changed=False):
        scheduler=cls(**(dict(kwargs,solver_order=1) if changed else kwargs))
        conf=dict(scheduler._internal_dict)
        if not changed:conf['_use_default_values']=order
        scheduler._internal_dict=type(scheduler._internal_dict)(conf)
        raw=tree_digest(scheduler._internal_dict)
        scheduler.set_timesteps(protocol['requested_steps'],device='cpu',use_kerras_sigma=True)
        assert scheduler.timesteps.tolist()==protocol['timesteps']
        x=torch.linspace(-0.8,0.9,12).reshape(1,3,2,2);outputs=[]
        for t in scheduler.timesteps:
            velocity=0.07*torch.sin(x)+0.03*x.square()+float(t)/100000.0
            x=scheduler.step(velocity,t,x,return_dict=False)[0];outputs.append(tree_digest(x))
        return raw,outputs,dict(scheduler._internal_dict)
    first,second=sorted(metadata),list(reversed(sorted(metadata)))
    h1,t1,c1=trajectory(first);h2,t2,c2=trajectory(second);hp,tp,cp=trajectory(first,True)
    assert h1!=h2 and t1==t2 and len(t1)==36 and tp!=t1
    assert {k:v for k,v in c1.items() if k!='_use_default_values'}=={k:v for k,v in c2.items() if k!='_use_default_values'}==numerical
    assert not torch.cuda.is_initialized()
    result={'status':'ACTUAL_SCHEDULER_DEFAULT_NAME_ORDER_CHANGES_RAW_HASH_NOT36_CPU_UPDATES_NUMERICAL_POSITIVE_CONTROL_PASS_NOT_EXACT_HISTORY_CAUSE',
        'CPU_seconds':time.monotonic()-start,'factory_sha256':sha(factory),'scheduler_sha256':sha(source),
        'diffusers_config_source_sha256':sha(config_source),'constructor_kwargs':kwargs,'numerical_config':numerical,
        'default_metadata_names':first,'permuted_metadata_names':second,'raw_config_hashes':[h1,h2],
        'numerical_only_config_sha256':tree_digest(numerical),'metadata_only_36_outputs_equal':True,
        'trajectory_output_hashes':t1,'solver_order_changed_positive_control_outputs':tp,'numerical_positive_control_detected':True,
        'original_historical_dictionary_values_not_available':True,'exact_two_historical_hashes_reconstructed':False,
        'old_GPU_and_H_T39_strict_criteria_unchanged':True,'real_video_or_quality_scores':0,'GPU_submissions':0,'CUDA_initialized':False}
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','CPU_seconds','metadata_only_36_outputs_equal','exact_two_historical_hashes_reconstructed')}))


if __name__=='__main__':main()
