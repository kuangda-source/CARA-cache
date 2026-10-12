"""Actual two-flow full parents and two complete endpoint suffixes per cell."""
import copy,inspect,json
from pathlib import Path
from textwrap import dedent
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.math_n2_sampling_owner_r1 import MathSamplingOwner
from wcomr.pi0_readout_suffix8_r1 import pi0_readout_suffix_install
from wcomr.rv0_causal import original_decode_tails
from wcomr.mid_coverage import tree_digest


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m


def select(scene,history,source,phase,target):
    rows=[]
    for h in history:
        d=h['source_policy']['decision'];state=d['state_before'];n=d['step'];born=state[2]
        if (state[1]!=source or ('EARLY' if n<25 else 'LATE')!=phase or h['protected']
                or not d['both_sources_ready'] or d['action']!='C' or born is None):continue
        age=n-born
        if 1<=age<=6:rows.append({'step':n,'age':age,'source_birth':born,'true_D_anchor':state[0],'actual_pi0_action':'C'})
    assert rows,'Declared Toy regime lacks a natural C in requested source/phase'
    return {'scene':scene,'source':source,'phase':phase,'target_age':target,
        'chosen':min(rows,key=lambda r:(abs(r['age']-target),r['step'])),
        'default_readout':'A' if source=='D' else 'C','alternative_readout':'C' if source=='D' else 'A'}


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    gains={n:1. for n in range(1,37)}
    for n in (8,9,10,25,27,28,29,30,31,32,33,34,35):gains[n]=0.
    gains[26]=1000.
    cal=Calibration('SYNTHETIC_SUFFIX8_PHASE_COVERAGE',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},gains)
    spec={'threshold':.04,'costs':Costs('SYNTHETIC_SUFFIX8',1.,4.,3.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_SUFFIX8',.0001,.3,early_creation_floor=.0001,late_creation_floor=10.),
        'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
    specs={'A_CPD_BETA1_ONE_PHASE':spec};params={'gamma':.5,'fingerprint':'SYNTHETIC_ONLY'}
    config={**config,'paired_prefix_reserve_bytes':config.get('paired_prefix_reserve_bytes',0)}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    net0,pipe0=net.forward,inference.pipe.worldcache_enabled;results=[]
    decoder,writer,tails=original_decode_tails(runtime,inference_module);ordinary_writer=inference_module.save_img_or_video
    cells=(('D','EARLY',3),('D','LATE',2),('P','EARLY',2),('P','LATE',1))
    try:
        for index,(sample,(source,phase,target)) in enumerate(zip(selected,cells)):
            directory=Path(artifact_root)/str(flow)/str(index);initial.restore();holder={}
            def parent(*a,**kw):
                o=MathSamplingOwner(*a,math_parameters=params,source_mode='P_OFF',**kw);holder['parent']=o;return o
            common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                inference_module=inference_module,expected_shape=config['expected_shape'],audit=True)
            with clean.patched(clean,'CurrentBirthSamplingOwner',parent):
                old=clean.execute(inference,sample,'KEEP_A_P',output=directory/'baseline',**common)
            point=select(sample.name,holder['parent'].history,source,phase,target)
            initial.restore();holder={}
            def save_branch(step,label,tensors):
                d=directory/'branches'/label;d.mkdir(parents=True)
                raw=d/'vectors.pt';torch.save(tensors,raw)
                with clean.patched(inference_module,'save_img_or_video',ordinary_writer):
                    video=decoder(inference.pipe,tensors['final_latent'].to(model.tensor_kwargs['device']))
                    path=writer(inference,video,d/sample.name)
                assert path is not None and Path(path).exists()
                return {'path':str(raw),'tensor_sha256':tree_digest(tensors),'video_path':str(path),'original_tails':tails}
            with pi0_readout_suffix_install(clean,scheduler,point,config,save_branch,params,holder,runtime=runtime,reverse_order=bool(index%2)):
                new=clean.execute(inference,sample,'KEEP_A_P',output=directory/'parent',**common)
            owner=holder['owner'];assert len(owner.event_records)==1
            assert old['status']==new['status']=='COMPLETE' and new['solver_steps']==new['guided_pairs']==36
            assert old['actions']==new['actions'] and torch.equal(old['final_latent'],new['final_latent'])
            assert all(torch.equal(x,y) for x,y in zip(old['guided'],new['guided']))
            assert Path(old['video_path']).read_bytes()==Path(new['video_path']).read_bytes()
            n=point['chosen']['step'];event=owner.event_records[0];by={b['label']:b for b in event['branches']}
            assert len(by)==2 and len(event['serial_restores'])==4 and event['actual_teacher_calls']==0
            assert owner.actual_pair_computations==36+2*(37-n)
            for label,b in by.items():
                raw=tensor_loader(Path(b['artifact']['path']),weights_only=True,map_location='cpu')
                assert tree_digest(raw)==b['artifact']['tensor_sha256']
                assert len(raw['guided'])==len(b['actions'])==len(b['source_policy_tail'])==37-n
                assert b['readout_actions'][0]==(point['default_readout'] if label=='DEFAULT_PI0' else point['alternative_readout'])
                assert b['source_policy_tail'][0]['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:')
                assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in b['source_policy_tail'][1:])
                assert b['actions'][0]=='CC' and b['source_policy_tail'][0]['true_D_before']==b['source_policy_tail'][0]['true_D_after']
                if label=='DEFAULT_PI0':
                    assert all(torch.equal(x,y) for x,y in zip(raw['guided'],old['guided'][n-1:]))
                    assert torch.equal(raw['final_latent'],old['final_latent']) and b['actions']==old['actions'][n-1:]
                    assert Path(b['artifact']['video_path']).read_bytes()==Path(old['video_path']).read_bytes()
            results.append({'scene':sample.name,'point':point,'event':event,'ordinary_parent_and_default_suffix_full_equal':True,
                'parent36_actions_guided_final_and_video_equal':True,'complete_CPU_paths':2,'endpoint_suffixes':2,
                'actual_diagnostic_pairs':owner.actual_pair_computations,'default_endpoint_decoder_writer_equal':True})
        initial.restore();assert initial.fingerprint()==origin and net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        assert len(results)==4
        return [{'flow':flow,'status':'PASS','checks':results,'complete_CPU_paths':8,'endpoint_suffixes':8,
            'four_cells':True,'ordinary_initial_state_restored':True}]
    finally:initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    ns={**vars(original),'_body':body}
    replacement='    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader)\n'
    exec(compile(source[:start]+replacement+source[end:],__file__+'#declared-Toy-setup','exec'),ns)
    r=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {x['flow'] for x in r['checks']}=={False,True}
    r.update(status='PI0_SUFFIX8_TWO_FLOW_FULL16_PARENTS16_ENDPOINT_SUFFIXES_CPU_PASS_NOT_GPU',
        actual_CPU_paths=16,endpoint_suffixes=16,events=8,
        actual_GPU_or_real_video_claim=False)
    return r
