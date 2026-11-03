"""Real pinned sampler/cache/UniPC with tiny CPU modules; no model weights/GPU."""
import json
import inspect
import itertools
import random
from textwrap import dedent
import types
import typing
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE),str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'vendor/CosmosPredict25'),str(ROOT/'vendor/CosmosPredict25/packages/cosmos-oss')]
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['NVIDIA_VISIBLE_DEVICES'] = 'void'
import torch
from sampling import execute, policy_for
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.policy_generator_r1.production_sampling import execute as full_policy
import check_cara_pg_production_sampling_cpu_r1 as fixture


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net
    model.config.state_ch=8;model.config.conditional_frame_timestep=.1
    model.precision,net.use_wan_fp32_strategy=torch.float32,False
    class Head(torch.nn.Module):
        def forward(self,x,*args,**kwargs):return x+.01*x.square()
    net.final_layer=Head().eval()
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=fixture.load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    model.conditioner.get_condition_with_negative_prompt=lambda batch:tuple(
        cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True]))
        .set_video_condition(torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,8,2,8,8),None)
    card=json.loads((ROOT/'plans/cara_next_stage_20261103/f19_speed190_cal/CAL35_MANIFEST_R1.json').read_text())
    card['settings']['worldcache_flow_enabled']=flow
    common=dict(runtime=runtime,wc=wc,rf=rf,inference_module=inference_module,expected_shape=[1,8,2,8,8])
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
    root=Path(artifact_root)/str(flow);root.mkdir()
    initial.restore()
    record=execute(inference,selected[0],card=card,common=common,output=root/'record',record_root=root/'states')
    profile=profile_from(card['profile'])
    controls=[]
    # Each resumed single-C must equal a separately executed complete single-C request.
    for target in range(8,35,2):
        initial.restore()
        suffix=execute(inference,selected[0],card=card,common=common,output=root/f'suffix_{target}',
            checkpoint=root/'states'/f'state_before_{target:02d}.pt',target=target)
        initial.restore()
        full=full_policy(inference,selected[0],profile=profile,policy=policy_for(profile,target),
            output=root/f'full_{target}',settings=card['settings'],calibration=None,specs={},audit=True,**common)
        assert torch.equal(suffix['final_latent'],full['final_latent']),target
        assert Path(suffix['video_path']).read_bytes()==Path(full['video_path']).read_bytes(),target
        assert suffix['guided_pairs']==suffix['solver_steps']==37-target
        controls.append(dict(t=target,suffix_updates=37-target,full_latent_and_RGB_equal=True))
    for target in (8,34):
        initial.restore()
        suffix=execute(inference,selected[0],card=card,common=common,output=root/f'unchanged_{target}',
            checkpoint=root/'states'/f'state_before_{target:02d}.pt')
        assert torch.equal(record['final_latent'],suffix['final_latent'])
    metrics=json.loads((root/'states/metrics.json').read_text())
    assert len(metrics)==36 and metrics[0]['guided_delta_RMS'] is None
    assert all(r['v_c_delta_RMS'] is not None and r['first_block_rel_l1_u'] is not None for r in metrics[1:])
    assert len(list((root/'states').glob('latent_before_*.pt')))==36
    initial.restore()
    # Complete physical routing, with an explicitly declared frozen request fixture.
    # The production class is separately imported in the Phase2 Linux admission.
    class FrozenSample(type(selected[0])):
        model_config={'frozen':True}
        def __init__(self,**values):
            for key,value in values.items():object.__setattr__(self,key,value)
        def __setattr__(self,key,value):raise AttributeError('Frozen CPU request fixture')
        def model_dump(self,**kwargs):return dict(vars(self))
        @classmethod
        def model_validate(cls,value):return cls(**value)
    production_card=json.loads((HERE/'manifest.json').read_text())
    production_card['settings']['worldcache_flow_enabled']=flow
    samples={r['name']:FrozenSample(**{**{k:v for k,v in r.items() if k!='partition'},'resolution':'16,16'})
             for r in production_card['inputs']}
    # Existing clean Native's explicit CPU adapter uses the unchanged all-D WC body.
    def native(self,*args,**kwargs):
        threshold=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*args,**kwargs)
        finally:self.worldcache_rel_l1_thresh=threshold
    from runner import collect_loaded
    from wcomr.h0_mode import mode_snapshot
    class Storage:
        def check(self):return None
    collection=collect_loaded(inference,samples,production_card,dict(common,CPU_native=native),
        root/'collection',Storage(),mode_snapshot(net)['module_types'],cpu_validation=True)
    assert collection['status']=='COMPLETE_PENDING_RELEASE_SCORING'
    assert len(collection['rows'])==143 and all(r['status']=='COMPLETE' for r in collection['rows'])
    return [dict(flow=flow,controls=controls,unchanged_suffix_controls=2,
                 Native_metrics_steps=36,latent_states=36,sensitivity_states=14,
                 complete_physical_requests=143,CPU_request_class='DECLARED_FROZEN_FIXTURE')]


