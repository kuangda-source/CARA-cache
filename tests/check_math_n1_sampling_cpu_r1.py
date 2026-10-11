"""Actual native-block/RF/UniPC CPU integration, declared Toy boundaries."""
import copy
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.math_n1_natural_diag_r1 import natural_diagnostic_install
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.mid_coverage import tree_digest


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    p=Path(__file__).with_name(name+'.py');s=spec_from_file_location(name,p)
    m=module_from_spec(s);s.loader.exec_module(m);return m


def select_toy_states(scene,history):
    reads=[]
    for h in history:
        if h['action']!='CC' or len(h['true_D_before'][0])!=2:continue
        w=h['working_sources'][0]
        reads.append({'scene':scene,'step':h['step'],'source':w['kind'],
            'working_created_step':w['created_step'],'true_D_reference_step':h['true_D_before'][0][-1],
            'true_D_history':h['true_D_before'],
            'D_reference_age_gap':w['created_step']-h['true_D_before'][0][-1]})
    ps=[h for h in reads if h['source']=='P'];ds=[h for h in reads if h['source']=='D']
    assert len(ps)>=2 and ds,'Synthetic natural policy must expose both sources'
    early=[p for p in ps if p['step']<25];late=[p for p in ps if p['step']>=25]
    assert early and late,'Synthetic natural policy must expose early and late P reads: '+str([p['step'] for p in ps])
    # Toy coverage is explicitly by phase. The real GPU point index remains
    # the independently frozen first/max-reference-gap N0 selection.
    first=early[0];longest=late[0]
    return [first,longest,ds[0]]


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    config={**config,'paired_prefix_reserve_bytes':config.get('paired_prefix_reserve_bytes',0)}
    cal=Calibration('SYNTHETIC_N1_FULL36',{(a,s):1. for a in range(1,36) for s in range(a+1,37)},
                    {s:1. for s in range(1,37)})
    spec={'threshold':.07,'costs':Costs('SYNTHETIC_N1',1.,4.,1.),
          'partial_prior':CreationPhasePrior('SYNTHETIC_N1_FLOOR',.005,.3,
                 early_creation_floor=.005,late_creation_floor=.02),
          'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
    specs={'A_CPD_BETA1_ONE_PHASE':spec}
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));fp=initial.fingerprint()
    results=[];net0=net.forward;pipe0=inference.pipe.worldcache_enabled
    try:
        for index,sample in enumerate(selected[:2]):
            sample.name=clean.SCENES[index]
            holder={};original_owner=clean.CurrentBirthSamplingOwner
            def bound(*args,**kw):
                o=original_owner(*args,**kw);holder['original']=o;return o
            initial.restore()
            with clean.patched(clean,'CurrentBirthSamplingOwner',bound):
                old=clean.execute(inference,sample,'KEEP_A_P',runtime=runtime,wc=wc,rf=rf,
                   settings=settings,calibration=cal,specs=specs,inference_module=inference_module,
                   output=Path(artifact_root)/str(flow)/str(index)/'baseline',
                   expected_shape=config['expected_shape'])
            history=copy.deepcopy(holder['original'].history)
            states=select_toy_states(sample.name,history)
            initial.restore();holder={};artifacts=[]
            def writer(step,payload):
                p=Path(artifact_root)/str(flow)/str(index)/('point_'+str(step)+'.pt')
                torch.save(payload,p);artifacts.append(p)
                return {'path':str(p),'tensor_sha256':tree_digest(payload)}
            with natural_diagnostic_install(clean,scheduler,states,config,writer,holder):
                new=clean.execute(inference,sample,'KEEP_A_P',runtime=runtime,wc=wc,rf=rf,
                   settings=settings,calibration=cal,specs=specs,inference_module=inference_module,
                   output=Path(artifact_root)/str(flow)/str(index)/'diagnostic',
                   expected_shape=config['expected_shape'],audit=True)
            owner=holder['owner'];assert len(owner.records)==len(artifacts)==3
            assert old['status']==new['status']=='COMPLETE' and new['solver_steps']==36
            assert old['actions']==new['actions'] and torch.equal(old['final_latent'],new['final_latent'])
            assert Path(old['video_path']).read_bytes()==Path(new['video_path']).read_bytes()
            assert all(len(r['serial_restores'])==3 and r['teacher_head_calls']==2
                       and r['deployed_variant']=='D_REFERENCE_UNIT' for r in owner.records)
            results.append({'flow':flow,'scene':sample.name,'complete_CPU_paths':2,
                'natural_P_states':2,'true_D_controls':1,'full36_endpoint_and_video_equal':True,
                'natural_actions_equal':True,'teacher_and_all_candidate_restores':True,
                'records':owner.records})
        initial.restore();assert initial.fingerprint()==fp
        assert net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        return [{'flow':flow,'status':'PASS','checks':results,'complete_CPU_paths':4,
                 'same_state_points':6,'ordinary_initial_state_restored':True}]
    finally:initial.restore();net.forward=net0;inference.pipe.worldcache_enabled=pipe0


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise));start=source.index('    results=[]\n    try:')
    end=source.index('\n    finally:\n',start)+1
    replacement='    try:\n        return _n1_body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'
    ns={**vars(original),'_n1_body':body}
    exec(compile(source[:start]+replacement+source[end:],__file__+'#declared-Toy-setup', 'exec'),ns)
    result=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](
          runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in result['checks']}=={False,True}
    result.update(status='MATH_N1_TWO_FLOW_FULL8_CPU_PATHS12_STATES_PASS_NOT_GPU',
        actual_CPU_paths=8,primary_P_points=8,D_source_controls=4,
        actual_GPU_or_real_video_claim=False)
    return result
