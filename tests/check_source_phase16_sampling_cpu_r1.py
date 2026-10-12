"""Full four-source/phase requests x two flows, including pre-parent-P."""
import copy,inspect
from pathlib import Path
from textwrap import dedent
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.math_n2_sampling_owner_r1 import MathSamplingOwner
from wcomr.source_phase16_calibration_r1 import calibration16_install
from wcomr.mid_coverage import tree_digest

def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    p=Path(__file__).with_name(name+'.py');s=spec_from_file_location(name,p)
    m=module_from_spec(s);s.loader.exec_module(m);return m

def select(scene,history):
    targets={('D','EARLY'):3,('D','LATE'):2,('P','EARLY'):2,('P','LATE'):1};out=[]
    for (source,phase),target in targets.items():
        rows=[]
        for h in history:
            d=h['source_policy']['decision'];state=d['state_before'];n=d['step'];born=state[2]
            if (state[1]!=source or ('EARLY' if n<25 else 'LATE')!=phase or h['protected']
                    or not d['both_sources_ready'] or not d['partial_ready'] or state[5]>=2
                    or d['local_proxy'] is None or born is None):continue
            age=n-born
            if 1<=age<=6:rows.append({'step':n,'age':age,'source_birth':born,'true_D_anchor':state[0],
                'actual_pi0_action':d['action'],'partial_ready':d['partial_ready']})
        assert rows,'Declared Toy regime lacks a complete source/phase cell'
        out.append({'scene':scene,'source':source,'phase':phase,'target_age':target,
            'chosen':min(rows,key=lambda r:(abs(r['age']-target),r['step']))})
    assert len({s['chosen']['step'] for s in out})==4
    return out

def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    cal=Calibration('SYNTHETIC_CAL16_AGE6',{(a,n):.99 for a in range(1,36)
        for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec={'threshold':2.,'costs':Costs('SYNTHETIC_CAL16',3.,4.,1.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_CAL16',.005,.3,
            early_creation_floor=.005,late_creation_floor=10.),
        'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
    specs={'A_CPD_BETA1_ONE_PHASE':spec};params={'gamma':.5,'fingerprint':'SYNTHETIC_ONLY'}
    config={**config,'paired_prefix_reserve_bytes':config.get('paired_prefix_reserve_bytes',0)}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    net0,pipe0=net.forward,inference.pipe.worldcache_enabled;results=[];P_parent=0
    try:
        for index,sample in enumerate(selected):
            initial.restore();holder={}
            def parent(*a,**kw):
                owner=MathSamplingOwner(*a,math_parameters=params,source_mode='P_OFF',**kw)
                holder['parent']=owner;return owner
            common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                inference_module=inference_module,expected_shape=config['expected_shape'],audit=True)
            with clean.patched(clean,'CurrentBirthSamplingOwner',parent):
                old=clean.execute(inference,sample,'KEEP_A_P',output=Path(artifact_root)/str(flow)/str(index)/'baseline',**common)
            states=select(sample.name,holder['parent'].history)
            P_parent+=sum(s['chosen']['actual_pi0_action']=='P' for s in states)
            initial.restore();holder={};artifacts=[]
            def writer(step,payload):
                p=Path(artifact_root)/str(flow)/str(index)/('cal16_point_'+str(step)+'.pt')
                torch.save(payload,p);artifacts.append(p);return {'path':str(p),'tensor_sha256':tree_digest(payload)}
            with calibration16_install(clean,scheduler,states,config,writer,params,holder):
                new=clean.execute(inference,sample,'KEEP_A_P',output=Path(artifact_root)/str(flow)/str(index)/'cal16',**common)
            owner=holder['owner'];assert len(owner.records)==len(artifacts)==4
            assert old['status']==new['status']=='COMPLETE' and new['solver_steps']==new['guided_pairs']==36
            assert old['actions']==new['actions'] and torch.equal(old['final_latent'],new['final_latent'])
            assert all(torch.equal(x,y) for x,y in zip(old['guided'],new['guided']))
            assert Path(old['video_path']).read_bytes()==Path(new['video_path']).read_bytes()
            assert owner.actual_pair_computations==56
            for r in owner.records:
                assert len(r['restores'])==5 and len(r['trial_receipts'])==5 and not r['offline_teacher_or_candidates_committed_to_parent']
                labels={x['label']:x for x in r['trial_receipts']}
                assert labels['DENSE_SAME_STATE']['actual_heads']==labels['C']['actual_heads']==labels['NEW_P']['actual_heads']==2
                assert labels['D_REFERENCE_A']['actual_heads']==4
                assert labels['FUSION_A']['actual_heads']==(4 if r['point']['source']=='D' else 6)
                assert labels['NEW_P']['history']['true_D_before']==labels['NEW_P']['history']['true_D_after']
            results.append({'scene':sample.name,'states':states,'records':owner.records,
                'all36_guided_actions_final_and_video_equal':True,'all5_pre_action_trials_restored':True,
                'complete_CPU_paths':2,'actual_diagnostic_pairs':56})
        initial.restore();assert initial.fingerprint()==origin and net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        assert len(results)==4 and P_parent>=4,'All four requests must exercise a natural parent-P point'
        return [{'flow':flow,'status':'PASS','checks':results,'complete_CPU_paths':8,
            'natural_states':16,'pre_parent_P_points':P_parent,'ordinary_initial_state_restored':True}]
    finally:initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0

def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise));start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    ns={**vars(original),'_body':body}
    replacement='    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'
    exec(compile(source[:start]+replacement+source[end:],__file__+'#declared-Toy-setup','exec'),ns)
    r=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {x['flow'] for x in r['checks']}=={False,True}
    r.update(status='SOURCE_PHASE16_TWO_FLOW_FULL16_PARENTS32_STATES_CPU_PASS_NOT_GPU',
        actual_CPU_paths=16,natural_points=32,offline_primitive_pairs=160,
        pre_parent_P_points=sum(x['pre_parent_P_points'] for x in r['checks']),
        actual_GPU_or_real_video_claim=False)
    return r