if __name__ == '__main__':
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('CPU dry-run forbids CUDA')
    torch.cuda._lazy_init=forbidden
    from analyze import reconstruct,permutation_test
    rng=random.Random(0)
    for weights in ([1.]*36,[1.+i%3 for i in range(36)],[rng.random()+.01 for _ in range(36)]):
        for nD in (34,35):
            candidates=[]
            for omitted in itertools.combinations(range(8,36),36-nD):
                dense=[t for t in range(1,37) if t not in omitted]
                intervals=[sum((t-a)*weights[t-1] for t in range(a+1,b)) for a,b in zip(dense,dense[1:])]
                candidates.append((max(intervals),sum(e*e for e in intervals),tuple(dense)))
            actual=reconstruct(weights,nD)
            assert (actual['peak'],actual['sum_square'],tuple(actual['dense_steps']))==min(candidates)
    assert permutation_test([.2]*4,[.2]*4,.027)==1/70
    assert permutation_test([.2]*4,[.3]*4,.027)==1
    from test_cara_read_write_transition_r1 import modules,pinned_functions
    runtime=Path(os.environ.get('CARA_READ_WRITE_RUNTIME',ROOT/'.sync/read-write-pinned-runtime-r1'))
    wc,rf=modules()
    vars(wc).update({name:getattr(typing,name) for name in ('Optional','Tuple','Dict','List','Union')})
    rf.parallel_state=types.SimpleNamespace(is_initialized=lambda:False)
    rf.broadcast_split_tensor=lambda tensor,**kwargs:tensor
    rf.NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames';rf.DataType=wc.DataType
    pinned_functions(runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py',
        ['get_velocity_fn_from_batch'],vars(rf))
    rf.Video2WorldModelRectifiedFlow.get_velocity_fn_from_batch=rf.get_velocity_fn_from_batch
    old=fixture.load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(old.exercise))
    source=source.replace('from cosmos_predict2._src.predict2.inference import worldcache_utils as wc','wc=_wc')
    source=source.replace('from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf','rf=_rf')
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    source=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    scope={**vars(old),'_body':body,'_wc':wc,'_rf':rf}
    exec(compile(source,__file__+'#CPU-fixture','exec'),scope)
    with tempfile.TemporaryDirectory(prefix='cara-sensitivity-cpu-') as directory:
        result=fixture.load('check_full_sampling').run(runtime,exercise=lambda **kwargs:
            scope['exercise'](runtime=runtime,tensor_loader=None,artifact_root=Path(directory),**kwargs))
    print(json.dumps(dict(passed=True,torch_version=torch.__version__,weighted_age_exhaustive_controls=6,
        exact_permutation_controls=2,pinned_sampler_cache_UniPC=result,CUDA_initialized=torch.cuda.is_initialized(),
        Cosmos_weights_loaded=False,GPU_submissions=0,ledger_written=False)))
