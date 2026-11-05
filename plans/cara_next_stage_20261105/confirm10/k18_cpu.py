"""The real Requests adapter on pinned tiny Native18/19 and Native35/36 paths."""
import argparse
import copy
import json
import inspect
import os
from pathlib import Path
import sys
import tempfile
import types
import typing

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
import numpy as np
import torch
import check_cara_pg_p2_sampling_cpu_r1 as fixture
from wcomr.cara_f19_speed190_requests_r1 import Requests
from wcomr import clean_speed20_r1 as clean


def run(runtime,output):
    # Same pinned namespace setup as sensitivity/cpu_dry_run.py, without Cosmos imports on Mac.
    os.environ['CARA_READ_WRITE_RUNTIME']=str(runtime.resolve())
    from test_cara_read_write_transition_r1 import modules,pinned_functions
    wc,rf=modules()
    vars(wc).update({name:getattr(typing,name) for name in ('Optional','Tuple','Dict','List','Union')})
    rf.parallel_state=types.SimpleNamespace(is_initialized=lambda:False)
    rf.broadcast_split_tensor=lambda tensor,**kwargs:tensor
    rf.NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames';rf.DataType=wc.DataType
    pinned_functions(runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py',
        ['get_velocity_fn_from_batch'],vars(rf))
    rf.Video2WorldModelRectifiedFlow.get_velocity_fn_from_batch=rf.get_velocity_fn_from_batch
    old=fixture.load('check_cara_pg_production_sampling_cpu_r1')
    source=inspect.getsource(old.body);i=source.index('    try:\n        initial.restore();n=')
    source=source[:i]+'    return _native(inference,selected,wc,rf,common,initial,profile,root,native,flow,inference_module)\n'
    scope={**vars(old),'_native':body};exec(compile(source,__file__+'#tiny-setup','exec'),scope)
    exercise=fixture.load('check_partial_mlp_guided_sampling_cpu_r1');source=inspect.getsource(exercise.exercise)
    source=source.replace('from cosmos_predict2._src.predict2.inference import worldcache_utils as wc','wc=_wc')
    source=source.replace('from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf','rf=_rf')
    i=source.index('    results=[]\n    try:');j=source.index('\n    finally:\n',i)+1
    source=source[:i]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[j:]
    env={**vars(exercise),'_body':scope['body'],'_wc':wc,'_rf':rf}
    exec(compile(source,__file__+'#pinned-setup','exec'),env)
    return fixture.load('check_full_sampling').run(runtime,exercise=lambda **kw:
        env['exercise'](runtime=runtime,tensor_loader=None,artifact_root=output,**kw))


def body(inference,selected,wc,rf,common,initial,profile,root,native,flow,inference_module):
    class FrozenSample(type(selected[0])):
        model_config={'frozen':True}
        def __init__(self,**values):
            for key,value in values.items():object.__setattr__(self,key,value)
        def __setattr__(self,key,value):raise AttributeError('Frozen CPU request fixture')
        def model_dump(self,**kwargs):return dict(vars(self))
        @classmethod
        def model_validate(cls,value):return cls(**value)
    sample=FrozenSample(**vars(selected[0]));original=sample.model_dump()
    card=json.loads((HERE/'manifest.json').read_text())
    grids=json.loads((ROOT/'reports/cara_PG_Native18to35_committed_scheduler_CPU_20261023.json').read_text())['rows']
    card['roles']={f'NATIVE{n}':dict(kind='native',requested_steps=n,expected_updates=n+1,
        schedule=next(row for row in grids if row['requested_steps']==n)) for n in (18,35)}
    card['matrix']=[dict(id=f'NATIVE{n}',member=sample.name,role=f'NATIVE{n}',seed=0,
        eligible_clean_time=True,audit=False) for n in (18,35)]
    args={k:common[k] for k in ('runtime','wc','rf','inference_module','expected_shape')}
    args['CPU_native']=native
    request=Requests(inference,{sample.name:sample},card,args,cpu_validation=True)
    frames=[];writer=inference_module.save_img_or_video
    def write(video,path,fps):
        frames.append(np.moveaxis(np.array(video,copy=True),0,-1).shape[0])
        return writer(video,path,fps)
    checks=[]
    with clean.patched(inference_module,'save_img_or_video',write):
        for slot in card['matrix']:
            initial.restore()
            result=request(slot,root/slot['id'])
            n=card['roles'][slot['role']]['requested_steps']
            assert result['status']=='COMPLETE' and result['solver_steps']==result['actual_updates']==n+1
            assert result['full_block_calls']==[2*(n+1)]*2 and result['cache_installed'] is False
            assert frames[-1]==93 and sample.model_dump()==original
            checks.append(dict(requested_steps=n,actual_updates=n+1,full_block_calls=result['full_block_calls'],
                frames=frames[-1],flow=flow,frozen_original_unchanged=True,timed_adapter_used=True))
    # Current P/CAL manifests lack per-role grids; normalize once without mutation.
    legacy=copy.deepcopy(card);legacy['roles']={'NATIVE35':dict(kind='native',requested_steps=35)}
    older=Requests(inference,{sample.name:sample},legacy,args,cpu_validation=True)
    assert older.roles['NATIVE35']['schedule']==legacy['schedule']
    assert older.roles['NATIVE35']['expected_updates']==36 and 'expected_updates' not in legacy['roles']['NATIVE35']
    initial.restore()
    return checks


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('Native adapter CPU check forbids CUDA')
    torch.cuda._lazy_init=forbidden
    with tempfile.TemporaryDirectory(prefix='cara-k18-cpu-') as directory:
        result=run(a.runtime,Path(directory))
    value=dict(passed=True,checks=result['checks'],CUDA_initialized=torch.cuda.is_initialized(),
        GPU_submissions=0,model_weights_loaded=False,legacy_roles_normalized_without_mutation=True,
        scope='Pinned sampler/RF/UniPC and real timed Requests adapter; tiny CPU weights, frozen request fixture, synthetic93 frames. Not GPU performance or LPIPS evidence.')
    assert not value['CUDA_initialized']
    a.output.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))
