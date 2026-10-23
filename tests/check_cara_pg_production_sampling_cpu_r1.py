"""Actual pinned sampler/WC/RF; small declared CPU weights and decoder only."""
import copy
import inspect
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.policy_generator_r1.production_sampling import execute, PolicyReadout, ReadoutFailure
from wcomr.policy_generator_r1.interval_grammar import Profile, Edge, compile_policy
from wcomr.policy_interval_assets_r1 import PROFILE
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr import clean_speed20_r1 as clean


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=module_from_spec(spec);spec.loader.exec_module(m);return m


def test_profile():
    d={k:PROFILE[k] for k in ('horizon','protected_dense','max_source_age','min_C_anchors','min_A_anchors','alpha_candidates')}
    d['protected_dense']=tuple(d['protected_dense']);d['alpha_candidates']=tuple(d['alpha_candidates'])
    return Profile(**d,identity='DECLARED_CPU_ONLY')


def plans():
    p=test_profile();out={}
    out['ALL_D']=compile_policy(p,[Edge(t,t+1) for t in range(1,37)])
    for name,alpha in [('C',0.),('HALF',.5),('ONE',1.)]:
        bounds=list(range(1,8))+[12,21,30,36,37]
        out[name]=compile_policy(p,[Edge(s,r,(s+1,r-1) if alpha and r>s+1 else (),alpha if r>s+1 else 0.) for s,r in zip(bounds,bounds[1:])])
    bounds=list(range(1,8))+[13,24,36,37]
    out['MIXED']=compile_policy(p,[Edge(s,r,(s+2,r-2),.5 if s==7 else 1.) if r-s>3 else Edge(s,r) for s,r in zip(bounds,bounds[1:])])
    return p,out


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    model.config.state_ch=8
    class Head(torch.nn.Module):
        def forward(self,x,*a,**kw):return x+.01*x.square()
    net.final_layer=Head().eval();net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    model.conditioner.get_condition_with_negative_prompt=lambda batch:tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b),fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.get_data_and_condition=lambda b:(None,torch.zeros(1,8,2,8,8),None)
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    profile,policy=plans();root=Path(artifact_root)/('flow_'+str(flow));result={};paths=0
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=None,specs={},inference_module=inference_module,expected_shape=[1,8,2,8,8],audit=True)
    def native(self,*a,**kw):
        threshold=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=threshold
    try:
        initial.restore();n=clean.execute(inference,selected[0],'NATIVE',output=root/'native',CPU_native=native,**common);paths+=1
        for label,plan in policy.items():
            initial.restore();r=execute(inference,selected[0],profile=profile,policy=plan,output=root/label,**common);paths+=1
            assert r['status']=='COMPLETE' and r['guided_pairs']==r['solver_steps']==36
            assert [h['actual'] for h in r['semantic_history']]==plan['actions']
            assert all(h['fallback_reason'] is None for h in r['semantic_history'])
            for t,h in enumerate(r['semantic_history'],1):
                if h['actual']!='D':
                    expected=[i for i,a in enumerate(plan['actions'][:t-1],1) if a=='D'][-2:]
                    assert h['source_history']['past_D_steps']==[expected,expected]
                    assert h['source_history']['shared_alpha']==(plan['shared_alpha'][t-1] or 0.)
            result[label]=r
        assert all(torch.equal(x,y) for x,y in zip(n['guided'],result['ALL_D']['guided']))
        assert torch.equal(n['final_latent'],result['ALL_D']['final_latent'])
        assert Path(n['video_path']).read_bytes()==Path(result['ALL_D']['video_path']).read_bytes()
        # A reused request object obtains a fresh owner and identical trajectory.
        initial.restore();repeat=execute(inference,selected[0],profile=profile,policy=policy['MIXED'],output=root/'repeat',**common);paths+=1
        assert all(torch.equal(x,y) for x,y in zip(repeat['guided'],result['MIXED']['guided']))
        # After a complete pair, fail the candidate fusion and require restored D.
        base_end=PolicyReadout.end
        def injected(self,actual,action):
            if self.current['step']==8 and action=='CC': raise ReadoutFailure('Injected nonfinite readout')
            return base_end(self,actual,action)
        initial.restore()
        with clean.patched(PolicyReadout,'end',injected):
            fallback=execute(inference,selected[0],profile=profile,policy=policy['ONE'],output=root/'fallback',**common);paths+=1
        assert fallback['semantic_history'][7]['actual']=='D'
        assert fallback['semantic_history'][7]['fallback_reason']=='NONFINITE_READOUT_RESTORED_THEN_FULL_D'
        assert fallback['semantic_history'][8]['source_history']['past_D_steps']==[[7,8],[7,8]]
        # Exact independently compiled mask with D8 must match the recovered path.
        altered=copy.deepcopy(policy['ONE']['actions']);altered[7]='D';bounds=[i for i,a in enumerate(altered,1) if a=='D']+[37]
        fallback_plan=compile_policy(profile,[Edge(s,r,(s+1,r-1),1.) if r>s+1 else Edge(s,r) for s,r in zip(bounds,bounds[1:])])
        initial.restore();ref=execute(inference,selected[0],profile=profile,policy=fallback_plan,output=root/'fallback_reference',**common);paths+=1
        assert all(torch.equal(x,y) for x,y in zip(ref['guided'],fallback['guided']))
        initial.restore()
        with clean.patched(inference,'generate',lambda *a,**kw:[]):
            rejected=execute(inference,selected[0],profile=profile,policy=policy['MIXED'],output=root/'rejected',**common)
        assert rejected['status']=='TEXT_REJECTED' and not rejected['semantic_history']
        initial.restore()
        def bad_writer(*a,**kw):raise OSError('Injected writer failure')
        with clean.patched(inference_module,'save_img_or_video',bad_writer):
            try:execute(inference,selected[0],profile=profile,policy=policy['MIXED'],output=root/'writer_failure',**common)
            except OSError:pass
            else:raise AssertionError('Writer failure lost')
        initial.restore();assert initial.fingerprint()==origin
        return [dict(flow=flow,status='PASS',complete_paths=paths,full36_CFG72=True,Native_allD_guided_final_RGB_equal=True,
            sparse_true_D_history=True,half_and_one_deployed=True,mixed_C_A_window=True,request_reset_equal=True,
            nonfinite_restored_fullD_equals_independent_policy=True,text_rejection_retained=True,writer_failure_cleanup=True,
            actual_Cosmos_weights=False,real_generated_video=False)]
    finally:initial.restore()


def run(runtime,artifact_root):
    old=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(old.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    source=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    ns={**vars(old),'_body':body};exec(compile(source,__file__+'#pinned-Toy-setup','exec'),ns)
    return load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),tensor_loader=None,artifact_root=artifact_root,**kw))
