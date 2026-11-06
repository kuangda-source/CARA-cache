"""Full native/RF/UniPC two-flow6-method audit/lean and state ownership proof."""
import copy,inspect
from pathlib import Path
from textwrap import dedent
import torch
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.h1_cost_curve_batch_r1 import execute,METHODS,matrix,lambda_variants
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
            'lambda_seconds_per_weighted_absolute_MSE':100.,'curve_lambdas':[25.,100.,400.]}
        p['fingerprint']=fingerprint(p);tables[group]=p
    def native(self,*a,**kw):
        value=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=value
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    old_forward,old_enabled=net.forward,inference.pipe.worldcache_enabled;checks=[];readouts=set();sources=set()
    try:
        for index,sample in enumerate(selected):
            for method in METHODS:
                common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                    inference_module=inference_module,expected_shape=config['expected_shape'],CPU_native=native)
                initial.restore();assert initial.fingerprint()==origin
                audit=execute(inference,sample,method,table_parameters=tables,previous_parameters=old,
                    output=Path(artifact_root)/str(flow)/str(index)/(method+'_AUDIT'),audit=True,**common)
                initial.restore()
                lean=execute(inference,sample,method,table_parameters=tables,previous_parameters=old,
                    output=Path(artifact_root)/str(flow)/str(index)/(method+'_LEAN'),audit=False,**common)
                assert audit['status']==lean['status']=='COMPLETE' and len(audit['guided'])==36
                assert audit['actions']==lean['actions'] and audit['A_history']==lean['A_history']
                assert torch.equal(audit['final_latent'],lean['final_latent'])
                assert Path(audit['video_path']).read_bytes()==Path(lean['video_path']).read_bytes()
                assert lean['in_timing_hashes']==lean['in_timing_guided_copies']==lean['research_checkpoints']==0
                assert all(h['teacher_calls']==h['extra_deep_blocks']==0 for h in (audit['A_history'] or []))
                if method.startswith('H1_'):
                    p=lambda_variants(tables['SOURCE_PHASE'])[method]
                    assert audit['curve_parameters_fingerprint']==p['fingerprint'] and audit['curve_lambda']==p['lambda_seconds_per_weighted_absolute_MSE']
                if method.startswith('FIXED_'):
                    assert audit['semantic_plan']==lean['semantic_plan'] and not audit['input_adaptive_action_selection']
                    assert audit['actions'].count('DD')==26
                if method=='NATIVE':assert audit['actions'] is None
                if method in ('H1_LOW','H1_MID','H1_HIGH','FIXED_A','FIXED_PLAIN'):
                    for row in audit['source_history']:
                        ah=row['A_readout'];assert ah['teacher_calls']==ah['extra_deep_blocks']==0
                        if row['action']!='DD':assert row['true_D_before']==row['true_D_after']
                        if row['action']=='PP':assert row['source_policy']['creation_floor_proxy_after']>0
                checks.append({'scene':sample.name,'method':method,'complete36':True,'clean_parity':True,'actions':audit['actions']})
        initial.restore();assert initial.fingerprint()==origin and net.forward==old_forward and inference.pipe.worldcache_enabled==old_enabled
        assert len(checks)==40
        rows=matrix([s.name for s in selected]);assert len(rows)==60 and sum(r['section']=='TIMED' for r in rows)==40
        return [{'flow':flow,'status':'PASS','checks':checks,'complete_CPU_paths':80,'all36_clean_outputs_actions_video_equal':True,
            'actual_rho_age_max':6,'readouts_exercised':sorted(readouts),'sources_exercised':sorted(sources),'ordinary_initial_state_restored':True}]
    finally:initial.restore();net.forward=old_forward;inference.pipe.worldcache_enabled=old_enabled


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1');source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:');end=source.index('\n    finally:\n',start)+1
    changed=source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    ns={**vars(original),'_body':body};exec(compile(changed,__file__+'#declared-Toy-setup','exec'),ns)
    value=load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kw))
    assert {c['flow'] for c in value['checks']}=={False,True}
    value.update(status='H1_COST_CURVE_TWO_FLOW_ALL160_CPU_PASS_NOT_GPU',actual_CPU_paths=160,
        complete_method_paths=80,clean_control_paths=80,actual_GPU_or_real_video_claim=False)
    return value
