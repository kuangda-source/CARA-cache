"""Full native/RF/UniPC two-flow6-method audit/lean and state ownership proof."""
import copy,inspect
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.source_phase_absolute_h1_batch_r1 import execute
from wcomr.source_phase_fixed_mask_r1 import execute_fixed,FixedMaskH1Controller,CAL_MASK_A,CAL_MASK_C,mask_fingerprint
from wcomr.source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller,VERSION,fingerprint
from wcomr.math_n2_batch_r1 import execute as previous_execute


def load(name):
    from importlib.util import spec_from_file_location,module_from_spec
    s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root):
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    cal=Calibration('SYNTHETIC_H1_ACTUAL_AGE6',{(a,n):.99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)},{n:1. for n in range(1,37)})
    spec={'threshold':2.,'costs':Costs('SYNTHETIC_H1',1.,4.,3.5),
        'partial_prior':CreationPhasePrior('SYNTHETIC_H1',.005,.3,early_creation_floor=.005,late_creation_floor=.02),
        'working_epoch_strategy':'WORKING_P_AGE_NONZERO_REBASE'}
    specs={'SOURCE_RA':spec,'A_CPD_BETA1_ONE_PHASE':spec}
    old={'fingerprint':'SYNTHETIC_PRIOR_UNCHANGED','gamma':.5}
    tables={}
    for group in ('SOURCE_PHASE','SOURCE'):
        keys=[s+'_'+phase for s in ('D','P') for phase in ('EARLY','LATE')] if group=='SOURCE_PHASE' else ['D','P']
        cells={key:{'status':'FIT','C_scale':1. if key.startswith('P') else 100.,'A_ratios':{'FUSION_A':.02},'actual_NEW_P_birth_mean':.0001} for key in keys}
        p={'version':VERSION,'gamma':.5,'table_model':{'grouping':group,'target':'absolute_guided_MSE',
            'current_teacher_energy_is_online_feature':False,'cells':cells},
            'cost_seconds':{'C':1.,'A':1.3,'P':3.5,'D':4.},'source_A_cost_seconds':{'D':1.1,'P':1.3},
            'lambda_seconds_per_weighted_absolute_MSE':100.}
        p['fingerprint']=fingerprint(p);tables[group]=p
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    old_forward,old_enabled=net.forward,inference.pipe.worldcache_enabled
    checks=[];actual_masks=[]
    try:
        for index,sample in enumerate(selected):
            common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                inference_module=inference_module,expected_shape=config['expected_shape'])
            initial.restore()
            dynamic,_=execute(inference,sample,'TABLE_PHASE_H1',table_parameters=tables,previous_parameters=old,
                output=Path(artifact_root)/str(flow)/str(index)/'DYNAMIC_AUDIT',audit=True,**common)
            initial.restore()
            dynamic_lean,_=execute(inference,sample,'TABLE_PHASE_H1',table_parameters=tables,previous_parameters=old,
                output=Path(artifact_root)/str(flow)/str(index)/'DYNAMIC_LEAN',audit=False,**common)
            assert torch.equal(dynamic['final_latent'],dynamic_lean['final_latent'])
            assert dynamic['actions']==dynamic_lean['actions'] and dynamic['A_history']==dynamic_lean['A_history']
            assert Path(dynamic['video_path']).read_bytes()==Path(dynamic_lean['video_path']).read_bytes()
            assert dynamic_lean['in_timing_hashes']==dynamic_lean['in_timing_guided_copies']==0
            plan=tuple(h['A_readout']['readout_action'] for h in dynamic['source_history'])
            assert len(plan)==36 and plan[:7]==('D',)*7 and plan[-1]=='D'
            actual_masks.append(plan)
            entries=(('EXACT_DYNAMIC_MASK_A',plan),
                     ('EXACT_DYNAMIC_MASK_PLAIN',tuple('C' if a=='A' else a for a in plan)),
                     ('FROZEN_CAL_MASK_A',CAL_MASK_A),('FROZEN_CAL_MASK_PLAIN',CAL_MASK_C))
            for label,mask in entries:
                outcomes=[]
                for audit in (True,False):
                    initial.restore();assert initial.fingerprint()==origin
                    value=execute_fixed(inference,sample,replay_plan=mask,
                        table_parameters=tables['SOURCE_PHASE'],previous_parameters=old,
                        output=Path(artifact_root)/str(flow)/str(index)/(label+('_AUDIT' if audit else '_LEAN')),
                        audit=audit,**common)
                    assert value['status']=='COMPLETE' and value['solver_steps']==value['guided_pairs']==36
                    assert value['semantic_plan']==list(mask)
                    assert value['mask_sha256']==mask_fingerprint(mask)
                    assert value['actions']==[('C' if a=='A' else a)*2 for a in mask]
                    assert not value['input_adaptive_action_selection'] and value['online_teacher_calls']==0
                    for h in value['source_history']:
                        q=h['source_policy']['event_math'];a=h['A_readout']
                        assert not q['input_adaptive_action_selection'] and not q['H1_table_and_optimizer_evaluated']
                        assert a['teacher_calls']==a['extra_deep_blocks']==0
                        if h['action']!='DD':assert h['true_D_before']==h['true_D_after']
                        if h['action']=='PP':assert h['source_policy']['creation_floor_proxy_after']>0
                        if a['readout_action']=='C':assert a['extra_heads']==0 and a['shared_alpha']==0
                    if not audit:assert value['in_timing_hashes']==value['in_timing_guided_copies']==value['research_checkpoints']==0
                    outcomes.append(value)
                a,b=outcomes
                assert torch.equal(a['final_latent'],b['final_latent']) and a['actions']==b['actions'] and a['A_history']==b['A_history']
                assert Path(a['video_path']).read_bytes()==Path(b['video_path']).read_bytes()
                if label=='EXACT_DYNAMIC_MASK_A':
                    assert torch.equal(a['final_latent'],dynamic['final_latent'])
                    assert all(torch.equal(x,y) for x,y in zip(a['guided'],dynamic['guided']))
                    assert a['actions']==dynamic['actions'] and a['A_history']==dynamic['A_history']
                    assert Path(a['video_path']).read_bytes()==Path(dynamic['video_path']).read_bytes()
                c=FixedMaskH1Controller(cal,2.,spec['costs'],spec['partial_prior'],strategy=spec['working_epoch_strategy'],
                    table_parameters=tables['SOURCE_PHASE'],math_parameters=old,horizon=1,
                    sigma_at=lambda n:float(scheduler.sigmas[n-1]),replay_plan=mask)
                for h in a['source_history']:
                    d=h['joint_decision'];choice=c._choice(d['step'],tuple(tuple(p) for p in d['packets']),
                        d['both_sources_ready'],d['partial_ready'],protected=d['reason']=='actual_protected_dense')
                    assert choice.reason==d['reason'] and choice.action*2==h['action']
                    c.commit(choice,actual_action=choice.action,pair_completed=True)
                snap=c.state_dict();c.accumulated=999.;c.restore(snap);assert c.state_dict()==snap
                bad=copy.deepcopy(snap);bad['binding']=bad['binding'][:-1]+('WRONG_MASK',)
                try:c.restore(bad)
                except ValueError:pass
                else:raise AssertionError('Foreign fixed mask snapshot accepted')
                checks.append(dict(scene=sample.name,label=label,mask_sha256=mask_fingerprint(mask),
                    all36_audit_lean_actions_final_video_equal=True,
                    exact_dynamic_numeric_parity=label=='EXACT_DYNAMIC_MASK_A',
                    replay_restore_and_foreign_mask_refusal=True,physical_D_counts=mask.count('D'),
                    plain_C_counts=mask.count('C'),semantic_A_counts=mask.count('A'),P_counts=mask.count('P')))
        initial.restore();assert initial.fingerprint()==origin and net.forward==old_forward and inference.pipe.worldcache_enabled==old_enabled
        assert len(checks)==16
        assert CAL_MASK_A.count('D')==26 and CAL_MASK_A.count('A')==5 and CAL_MASK_A.count('C')==5
        assert CAL_MASK_C.count('D')==26 and CAL_MASK_C.count('C')==10
        return [dict(flow=flow,status='PASS',checks=checks,complete_CPU_paths=40,
            all36_clean_outputs_actions_video_equal=True,ordinary_initial_state_restored=True,
            exact_dynamic_masks=[list(p) for p in actual_masks],
            frozen_CAL_mask_counts={'D':26,'A':5,'C':5,'P':0})]
    finally:initial.restore();net.forward=old_forward;inference.pipe.worldcache_enabled=old_enabled


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    ns={**vars(original),'_body':body};exec(compile(changed,__file__+'#same-declared-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='SOURCE_PHASE_FIXED_MASK_TWO_FLOW_FULL80_CPU_PASS_NOT_GPU',actual_CPU_paths=80,
        complete_method_paths=40,clean_control_paths=40,actual_GPU_or_real_video_claim=False)
    return value
