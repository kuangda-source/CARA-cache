"""Run the actual S1 prefix/local probes and eight S2 routes with tiny weights."""
import copy
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile
from textwrap import dedent
import types
import typing
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'tests'),str(HERE)]
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
import torch
import check_cara_pg_production_sampling_cpu_r1 as fixture
from plans.cara_next_stage_20261105.sparse_refresh_probe import collector
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.h0_mode import mode_snapshot


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net
    model.config.state_ch=8;model.config.conditional_frame_timestep=.1
    model.precision,net.use_wan_fp32_strategy=torch.float32,False
    net.blocks=torch.nn.ModuleList([copy.deepcopy(net.blocks[0]) for _ in range(28)])
    class Head(torch.nn.Module):
        def forward(self,x,*args,**kwargs):return x+.01*x.square()
    net.final_layer=Head().eval()
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=fixture.load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    model.conditioner.get_condition_with_negative_prompt=lambda batch:tuple(
        cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True]))
        .set_video_condition(torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,8,2,8,8),None)
    class FrozenSample(type(selected[0])):
        model_config={'frozen':True}
        def __init__(self,**values):
            for key,value in values.items():object.__setattr__(self,key,value)
        def __setattr__(self,key,value):raise AttributeError('Frozen CPU request fixture')
        def model_dump(self,**kwargs):return dict(vars(self))
        @classmethod
        def model_validate(cls,value):return cls(**value)
    card=json.loads((HERE/'manifest.json').read_text());card['settings']['worldcache_flow_enabled']=flow
    samples={r['name']:FrozenSample(**{**{k:v for k,v in r.items() if k!='partition'},'resolution':'16,16'}) for r in card['inputs']}
    common=dict(runtime=runtime,wc=wc,rf=rf,inference_module=inference_module,expected_shape=[1,8,2,8,8])
    class Storage:
        def check(self):pass
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));results=[]
    original_gate=collector.s1_gate
    for admit in (False,True):
        initial.restore();root=Path(artifact_root)/f'{flow}_{admit}'
        def gate(**measurements):
            result=original_gate(**measurements)
            # CPU timings are not a GPU cost admission. Force each branch only
            # in this declared fixture after exercising the real measurement.
            return dict(result,gate_passed=admit)
        with patch.object(collector,'s1_gate',gate):
            result=collector.collect_loaded(inference,samples,card,common,root,Storage(),mode_snapshot(net)['module_types'],cpu_validation=True)
        s1=json.loads((root/'s1.json').read_text())
        assert len(s1['local29'])==20 and not s1['actual_GPU_measurement']
        assert s1['next30']['raw_sync_same_state'] and not list((root/'s1_prefix').glob('*.mp4'))
        assert result['status']==('COMPLETE_PENDING_RELEASE_SCORING' if admit else 'S1_GATE_STOP')
        assert sum(r['status']=='COMPLETE' for r in result['rows'])==(8 if admit else 0)
        if admit:
            for row in result['rows']:
                actual=''.join(h['actual'] for h in row['result']['semantic_history'])
                assert actual==card['roles'][row['slot']['role']]['mask']
        results.append(dict(flow=flow,fixture_gate_passed=admit,S1_parent_steps=28,local_evaluations=20,
            completed_S2=8 if admit else 0,no_S1_video=True,raw_sync_same_state=True))
    return results


def run():
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('Runtime CPU fixture forbids CUDA')
    torch.cuda._lazy_init=forbidden
    from test_cara_read_write_transition_r1 import modules,pinned_functions
    runtime=Path(os.environ.get('CARA_READ_WRITE_RUNTIME',ROOT/'.sync/read-write-pinned-runtime-r1'))
    wc,rf=modules();vars(wc).update({name:getattr(typing,name) for name in ('Optional','Tuple','Dict','List','Union')})
    rf.parallel_state=types.SimpleNamespace(is_initialized=lambda:False)
    rf.broadcast_split_tensor=lambda tensor,**kwargs:tensor
    rf.NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames';rf.DataType=wc.DataType
    pinned_functions(runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py',['get_velocity_fn_from_batch'],vars(rf))
    rf.Video2WorldModelRectifiedFlow.get_velocity_fn_from_batch=rf.get_velocity_fn_from_batch
    old=fixture.load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(old.exercise))
    source=source.replace('from cosmos_predict2._src.predict2.inference import worldcache_utils as wc','wc=_wc')
    source=source.replace('from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf','rf=_rf')
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    source=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    scope={**vars(old),'_body':body,'_wc':wc,'_rf':rf};exec(compile(source,__file__+'#tiny-setup','exec'),scope)
    with tempfile.TemporaryDirectory(prefix='cara-sparse-runtime-CPU-') as directory:
        results=fixture.load('check_full_sampling').run(runtime,exercise=lambda **kw:scope['exercise'](
            runtime=runtime,tensor_loader=None,artifact_root=Path(directory),**kw))
    from plans.cara_next_stage_20261105.sparse_refresh_probe import ops
    base=ops.load_base(HERE/'manifest.json')
    for name in ('PRECHECK','INSTALL','CPU','CPU_STATUS','PROVISION','STORAGE_STATUS','ADMIT','CENTRAL','DISPATCH','STATUS','CAPTURE'):
        compile(getattr(base,name),'<sparse-'+name+'>','exec')
    calls=[]
    def memory_refusal(operator,data,**kwargs):
        calls.append(operator)
        return dict(MemAvailable_kib=49*1024**2)
    with tempfile.TemporaryDirectory(prefix='cara-sparse-launch-gate-CPU-') as directory:
        target=Path(directory)/'launch.json'
        with patch.object(ops,'rpc',memory_refusal):
            try:ops.launch(base,'relay',target,base.GPU)
            except ValueError as error:assert '50GiB' in str(error)
            else:raise AssertionError('Low host memory reached launch')
        assert calls==[base.PRECHECK] and not target.exists()
    return dict(passed=True,paths=results,lifecycle=dict(operators_compile=True,
        low_memory_stops_before_authority_reservation_dispatch=True,mocked_RPC_calls=1),
        CUDA_initialized=torch.cuda.is_initialized(),GPU_submissions=0,ledger_writes=0,
        scope='Pinned sampler/RF/WC/UniPC with tiny28-block weights, declared decoder/writer and forced gate branches; not real timing/quality')


if __name__=='__main__':
    value=run();target=HERE/'runtime_cpu.json';target.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))
